#!/usr/bin/env python3
"""VELA-NO-NÍVEL — copiloto de leitura de barra nas zonas CRÍTICAS do MAPA DO TRADER (Cris 2026-08-04).

A peça que faltou em 04/08: a vela 15M das 09:00 tocou 4073 (zona declarada), imprimiu pavio de absorção
de 57% e fechou de volta — e nenhum componente a leu no fecho. Este daemon lê CADA barra 15M FECHADA nas
zonas 'critica' do mapa e alerta IMEDIATAMENTE (~35s pós-fecho) com a leitura completa.

FILOSOFIA: advisory-to-human, RECALL alto — a 1ª rejeição DISPARA (deliberadamente mais sensível que o R10,
que exige >=2 rejeições). O Cris julga; o alerta descreve. Grau A = assinatura+absorção+regime alinhados;
grau B = só assinatura de vela (contexto não confirma) — sempre honesto.
Thresholds = FIT calibrados na vela 09:00 de 04/08 (pavio 57% range / 0.82×ATR): rever na 1ª semana.
Telegram só com VELA_PRODUCTION_AUTHORIZED=1 (hard-lock); senão chat/stdout. py3.9."""
import os, sys, json, time, datetime as dt
from pathlib import Path
from zoneinfo import ZoneInfo

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
import trader_map

LX = ZoneInfo("Europe/Lisbon")
REPO = BASE.parent
BARS_F = REPO / "my-strategy/core/bar_store/store/bars_15m.jsonl"

# FIT (calibrados na vela 09:00 04/08; rever na 1ª semana de shadow)
TOUCH_BUF = 1.0            # toque = wick chega a <=1pt da borda (valor do vigia)
WICK_MIN_RANGE = 0.35      # pavio >= 35% do range (Cris 04/08: "qualquer pavio 35-50% vale, EM região OB")
WICK_MIN_ATR = 0.30        # piso baixo (só mata dojis minúsculos); a REGIÃO OB (zona do mapa) é o filtro de ruído,
                           # não o tamanho do pavio — por isso o piso ATR desceu p/ o 35% passar em vela normal
SL_BUF_ATR = 0.15          # SL = extremo do wick + 0.15×ATR
COOLDOWN_S = 2 * 3600
_TOUCH5 = {}          # zona_id -> [ts das rejeições 5M] (2ª-rejeição, ordem Cris 05/08)      # por zona; override se novo extremo > anterior +0.5×ATR
VELA_LIVE = os.environ.get("VELA_PRODUCTION_AUTHORIZED", "") == "1"
CONSULT = os.environ.get("VELA_READER_CONSULT", "1") == "1"


def hm(t):
    return dt.datetime.fromtimestamp(int(t), LX).strftime("%d/%m %H:%M")


def atr14(bars):
    if len(bars) < 15:
        return None
    trs = []
    for i in range(1, len(bars)):
        h, l, pc = bars[i]["h"], bars[i]["l"], bars[i - 1]["c"]
        trs.append(max(h - l, abs(h - pc), abs(l - pc)))
    n = min(14, len(trs))
    return sum(trs[-n:]) / n


