#!/usr/bin/env python3
"""EIXO LIQUIDEZ/MANIPULAÇÃO — E0 (Cris aprovou desenho B + VOZ ON imediata, 2026-08-04).

Causa-raiz que corrige (2 falhas no MESMO dia, direções opostas): o reader lia momentum + rótulo de perna
(superfície) e não lia MECÂNICA DE LIQUIDEZ (estrutura). 08:03 comprou o topo (iniciativa a ser ABSORVIDA
para dentro da supply declarada = Judas); 11:30 recusou o reclaim genuíno pós-sweep chamando-lhe faca
(ancorado no rótulo de perna ATRASADO). Este eixo responde em código determinístico:
  1. Que liquidez foi TOMADA (PDH/PDL/PWH/PWL, extremos de sessão, pivôs) e quem ficou PRESO?
  2. O movimento é INICIATIVA-PARA-ÍMAN contrário não-preenchido (manipulation-prone) ou
     DESLOCAMENTO-PÓS-SWEEP para longe da liquidez varrida (genuíno)?
  3. Estado da sequência por lado: SWEPT → RECLAIMED → HOLDING → CONTINUATION / FAILED
     (gramática AMD em 15M; 1ª quebra=manipulação, 2ª=confirmação — R8 agora como VOZ, não só gatilho).

CONSUMO (nunca reconstruir): bars_15m do bar-store · swings/choch do dossiê (context_structure) ·
magnets (F-A2) · zonas HTF · trader_map · amd_setup · janela de confluência. Novo de verdade: só o scan
de sweeps 15M + a FSM. Stateless: recomputa dos últimos LOOKBACK bares (replayável, testável).
FIT declarados (calibrar em replay, nunca só no dia visível): RECLAIM_N=3 · HOLD_BARS=2 · REACH_ATR=1.5 ·
PEN_MIN_ATR=0.05 · janela eventos 24h · sessões UTC Ásia 23-07 / Londres 07-12 / NY 12-21. py3.9."""
import json, time, datetime as dt
from pathlib import Path

BASE = Path(__file__).resolve().parent

# FIT (ver docstring)
LOOKBACK = 480
RECLAIM_N = 3
HOLD_BARS = 2
REACH_ATR = 1.5
PEN_MIN_ATR = 0.05
EVENT_WINDOW_S = 24 * 3600
PIVOT_K = 3
SESSIONS = (("asia", 23, 7), ("london", 7, 12), ("ny", 12, 21))   # UTC, FIT


def _atr14(bars):
    if len(bars) < 15: return None
    trs = [max(b["h"] - b["l"], abs(b["h"] - p["c"]), abs(b["l"] - p["c"]))
           for p, b in zip(bars, bars[1:])]
    return sum(trs[-14:]) / 14


def _utc(t): return dt.datetime.fromtimestamp(int(t), dt.timezone.utc)


