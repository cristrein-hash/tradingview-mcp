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
COOLDOWN_S = 2 * 3600      # por zona; override se novo extremo > anterior +0.5×ATR
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
    if not atr15 or zone.get("criticidade") != "critica":
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
    return g, notes


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
        return "tg" if E2._tg_send(txt) else "tg-fail"
    except Exception:
        return "tg-erro"


def load_bars(n=40):
    try:
        with open(BARS_F, "rb") as f:
            f.seek(0, 2); size = f.tell(); f.seek(max(0, size - 12000))
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


def scan_zones(cur, tf, atr, tmap, fired):
    """Verifica a vela `cur` (TF `tf`) contra todas as zonas do mapa; alerta na rejeição. Dedup por (tf,zona).
    Estendido a 1H por ordem do Cris (04/08): a rejeição 1H das 18:00 foi o sinal mais claro do dia e a vigia
    só corria em 15M. Mesma régua-de-zona, ATR próprio do TF. (5M fica de fora — ordem Cris: ruído.)"""
    for zone in tmap["zones"]:
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
        try:
            import e2_quality as E2
            dsr = E2.load_dossier() or {}
        except Exception:
            dsr = {}
        g, notes = grade(read, dsr)
        tgts = targets_for(read, tmap, dsr) if dsr else []
        txt = alert_text(read, zone, g, notes, tgts, cur["t"], tf)
        print(txt, flush=True)
        print(f"(canal: {_tg(txt)})", flush=True)
        if CONSULT and dsr:
            try:
                import e2_quality as E2
                cand = {"direction": read["direction"], "rule": "zone_reject", "tf": tf,
                        "entry": read["entry"], "sl": read["sl"],
                        "target": tgts[0] if tgts else (read["entry"] - 3 * abs(read["entry"] - read["sl"])
                                                        if read["direction"] == "SHORT" else
                                                        read["entry"] + 3 * abs(read["entry"] - read["sl"])),
                        "rr": 3.0, "materiality": {"sl_atr": None, "confluence": None, "confluence_breakdown": {}}}
                th = E2.run_read(cand, dsr)
                if not th.get("error"):
                    print(f"   juízo do reader ({tf}): surfaced={E2.surfaced(th, cand)} · "
                          f"convicção {th.get('conviction')} · {str(th.get('thesis'))[:180]}", flush=True)
            except Exception as e:
                print(f"   (reader consult falhou: {type(e).__name__})", flush=True)


def main_loop():
    print("🕯️ vela-no-nível armado: leio cada barra 15M E 1H FECHADA nas zonas CRÍTICAS do mapa do trader "
          f"(1H estendido por ordem Cris 04/08; telegram={'ON' if VELA_LIVE else 'OFF/chat'})")
    last_t15 = None; last_t1h = None
    fired = {}                                    # (tf, zone_id) -> (ts, extreme)
    while True:
        try:
            bars = load_bars()
            if len(bars) >= 16:
                tmap = trader_map.load_map()
                # 15M — cada barra fechada (comportamento original)
                cur15 = bars[-1]
                if cur15["t"] != last_t15:
                    last_t15 = cur15["t"]
                    if tmap:
                        scan_zones(cur15, "15", atr14(bars), tmap, fired)
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
        for lab, ok in (("09:00 dispara SHORT (aceitação a)", ok1), ("sem toque nao dispara", ok2),
                        ("fechou em cima nao dispara", ok3), ("doji na zona nao dispara", ok4),
                        ("espelho LONG na demanda dispara", ok5),
                        ("1H 18:00 rejeição premium dispara (Cris)", ok6), ("agregação 1H 4x15m ok", ok7),
                        ("pavio 37.5% na OB dispara com novo threshold 35%", ok8)):
            print(f"  [{'OK' if ok else 'FAIL'}] {lab}")
        allok = all([ok1, ok2, ok3, ok4, ok5, ok6, ok7, ok8])
        print("selftest", "PASS" if allok else "FAIL")
        sys.exit(0 if allok else 1)
    main_loop()