def decide(bar, zone, atr15):
    """Função PURA de decisão (testável; usada pela aceitação). Devolve leitura ou None.
    tese SHORT: toque na borda inferior da supply + pavio superior de rejeição + fecho de volta em baixo.
    tese LONG (espelho): toque na borda superior da demanda + pavio inferior + fecho de volta em cima."""
    if not atr15:
        return None
    o, h, l, c = bar["o"], bar["h"], bar["l"], bar["c"]
    rng = h - l
    if rng <= 0:
        return None
    zl, zh = zone["low"], zone["high"]
    mid = (zl + zh) / 2.0
    if zone["tese"] == "SHORT":
        if h < zl - TOUCH_BUF:                                   # nunca tocou a zona
            return None
        wick = h - max(o, c)
        if wick < WICK_MIN_RANGE * rng or wick < WICK_MIN_ATR * atr15:
            return None
        # REJEIÇÃO baseada na ZONA (fix Cris 04/08: a vela 18:00 fechou 4099.85 = ABAIXO da premium 4101,
        # rejeição real, mas falhava por 0.36pt a regra antiga de "metade inferior da vela"). Rejeitou se:
        # fechou de volta ABAIXO da zona, OU na metade inferior da própria vela — e nunca na metade sup. da zona.
        rejected = (c < zl) or (c <= l + 0.5 * rng)
        if not rejected or c > mid:
            return None
        sl = round(h + SL_BUF_ATR * atr15, 2)
        return {"direction": "SHORT", "entry": round(c, 2), "sl": sl, "wick_pts": round(wick, 2),
                "wick_pct": round(100 * wick / rng), "wick_atr": round(wick / atr15, 2),
                "touch_extreme": h, "zone_id": zone["id"]}
    if zone["tese"] == "LONG":
        if l > zh + TOUCH_BUF:
            return None
        wick = min(o, c) - l
        if wick < WICK_MIN_RANGE * rng or wick < WICK_MIN_ATR * atr15:
            return None
        rejected = (c > zh) or (c >= h - 0.5 * rng)             # espelho: fechou acima da zona OU metade sup. da vela
        if not rejected or c < mid:
            return None
        sl = round(l - SL_BUF_ATR * atr15, 2)
        return {"direction": "LONG", "entry": round(c, 2), "sl": sl, "wick_pts": round(wick, 2),
                "wick_pct": round(100 * wick / rng), "wick_atr": round(wick / atr15, 2),
                "touch_extreme": l, "zone_id": zone["id"]}
    return None


def grade(read, dsr):
    """Grau A (absorção + regime alinhados) vs B (só assinatura). Soft — nunca gate."""
    notes = []
    a_absorb = a_regime = False
    try:
        conf = ((dsr.get("axes", {}).get("confluence") or {}).get("15") or {})
        win = conf.get("window") or {}
        wb = (win.get("buy") or {}).get("n") or 0
        ws = (win.get("sell") or {}).get("n") or 0
        if read["direction"] == "SHORT" and wb > 0 and (win.get("net_side") == "buy" or wb >= ws):
            a_absorb = True; notes.append(f"compra (janela buy {wb}/{ws}) ABSORVIDA na supply = distribuição")
        if read["direction"] == "LONG" and ws > 0 and (win.get("net_side") == "sell" or ws >= wb):
            a_absorb = True; notes.append(f"venda (janela sell {ws}/{wb}) ABSORVIDA na demanda = acumulação")
        reg = dsr.get("axes", {}).get("regime") or {}
        r4 = (reg.get("v5_4h") or {}).get("regime"); r1d = (reg.get("structural_1d") or {}).get("regime")
        want = "BEAR" if read["direction"] == "SHORT" else "BULL"
        n_al = sum(1 for r in (r4, r1d) if r == want)
        if n_al >= 1:
            a_regime = True; notes.append(f"regime {r4}/{r1d} a favor")
        else:
            notes.append(f"regime {r4}/{r1d} não confirma")
    except Exception:
        notes.append("contexto indisponível")
    g = "A" if (a_absorb and a_regime) else "B"
    return g, notes, a_regime


def targets_for(read, tmap, dsr):
    """Alvos = próximas zonas opostas do mapa; fallback zones/magnets do dossiê."""
    tg = []
    entry = read["entry"]
    if read["direction"] == "SHORT":
        for z in sorted(tmap["zones"], key=lambda x: -x["high"]):
            if z["high"] < entry and z["tese"] in ("LONG", "NEUTRA"):
                tg.append(z["high"])
        try:
            zb = ((dsr["axes"]["mtf"].get("60", {}) or {}).get("zones") or {}).get("below") or {}
            if zb.get("high") and zb["high"] < entry:
                tg.append(zb["high"])
        except Exception:
            pass
    else:
        for z in sorted(tmap["zones"], key=lambda x: x["low"]):
            if z["low"] > entry and z["tese"] in ("SHORT", "NEUTRA"):
                tg.append(z["low"])
        try:
            za = ((dsr["axes"]["mtf"].get("60", {}) or {}).get("zones") or {}).get("above") or {}
            if za.get("low") and za["low"] > entry:
                tg.append(za["low"])
        except Exception:
            pass
    uniq = []
    for t in tg:
        if not any(abs(t - u) < 3 for u in uniq):
            uniq.append(round(t, 2))
    return uniq[:2]