def _levels(bars):
    """Níveis vigiados: PDH/PDL/PWH/PWL, extremos de sessões COMPLETAS de hoje, pivôs (k=PIVOT_K).
    Cada nível = (kind, price, born_i) — só barras DEPOIS de born_i podem varrê-lo."""
    if not bars: return []
    out = []
    days = {}
    weeks = {}
    for i, b in enumerate(bars):
        d = _utc(b["t"])
        days.setdefault(d.date(), []).append((i, b))
        weeks.setdefault(d.isocalendar()[:2], []).append((i, b))
    dkeys = sorted(days)
    if len(dkeys) >= 2:
        prev = days[dkeys[-2]]
        out.append(("PDH", max(b["h"] for _, b in prev), prev[-1][0]))
        out.append(("PDL", min(b["l"] for _, b in prev), prev[-1][0]))
    wkeys = sorted(weeks)
    if len(wkeys) >= 2:
        pw = weeks[wkeys[-2]]
        out.append(("PWH", max(b["h"] for _, b in pw), pw[-1][0]))
        out.append(("PWL", min(b["l"] for _, b in pw), pw[-1][0]))
    # sessões completas de HOJE (uma sessão só vira nível depois de fechar)
    today = dkeys[-1]
    now_h = _utc(bars[-1]["t"]).hour
    for name, h0, h1 in SESSIONS:
        rows = [(i, b) for i, b in days[today] if (h0 <= _utc(b["t"]).hour < h1) if h0 < h1] or \
               [(i, b) for i, b in days.get(today, []) if h0 > h1 and (_utc(b["t"]).hour >= h0 or _utc(b["t"]).hour < h1)]
        if rows and (now_h >= h1 if h0 < h1 else (h1 <= now_h < h0)):
            out.append((f"{name}_hi", max(b["h"] for _, b in rows), rows[-1][0]))
            out.append((f"{name}_lo", min(b["l"] for _, b in rows), rows[-1][0]))
    # pivôs k=PIVOT_K (liquidez local: swing highs/lows confirmados)
    k = PIVOT_K
    for i in range(k, len(bars) - k):
        if bars[i]["h"] == max(b["h"] for b in bars[i - k:i + k + 1]):
            out.append(("pivot_hi", bars[i]["h"], i + k))
        if bars[i]["l"] == min(b["l"] for b in bars[i - k:i + k + 1]):
            out.append(("pivot_lo", bars[i]["l"], i + k))
    # dedup: equal highs/lows (mesmo kind+preço) = UM nível (o mais antigo); evita eventos duplicados
    seen = {}
    for kind, lvl, born in out:
        key = (kind, round(lvl, 2))
        if key not in seen or born < seen[key][2]:
            seen[key] = (kind, lvl, born)
    return list(seen.values())


def _sweeps(bars, levels, atr):
    """Sweep = pavio além do nível (pen>=PEN_MIN_ATR·ATR) + close de volta em <=RECLAIM_N barras.
    Devolve eventos {kind, level, side, sweep_i, sweep_extreme, reclaim_i, trapped}."""
    if not atr: return []
    ev = []
    t_now = bars[-1]["t"]
    for kind, lvl, born in levels:
        is_high = kind.endswith(("H", "hi")) or kind == "pivot_hi"
        i = born + 1
        while i < len(bars):
            b = bars[i]
            pen = (b["h"] - lvl) if is_high else (lvl - b["l"])
            if pen >= PEN_MIN_ATR * atr and (is_high and b["h"] > lvl or not is_high and b["l"] < lvl):
                # candidato: procurar reclaim (close de volta) em <=RECLAIM_N barras a partir desta
                extreme = b["h"] if is_high else b["l"]
                rec = None
                j = i
                while j < min(i + RECLAIM_N, len(bars)):
                    bj = bars[j]
                    extreme = max(extreme, bj["h"]) if is_high else min(extreme, bj["l"])
                    back = (bj["c"] < lvl) if is_high else (bj["c"] > lvl)
                    if back:
                        rec = j; break
                    j += 1
                if rec is not None and t_now - bars[i]["t"] <= EVENT_WINDOW_S:
                    ev.append({"kind": kind, "level": round(lvl, 2), "side": "high" if is_high else "low",
                               "sweep_i": i, "sweep_extreme": round(extreme, 2), "reclaim_i": rec,
                               "trapped": "buyers" if is_high else "shorts"})
                i = (rec + 1) if rec is not None else j   # sem reclaim: barra j reavaliada como novo sweep
            else:
                i += 1
    ev.sort(key=lambda e: e["sweep_i"])
    return ev


def _fsm(bars, ev):
    """Estado da sequência a partir do evento: RECLAIMED → HOLDING (>=HOLD_BARS closes sem re-perder)
    → CONTINUATION (deslocou >=1 ATR do nível) · FAILED (close além do extremo varrido)."""
    lvl, is_high = ev["level"], ev["side"] == "high"
    ext = ev["sweep_extreme"]
    state = "RECLAIMED"
    hold = 0
    for b in bars[ev["reclaim_i"] + 1:]:
        beyond_ext = (b["c"] > ext) if is_high else (b["c"] < ext)
        if beyond_ext:
            return "FAILED"
        ok = (b["c"] < lvl) if is_high else (b["c"] > lvl)
        hold = hold + 1 if ok else 0
        if hold >= HOLD_BARS and state == "RECLAIMED":
            state = "HOLDING"
    if state == "HOLDING":
        last_c = bars[-1]["c"]
        disp = (lvl - last_c) if is_high else (last_c - lvl)
        atr = _atr14(bars)
        if atr and disp >= 1.0 * atr:
            state = "CONTINUATION"
    return state


def _opposing_magnets(direction, price, atr, magnets, zones_stack, tmap_zones):
    """Ímanes contrários NÃO-preenchidos ao alcance (<=REACH_ATR) na direção do movimento."""
    out = []
    side = "above" if direction == "up" else "below"
    for m in ((magnets or {}).get(side) or []):
        if m.get("dist_atr") is not None and m["dist_atr"] <= REACH_ATR:
            out.append(f"{m['type']}@{m['dist_atr']}ATR")
    for z in (zones_stack or []):
        zl, zh = z.get("low"), z.get("high")
        if zl is None: continue
        d = (zl - price) / atr if direction == "up" else (price - zh) / atr
        if -0.2 <= d <= REACH_ATR:
            out.append(f"zona {zl:.0f}-{zh:.0f} ({z.get('src','')[:12]})")
    want = "SHORT" if direction == "up" else "LONG"
    for z in (tmap_zones or []):
        if z.get("tese") != want: continue
        d = (z["low"] - price) / atr if direction == "up" else (price - z["high"]) / atr
        if -0.2 <= d <= REACH_ATR:
            out.append(f"zona-do-trader {z['low']:.0f}-{z['high']:.0f} (tese {z['tese']})")
    return out[:4]


def compute(bars, magnets=None, zones_by_tf=None, tmap_zones=None, window=None, amd=None):
    """Núcleo puro (testável/replayável). bars = 15M fechadas (dicts t/o/h/l/c)."""
    bars = bars[-LOOKBACK:]
    if len(bars) < 40: return None
    atr = _atr14(bars)
    if not atr: return None
    price = bars[-1]["c"]
    levels = _levels(bars)
    events = _sweeps(bars, levels, atr)
    # estado por lado = evento mais recente de cada lado
    # SIGNIFICÂNCIA (princípio, não fit-ao-dia): reversão genuína segue-se a um RAID (liquidez a sério
    # tomada), não a uma roçadela de pivô. Sequência só CONTA para a classificação se: nível de 1ª ordem
    # (PDH/PDL/PWH/PWL/sessão) OU profundidade da excursão do raid >= RAID_MIN_ATR (do nível mais alto
    # varrido ao extremo, na mesma janela). Continua visível no render como info mesmo se não-significante.
    # FIT: RAID_MIN_ATR=1.0 (unidade natural); validado nas 27 facas resolvidas 20/07-03/08 (multi-dia).
    RAID_MIN_ATR = 1.0
    first_order = ("PDH", "PDL", "PWH", "PWL")
    sides = {}
    for e in events:
        raid_ev = [o for o in events
                   if o["side"] == e["side"] and abs(o["sweep_i"] - e["sweep_i"]) <= 12]
        if e["side"] == "low":
            raid_depth = max(o["level"] for o in raid_ev) - min(o["sweep_extreme"] for o in raid_ev)
        else:
            raid_depth = max(o["sweep_extreme"] for o in raid_ev) - min(o["level"] for o in raid_ev)
        sig = (e["kind"] in first_order or e["kind"].startswith(("asia_", "london_", "ny_"))
               or raid_depth >= RAID_MIN_ATR * atr)
        sides[e["side"]] = {**e, "state": _fsm(bars, e), "significant": sig,
                            "raid_n": len(raid_ev), "raid_depth": round(raid_depth, 2)}
    # direção do movimento: últimas 3 barras + janela de agressão
    net = sum(1 if b["c"] > b["o"] else -1 for b in bars[-3:])
    win_side = ((window or {}).get("net_side"))
    direction = "up" if (net > 0 or (net == 0 and win_side == "buy")) else "down"
    # zonas HTF contrárias (stack 60/240)
    stack = []
    for tf in ("60", "240"):
        z = (zones_by_tf or {}).get(tf) or {}
        zz = z.get("above") if direction == "up" else z.get("below")
        if isinstance(zz, dict): stack.append(zz)
        for s in (z.get("stack") or []):
            if isinstance(s, dict): stack.append(s)
    opposing = _opposing_magnets(direction, price, atr, magnets, stack, tmap_zones)
    # classificação
    fav = sides.get("low") if direction == "up" else sides.get("high")
    # guard de chase (princípio da entrada-ancorada): CONTINUATION já >SPENT_ATR além do nível = janela passada
    SPENT_ATR = 1.5
    spent = fav and fav["state"] == "CONTINUATION" and abs(price - fav["level"]) > SPENT_ATR * atr
    fav_ok = (fav and fav.get("significant") and not spent
              and fav["state"] in ("RECLAIMED", "HOLDING", "CONTINUATION"))
    if fav_ok:
        if opposing and fav["state"] == "RECLAIMED":
            move_class = "INICIATIVA_PARA_IMAN"      # reclaim SEM hold + íman contrário ao alcance: o íman manda
        elif opposing:
            move_class = "MISTO"                     # sequência provada (hold+) MAS íman ao alcance: exigir rejeição
        else:
            move_class = "DESLOCAMENTO_POS_SWEEP"
    elif opposing:
        move_class = "INICIATIVA_PARA_IMAN"
    else:
        move_class = "NEUTRO"
    recent = [e for e in events if bars[-1]["t"] - bars[e["sweep_i"]]["t"] <= EVENT_WINDOW_S][-4:]
    return {"computed_at": int(bars[-1]["t"]), "atr15": round(atr, 2), "direction": direction,
            "move_class": move_class,
            "taken": [{"kind": e["kind"], "level": e["level"], "side": e["side"], "trapped": e["trapped"],
                       "t": int(bars[e["sweep_i"]]["t"])} for e in recent],
            "sequence": {s: {"kind": v["kind"], "level": v["level"], "state": v["state"],
                             "trapped": v["trapped"], "sweep_extreme": v["sweep_extreme"]}
                         for s, v in sides.items()},
            "opposing_magnets": opposing,
            "amd_active": bool((amd or {}).get("active"))}