def alert_text(read, zone, g, notes, tgts, bar_t, tf="15"):
    r = abs(read["entry"] - read["sl"])
    rrs = " / ".join(f"{abs(read['entry'] - t) / r:.1f}" for t in tgts) if (tgts and r > 0) else "—"
    tgt_s = " / ".join(str(t) for t in tgts) if tgts else "—"
    tflabel = "1H" if tf == "60" else f"{tf}M"
    return (f"🕯️ VELA-NO-NÍVEL {tflabel} — COPILOTO (leitura de barra, NÃO é sinal E2)\n"
            f"zona declarada {zone['low']:.2f}–{zone['high']:.2f} (tese {zone['tese']}, crítica): a vela {tflabel} "
            f"das {hm(bar_t)} tocou {read['touch_extreme']}, pavio {read['wick_pts']}pts "
            f"({read['wick_pct']}% do range, {read['wick_atr']}×ATR) e fechou de volta em {read['entry']}.\n"
            f"{'; '.join(notes)}. [grau {g}]\n"
            f"Leitura {read['direction']}: entry {read['entry']} · SL {read['sl']} · alvos {tgt_s} · RR {rrs}\n"
            f"(alta sensibilidade por desenho — 1ª rejeição dispara; tu julgas. Não é o gatilho R10.)")


def _tg(txt):
    if not VELA_LIVE:
        return "chat-only"
    try:
        import e2_quality as E2
        return "tg" if E2._tg_send(txt, audience="assistant") else "tg-fail"
    except Exception:
        return "tg-erro"


def load_bars(n=80):
    try:
        with open(BARS_F, "rb") as f:
            f.seek(0, 2); size = f.tell(); f.seek(max(0, size - 30000))
            rows = [json.loads(l) for l in f.read().decode(errors="ignore").splitlines()
                    if l.strip() and l[0] == "{"]
        rows = [b for b in rows if all(k in b for k in ("t", "o", "h", "l", "c"))]
        return rows[-n:]
    except Exception:
        return []


def load_bars_5m(n=60):
    """5M do store — SÓ para o fast-lane das zonas com fast_5m (ordem Cris 05/08: toque em 4116/premium
    precisa reação em 5M; 15M/1H atrasam a entrada). Fora dessas zonas, 5M continua fora (ruído)."""
    try:
        with open(BARS_F.parent / "bars_5m.jsonl", "rb") as f:
            f.seek(0, 2); size = f.tell(); f.seek(max(0, size - 30000))
            rows = [json.loads(l) for l in f.read().decode(errors="ignore").splitlines()
                    if l.strip() and l[0] == "{"]
        rows = [b for b in rows if all(k in b for k in ("t", "o", "h", "l", "c"))]
        return rows[-n:]
    except Exception:
        return []