def read_liquidity(magnets=None, mtf=None, amd=None, window=None):
    """Entrada E0: lê bars do store + consome eixos já computados. None em falha (fail-open)."""
    try:
        import store_reader as SR
        bars = [b for b in SR.bars("15") if all(k in b for k in ("t", "o", "h", "l", "c"))]
        tmz = None
        try:
            import trader_map
            tm = trader_map.load_map()
            tmz = tm["zones"] if tm else None
        except Exception:
            pass
        zones = {tf: (d.get("zones") if isinstance(d, dict) else None) or
                     ((d.get("structure") or {}).get("zones") if isinstance(d, dict) else None)
                 for tf, d in (mtf or {}).items()} if mtf else None
        return compute(bars, magnets=magnets, zones_by_tf=zones, tmap_zones=tmz, window=window, amd=amd)
    except Exception:
        return None


# ---------------------------------------------------------------- voz E2
LIQUIDITY_RULE = (
    "VOZ DE LIQUIDEZ/MANIPULAÇÃO (2026-08-04, duas falhas no mesmo dia em direções opostas — mesma "
    "causa-raiz: momentum e rótulo de perna sem mecânica de liquidez): o briefing traz a secção "
    "LIQUIDEZ/MANIPULAÇÃO com (1) que liquidez foi TOMADA e que lado ficou PRESO; (2) o estado da sequência "
    "sweep→reclaim→hold→continuação por lado (1ª quebra = manipulação provável, 2ª = confirmação); (3) a "
    "classificação do movimento: INICIATIVA PARA DENTRO DE ÍMAN CONTRÁRIO não-preenchido vs DESLOCAMENTO "
    "PÓS-SWEEP. Antes de concluir responde SEMPRE: quem está preso? para onde vai o preço buscar liquidez?\n"
    "• JUDAS/ABSORÇÃO (a falha das 08:03): iniciativa fresca A CAMINHAR PARA DENTRO de íman contrário "
    "não-preenchido (supply/demand HTF, zona declarada do trader, PDH/PDL intacto) NÃO é força — é candidata "
    "a manipulação: a agressão está a ser absorvida no íman antes do movimento contrário. Esta voz REBAIXA a "
    "convicção baseada em momentum: 'iniciativa compradora fresca' com supply por preencher a <1.5 ATR pesa "
    "CONTRA o long, não a favor. Só volta a pesar a favor DEPOIS do teste-e-rejeição no íman (GT#1: o "
    "discriminador é a rejeição NO íman, nunca a antecipação).\n"
    "• RECLAIM PÓS-SWEEP (a falha das 11:30): quando a sequência diz SWEPT→RECLAIMED(hold) e o movimento é "
    "DESLOCAMENTO para longe da liquidez varrida, esta leitura SOBREPÕE-SE ao rótulo da perna 1H — o rótulo "
    "é o dado ATRASADO nas viragens; a sequência de liquidez é o dado causal. Nesse estado 'faca/pullback "
    "contra a perna' deixa de ser a leitura por defeito: passa a 'reclaim pós-sweep válido, candidato genuíno "
    "a reversão'; a exigência de OB 4H/1D para reversão dá lugar à sequência (o sweep+reclaim É a confluência "
    "de exaustão). Rigor mantido: sem hold ≥2 barras fechadas, ou com re-perda do nível varrido, não há "
    "sequência — a regra do frame aplica-se por inteiro.\n"
    "• A voz não é veto nem aprovação automática — entra na convergência com as restantes. Mas em CONTRADIÇÃO "
    "direta entre esta voz e o rótulo da perna, esta voz manda.")

_STATE_PT = {"RECLAIMED": "reclaimed (fresco, sem hold)", "HOLDING": "reclaim + HOLD confirmado",
             "CONTINUATION": "continuação confirmada", "FAILED": "falhou (re-perdeu o nível)"}


def render_section(liq):
    if not liq: return ""
    L = ["\n# LIQUIDEZ / MANIPULAÇÃO (mecânica: quem está preso, para onde vai o preço buscar liquidez)"]
    if liq["taken"]:
        for e in liq["taken"][-3:]:
            hh = dt.datetime.fromtimestamp(e["t"], dt.timezone.utc).strftime("%H:%M")
            L.append(f"  liquidez tomada: {e['kind']} {e['level']} varrido ({hh}Z) → presos: {e['trapped']}")
    else:
        L.append("  sem sweeps nas últimas 24h (níveis vigiados intactos)")
    for side, s in (liq.get("sequence") or {}).items():
        lado = "lows" if side == "low" else "highs"
        L.append(f"  sequência {lado}: {s['kind']} {s['level']} → {_STATE_PT.get(s['state'], s['state'])} "
                 f"(extremo varrido {s['sweep_extreme']}; presos {s['trapped']})")
    mc = liq["move_class"]
    if mc == "INICIATIVA_PARA_IMAN":
        L.append(f"  movimento ({liq['direction']}): INICIATIVA PARA DENTRO DE ÍMAN CONTRÁRIO não-preenchido "
                 f"→ MANIPULAÇÃO-PROVÁVEL (agressão a ser absorvida) · ímanes: {'; '.join(liq['opposing_magnets'])}")
    elif mc == "DESLOCAMENTO_POS_SWEEP":
        L.append(f"  movimento ({liq['direction']}): DESLOCAMENTO PÓS-SWEEP, a afastar-se da liquidez varrida "
                 f"→ candidato GENUÍNO (reclaim pós-sweep válido; sobrepõe rótulo de perna atrasado)")
    elif mc == "MISTO":
        L.append(f"  movimento ({liq['direction']}): MISTO — sequência pós-sweep a favor MAS íman contrário ao "
                 f"alcance ({'; '.join(liq['opposing_magnets'])}) — exigir teste-e-rejeição no íman")
    else:
        L.append(f"  movimento ({liq['direction']}): NEUTRO (sem sequência viva nem íman contrário ao alcance)")
    if liq.get("amd_active"):
        L.append("  reforço: setup AMD H4 sweep ATIVO (grau superior da mesma gramática)")
    return "\n".join(L)