def agg_1h(m15):
    """Agrega 15m em velas 1H (bucket t//3600). _n15==4 = hora COMPLETA (fechada). Store não tem bars_1h."""
    buckets = {}
    for b in m15:
        hb = (b["t"] // 3600) * 3600
        buckets.setdefault(hb, []).append(b)
    out = []
    for hb in sorted(buckets):
        g = sorted(buckets[hb], key=lambda x: x["t"])
        out.append({"t": hb, "o": g[0]["o"], "h": max(x["h"] for x in g),
                    "l": min(x["l"] for x in g), "c": g[-1]["c"], "_n15": len(g)})
    return out


def check_break_continuation(cur, tf, atr, tmap, bars15, fired):
    """SINAL DE CONTINUIDADE SHORT no break do nível-gatilho (Cris 04/08: 'se cortar abaixo de 4075 quero
    entrada de continuidade planeada'). Determinístico: fecho DECISIVO (>=0.1·ATR) abaixo de
    tese_geral.nivel_confirmacao_short. Entry=fecho do break · SL=swing-high recente+0.15·ATR · alvo=OB
    Detector abaixo (lido do dossiê, NÃO inventado). Dedup por TF."""
    tg = (tmap.get("tese_geral") or {})
    lvl = tg.get("nivel_confirmacao_short")
    if not lvl or not atr:
        return
    c = cur["c"]
    if c >= lvl - 0.05 * atr:                      # sem FECHO decisivo abaixo do nível (token p/ evitar wick-only)
        return
    key = ("BREAK_CONT", tf)
    prev = fired.get(key)
    if prev and time.time() - prev[0] < COOLDOWN_S and c > prev[1] - 0.5 * atr:
        return                                      # já sinalizado; só re-sinaliza em nova extensão
    fired[key] = (time.time(), c)
    swing_high = max((b["h"] for b in bars15[-8:-1]), default=cur["h"])
    sl = round(max(swing_high, cur["h"]) + 0.15 * atr, 2)
    # alvo = OB Detector abaixo (dossiê); fallback 2.5R
    try:
        import e2_quality as E2
        dsr = E2.load_dossier() or {}
        ax = dsr.get("axes", {})
        tgs = []
        for t in ("60", "240", "15"):
            z = ((ax.get("mtf", {}).get(t, {}) or {}).get("zones") or {}).get("below") or {}
            if z.get("high") and z["high"] < c:
                tgs.append(z["high"])
        tgt = max(tgs) if tgs else round(c - 2.5 * (sl - c), 2)   # OB mais próximo abaixo
    except Exception:
        dsr = {}; tgt = round(c - 2.5 * (sl - c), 2)
    risk = sl - c
    rr = round((c - tgt) / risk, 1) if risk > 0 else 0
    tflabel = "1H" if tf == "60" else f"{tf}M"
    if not tg_claim(f"break_{cur['t']}"):
        print("(break: dedup — evento já alertado)", flush=True)
        return
    txt = (f"🔻 SINAL SHORT — CONTINUIDADE (break de {lvl})\n"
           f"vela {tflabel} das {hm(cur['t'])} FECHOU {c} abaixo do gatilho {lvl} = quebra confirmada, "
           f"continuação bear.\n"
           f"Entry {c} (ou retest de {lvl} por baixo) · SL {sl} (acima do swing {swing_high:.2f}) · "
           f"alvo {tgt} (OB Detector) · RR {rr}\n"
           f"(entrada PLANEADA de continuidade — a decisão é tua)")
    print(txt, flush=True)
    # TG só sinal OPERÁVEL (Cris 05/08: apenas entry/SL/TP claros): 1º break do nível E RR>=1.5.
    # Re-extensões (preço já longe do gatilho) e RR pobre = chat-only — o RR 0.3 das 00:15 no TG foi spam.
    if prev is not None or (rr and rr < 1.5):
        why = "re-extensão" if prev is not None else "RR<1.5"
        print(f"(canal: chat-only — {why})", flush=True)
        return
    print(f"(canal: {_tg(txt)})", flush=True)




def tg_claim(key):
    """True se somos os PRIMEIROS a alertar este evento (dedup entre daemons + zonas sobrepostas).
    Chave = classe_evento + t da vela. Lockfile O_EXCL em logs/.tg_dedup (limpos >24h)."""
    import os
    d = BASE.parent / "alert-bridge" / "logs" / ".tg_dedup"
    try:
        d.mkdir(exist_ok=True)
        now = time.time()
        for f in d.iterdir():
            if now - f.stat().st_mtime > 86400:
                f.unlink(missing_ok=True)
        fd = os.open(str(d / f"{key}.lock"), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.close(fd)
        return True
    except FileExistsError:
        return False
    except Exception:
        return True                                    # fail-open: melhor duplicar que silenciar


def scan_zones(cur, tf, atr, tmap, fired):
    """Verifica a vela `cur` (TF `tf`) contra todas as zonas do mapa; alerta na rejeição. Dedup por (tf,zona).
    Estendido a 1H por ordem do Cris (04/08): a rejeição 1H das 18:00 foi o sinal mais claro do dia e a vigia
    só corria em 15M. Mesma régua-de-zona, ATR próprio do TF. (5M fica de fora — ordem Cris: ruído.)"""
    consulted = False
    for zone in tmap["zones"]:
        if zone.get("criticidade") != "critica":
            continue
        read = decide(cur, zone, atr)
        if not read:
            continue
        key = (tf, zone["id"])
        prev = fired.get(key)
        if prev and time.time() - prev[0] < COOLDOWN_S:
            new_ext = (read["touch_extreme"] > prev[1] + 0.5 * (atr or 6)) if read["direction"] == "SHORT" \
                else (read["touch_extreme"] < prev[1] - 0.5 * (atr or 6))
            if not new_ext:
                continue
        fired[key] = (time.time(), read["touch_extreme"])
        # ---- GUARDAS ANTI-PERDA (Cris 05/08 13:2x, após SL do sinal 13:10) — correm ANTES do reader ----
        guard_block = None
        # (1) ESCADARIA 5M: >=4 das últimas 5 velas verdes com highs a subir = perna impulsiva; rejeição de
        #     1 vela é pausa, não topo (o sinal 13:10 vendeu uma escadaria de 5 verdes).
        if tf == "5":
            _b5 = load_bars_5m(6)
            b5g = _b5[:-1]                                   # exclui a própria vela da rejeição
            if len(b5g) >= 5:
                greens = sum(1 for b in b5g if b["c"] > b["o"])
                hh_up = all(b5g[x]["h"] >= b5g[x-1]["h"] for x in range(1, len(b5g)))
                if read["direction"] == "SHORT" and greens >= 4 and hh_up:
                    guard_block = "escadaria 5M (>=4 verdes, HH) — pausa, não topo"
        # (2) 2ª REJEIÇÃO (ordem Cris: TG do fast-5M só na 2ª rejeição da zona; a 1ª = aviso de copiloto)
        if tf == "5" and guard_block is None:
            hist = _TOUCH5.setdefault(zone["id"], [])
            now_g = time.time()
            hist[:] = [h for h in hist if now_g - h < 4 * 3600]
            hist.append(now_g)
            if len(hist) < 2:
                guard_block = "1ª rejeição da zona — copiloto; TG só na 2ª (ordem Cris 05/08)"
        # (3) FRESCURA NO ENVIO: se o preço corrente já está além do SL, o sinal nasceu morto (13:10→13:16)
        if guard_block is None:
            b5f = load_bars_5m(2)
            px_now = b5f[-1]["c"] if b5f else None
            if px_now is not None:
                if (read["direction"] == "SHORT" and px_now >= read["sl"]) or \
                   (read["direction"] == "LONG" and px_now <= read["sl"]):
                    guard_block = f"JÁ INVALIDADO no envio (preço {px_now} além do SL {read['sl']})"
        try:
            import e2_quality as E2
            dsr = E2.load_dossier() or {}
        except Exception:
            dsr = {}
        g, notes, _reg_ok = grade(read, dsr)
        tgts = targets_for(read, tmap, dsr) if dsr else []
        txt = alert_text(read, zone, g, notes, tgts, cur["t"], tf)
        # GATE DO READER NO TELEGRAM DA VELA (ordem Cris 05/08 ~06:1x: "aplica mesmo gate do reader no
        # Telegram da vela"). A vela grau-A com absorção MECÂNICA (janela buy N/0) chegava ao TG mesmo com
        # o reader a refutar ("sem absorção efetiva, short prematuro"). Agora: reader julga ANTES; grau A
        # que o reader NÃO confirma = chat-only. Fail-open: reader indisponível → envia (avaria não cala).
        if guard_block:
            print(txt, flush=True)
            print(f"(canal: chat-only — guarda: {guard_block})", flush=True)
            continue
        jz = ""; ok_reader = (read["direction"] == "LONG")   # SHORT fail-closed, LONG fail-open (Cris 10/08)
        if CONSULT and dsr:
            try:
                import e2_quality as E2
                cand = {"direction": read["direction"], "rule": "zone_reject", "tf": tf,
                        "entry": read["entry"], "sl": read["sl"],
                        "target": tgts[0] if tgts else (read["entry"] - 3 * abs(read["entry"] - read["sl"])
                                                        if read["direction"] == "SHORT" else
                                                        read["entry"] + 3 * abs(read["entry"] - read["sl"])),
                        "rr": 3.0, "materiality": {"sl_atr": None, "confluence": None, "confluence_breakdown": {}}}
                th = E2.run_read(cand, dsr, timeout=90)
                if not th.get("error"):
                    sf = E2.surfaced(th, cand)
                    cv = E2.fnum(th.get("conviction")) or 0
                    thesis = str(th.get("thesis") or "")
                    premature = any(w in thesis.lower() for w in
                                    ("prematur", "ainda a sub", "antecipa", "sem rejeição", "não imp"))
                    jz = (f"\nreader: {'CONFIRMA' if sf else 'NÃO confirma'} · conv {th.get('conviction')} · "
                          f"{thesis[:150]}")
                    ok_reader = bool(sf) and cv >= 55 and not premature
            except Exception as e:
                jz = f"\n(reader indisponível: {type(e).__name__} — enviado sem juízo)"
        txt = txt + jz
        print(txt, flush=True)
        if not ok_reader:
            print("(canal: chat-only — reader refutou a vela)", flush=True)
        elif tg_claim(f"reject_{tf}_{cur['t']}"):      # 1 Telegram por vela+classe (zonas sobrepostas + validador)
            print(f"(canal: {_tg(txt)})", flush=True)
        else:
            print("(canal: dedup — evento já alertado)", flush=True)


def main_loop():
    print("🕯️ vela-no-nível armado: leio cada barra 15M E 1H FECHADA nas zonas CRÍTICAS do mapa do trader "
          f"(1H estendido por ordem Cris 04/08; telegram={'ON' if VELA_LIVE else 'OFF/chat'})")
    last_t15 = None; last_t1h = None; last_t5 = None
    fired = {}                                    # (tf, zone_id) -> (ts, extreme)
    while True:
        try:
            bars = load_bars()
            if len(bars) >= 16:
                tmap = trader_map.load_map()
                # OB AUTO-WATCH (Cris 10/08: "descobrir demandas onde capitula, não só as declaradas").
                # Injeta as demandas OB Detector perto do preço como zonas CRÍTICAS LONG — o scan_zones
                # trata-as igual às declaradas (rejeição + gate do reader + dedup). Fail-safe: se falha,
                # a vela segue só com o mapa declarado. Dedup vs declaradas dentro de load_ob_zones.
                if tmap:
                    try:
                        import ob_watch
                        px = bars[-1]["c"]
                        obz = ob_watch.load_ob_zones(px, tmap["zones"])
                        if obz:
                            tmap = {**tmap, "zones": tmap["zones"] + obz}
                    except Exception as e:
                        print(f"ob_watch erro transitório: {type(e).__name__}:{str(e)[:50]}", flush=True)
                # FAST-LANE 5M (ordem Cris 05/08): zonas fast_5m (premium 4101-4116, toque 4116) lidas a
                # cada 5M fechada — rejeição lá = entrada rápida, 15M/1H atrasam. Restrito às zonas marcadas.
                if tmap and any(z.get("fast_5m") for z in tmap["zones"]):
                    b5 = load_bars_5m()
                    if len(b5) >= 16 and b5[-1]["t"] != last_t5:
                        last_t5 = b5[-1]["t"]
                        fmap = {"zones": [z for z in tmap["zones"] if z.get("fast_5m")],
                                "tese_geral": {}}
                        scan_zones(b5[-1], "5", atr14(b5), fmap, fired)
                # 15M — cada barra fechada (comportamento original)
                cur15 = bars[-1]
                if cur15["t"] != last_t15:
                    last_t15 = cur15["t"]
                    if tmap:
                        a15 = atr14(bars)
                        scan_zones(cur15, "15", a15, tmap, fired)
                        check_break_continuation(cur15, "15", a15, tmap, bars, fired)   # break-4075 = short continuidade
                # 1H — cada HORA COMPLETA fechada (agregada de 4×15m); só quando fecha uma nova hora
                h1 = agg_1h(bars)
                complete = [b for b in h1 if b.get("_n15") == 4]
                if complete:
                    cur1h = complete[-1]
                    if cur1h["t"] != last_t1h:
                        last_t1h = cur1h["t"]
                        if tmap:
                            scan_zones(cur1h, "60", atr14(complete), tmap, fired)
        except Exception as e:
            print(f"vela-no-nível erro transitório: {type(e).__name__}:{str(e)[:60]}", flush=True)
        time.sleep(45)


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        z = {"id": "s", "low": 4066.0, "high": 4073.0, "tese": "SHORT", "criticidade": "critica", "nota": ""}
        b0900 = {"t": 1785830400, "o": 4065.36, "h": 4073.04, "l": 4064.72, "c": 4068.28}
        r = decide(b0900, z, 5.77)
        ok1 = r and r["direction"] == "SHORT" and r["entry"] == 4068.28 and r["sl"] >= 4073.9
        b_notouch = {"t": 2, "o": 4059.0, "h": 4064.57, "l": 4058.4, "c": 4059.31}
        ok2 = decide(b_notouch, z, 5.77) is None
        b_nowick = {"t": 3, "o": 4066.0, "h": 4073.0, "l": 4065.5, "c": 4072.5}       # fechou em cima
        ok3 = decide(b_nowick, z, 5.77) is None
        b_doji = {"t": 4, "o": 4068.0, "h": 4069.5, "l": 4067.5, "c": 4068.2}          # pavio minúsculo <0.6ATR
        ok4 = decide(b_doji, z, 5.77) is None
        zl = {"id": "d", "low": 4028.0, "high": 4036.0, "tese": "LONG", "criticidade": "critica", "nota": ""}
        b_long = {"t": 5, "o": 4037.0, "h": 4038.5, "l": 4029.0, "c": 4036.8}          # pavio inferior + fecho em cima
        rl = decide(b_long, zl, 5.77)
        ok5 = rl and rl["direction"] == "LONG" and rl["sl"] <= 4028.2
        # 1H 18:00 (Cris 04/08): rejeição da premium 4101-4116 — o sinal mais claro do dia, tem de disparar
        zp = {"id": "premium", "low": 4101.07, "high": 4116.28, "tese": "SHORT", "criticidade": "critica", "nota": ""}
        b1h_1800 = {"t": 1785862800, "o": 4093.46, "h": 4106.46, "l": 4086.26, "c": 4086.26}
        r1h = decide(b1h_1800, zp, 15.0)
        ok6 = r1h and r1h["direction"] == "SHORT" and r1h["entry"] == 4086.26 and r1h["sl"] > 4106
        # agregação 1H: 4×15m -> 1 hora completa
        m = [{"t": 1785862800 + i * 900, "o": 4093 + i, "h": 4106 - i, "l": 4092 + i, "c": 4095 + i} for i in range(4)]
        agg = agg_1h(m)
        ok7 = len(agg) == 1 and agg[0]["_n15"] == 4 and agg[0]["o"] == 4093 and agg[0]["h"] == 4106
        # NOVO THRESHOLD 35% (Cris 04/08): pavio de 37.5% na premium + fecho abaixo da zona -> dispara agora
        # (com o antigo 45% NÃO disparava). Prova o ajuste do threshold.
        b37 = {"t": 9, "o": 4103.0, "h": 4106.0, "l": 4098.0, "c": 4100.0}
        r37 = decide(b37, zp, 7.9)
        wick37 = 4106.0 - 4103.0; ok8 = r37 and r37["direction"] == "SHORT" and abs(wick37 / 8.0 - 0.375) < 0.01
        # break-continuidade: fecho decisivo abaixo do nível-gatilho dispara (Cris 04/08)
        tmap_fix = {"tese_geral": {"nivel_confirmacao_short": 4075.0}, "zones": []}
        b15fix = [{"t": i, "o": 4080, "h": 4086, "l": 4078, "c": 4082} for i in range(8)]
        firedbc = {}
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            check_break_continuation({"t": 1785870000, "o": 4076, "h": 4077, "l": 4072, "c": 4072.5},
                                     "15", 7.9, tmap_fix, b15fix, firedbc)
        ok9 = "SINAL SHORT — CONTINUIDADE" in buf.getvalue() and ("BREAK_CONT", "15") in firedbc
        # não dispara se fecha ACIMA do nível
        firedbc2 = {}
        with contextlib.redirect_stdout(io.StringIO()):
            check_break_continuation({"t": 1785870000, "o": 4078, "h": 4080, "l": 4076, "c": 4079},
                                     "15", 7.9, tmap_fix, b15fix, firedbc2)
        ok10 = ("BREAK_CONT", "15") not in firedbc2
        for lab, ok in (("09:00 dispara SHORT (aceitação a)", ok1), ("sem toque nao dispara", ok2),
                        ("fechou em cima nao dispara", ok3), ("doji na zona nao dispara", ok4),
                        ("espelho LONG na demanda dispara", ok5),
                        ("1H 18:00 rejeição premium dispara (Cris)", ok6), ("agregação 1H 4x15m ok", ok7),
                        ("pavio 37.5% na OB dispara com novo threshold 35%", ok8),
                        ("break <4075 dispara SHORT continuidade", ok9),
                        ("fecho acima do nível NAO dispara break", ok10)):
            print(f"  [{'OK' if ok else 'FAIL'}] {lab}")
        allok = all([ok1, ok2, ok3, ok4, ok5, ok6, ok7, ok8, ok9, ok10])
        print("selftest", "PASS" if allok else "FAIL")
        sys.exit(0 if allok else 1)
    main_loop()