if __name__ == "__main__":
    import sys
    if "--selftest" in sys.argv:
        T0 = 1785600000
        mk = lambda i, o, h, l, c: {"t": T0 + i * 900, "o": o, "h": h, "l": l, "c": c}
        # 50 barras planas ~100 com pivô low em i=20 (l=98.0), depois sweep em i=44 e reclaim
        bars = []
        for i in range(48):
            if i == 20: bars.append(mk(i, 100, 100.5, 98.0, 100.1))
            elif i == 44: bars.append(mk(i, 100, 100.2, 95.5, 99.6))     # RAID: varre 98.0 fundo (depth 2.5 >1·ATR)
            elif i == 45: bars.append(mk(i, 99.6, 100.4, 99.2, 100.2))   # reclaim close>98 (já era) → close acima
            elif i == 46: bars.append(mk(i, 100.2, 100.8, 99.9, 100.6))  # hold 1
            elif i == 47: bars.append(mk(i, 100.6, 100.9, 100.3, 100.6)) # hold 2 → HOLDING (sem passar chase-guard)
            else: bars.append(mk(i, 100, 100.9, 99.1, 100 + (0.2 if i % 2 else -0.2)))
        liq = compute(bars)
        seq = (liq or {}).get("sequence", {}).get("low")
        ok1 = liq and seq and seq["state"] in ("HOLDING", "CONTINUATION")
        ok2 = liq and any(e["trapped"] == "shorts" for e in liq["taken"])
        ok3 = liq and liq["move_class"] == "DESLOCAMENTO_POS_SWEEP"
        # sem reclaim => sem evento (queda continua)
        bars2 = bars[:44] + [mk(44, 100, 100.1, 95.5, 95.7), mk(45, 95.7, 96.0, 94.9, 95.0),
                             mk(46, 95.0, 95.3, 94.5, 94.6), mk(47, 94.6, 94.9, 94.2, 94.3)]
        liq2 = compute(bars2)
        s2 = (liq2 or {}).get("sequence", {}).get("low")
        ok4 = liq2 is not None and (s2 is None or s2["state"] == "FAILED") \
            and liq2["move_class"] != "DESLOCAMENTO_POS_SWEEP"   # queda contínua NUNCA lê como genuíno
        # iniciativa para íman: subida com zona-do-trader SHORT ao alcance, sem sweep dos lows
        bars3 = [mk(i, 100 + i * 0.05, 100.3 + i * 0.05, 99.9 + i * 0.05, 100.1 + i * 0.05) for i in range(48)]
        liq3 = compute(bars3, tmap_zones=[{"low": 102.6, "high": 103.4, "tese": "SHORT"}])
        ok5 = liq3 and liq3["direction"] == "up" and liq3["move_class"] == "INICIATIVA_PARA_IMAN"
        ok6 = liq3 and any("zona-do-trader" in m for m in liq3["opposing_magnets"])
        # FAILED: reclaim e depois close abaixo do extremo varrido (95.5)
        bars4 = bars[:46] + [mk(46, 99.5, 99.6, 95.0, 95.2), mk(47, 95.2, 95.3, 94.6, 94.8)]
        liq4 = compute(bars4)
        s4 = (liq4 or {}).get("sequence", {}).get("low")
        ok7 = s4 and s4["state"] == "FAILED"
        ok8 = render_section(liq) and "DESLOCAMENTO PÓS-SWEEP" in render_section(liq)
        for lab, ok in (("sweep+reclaim+hold => HOLDING", ok1), ("trapped=shorts", ok2),
                        ("classe DESLOCAMENTO_POS_SWEEP", ok3), ("sem reclaim => sem evento", ok4),
                        ("subida p/ zona SHORT => INICIATIVA_PARA_IMAN", ok5), ("iman nomeado", ok6),
                        ("re-perda => FAILED", ok7), ("render ok", ok8)):
            print(f"  [{'OK' if ok else 'FAIL'}] {lab}")
        allok = all([ok1, ok2, ok3, ok4, ok5, ok6, ok7, ok8])
        print("selftest", "PASS" if allok else "FAIL")
        sys.exit(0 if allok else 1)
    # live probe
    liq = read_liquidity()
    print(json.dumps(liq, indent=1)[:1500] if liq else "eixo indisponível")
