#!/usr/bin/env python3
"""DETETOR DE CHOQUE DE PREÇO (Cris 2026-07-18; deteção por EXCURSÃO v3 2026-07-20) — o gatilho realtime
MAIS RÁPIDO, independente de news feeds: o mercado precifica a notícia ANTES dos feeds a reportarem. Loop 30s:
lê as barras 5M live (forming incl.) e mede a maior EXCURSÃO rápida (high/low vs close anterior, ≤5min).
CHOQUE = excursão ≥ 10 pts (MAJOR ≥ 18). Medir por high/low (não close-to-close) é o que apanha WICKS que
recuperam — ex. queda a 4001 que voltou a 4009 (close-to-close via só −3, a excursão vê −11). Histórico das
calibrações falhadas: ATR5 close-to-close = zigzag (~3pts); ATR15 close-to-close = perdia wicks. Absoluto em
pontos = o que o trader sente. Na hora: snapshot (lido pelo news_gate → E0/E2) + Telegram (dedup+cooldown
600s). Fail-closed, horas Lisboa, py3.9. CLI: --once (default 1 ciclo)."""
import os, sys, json, time, datetime as dt
from pathlib import Path
from zoneinfo import ZoneInfo
HERE = Path(__file__).resolve().parent
CORE = HERE.parent
sys.path.insert(0, str(CORE)); sys.path.insert(0, "/Users/cristrein/tradingview-mcp/alert-bridge")
import tab_pin
from draw_xau_4h_trades import MCPClient
import context_structure as cs
import mtf_cross as mx                     # motor de cruzamento MTF (OB tipado + SVP + SMC + regime + NAS + Bubbles)
LX = ZoneInfo("Europe/Lisbon")
STATE = HERE / ".shock_state"; STATE.mkdir(exist_ok=True)
SHOCK_F = STATE / "shock.json"          # lido pelo news_gate (price_shock_now)
ALERT_F = STATE / "alert_state.json"
LOG = STATE / "shock_cycle.log"
OB_TOUCH_F = STATE / "ob_touch_state.json"          # dedup do alerta de toque em zona OB
PB15_F = CORE / "bar_store/store/pine_boxes_15.json"  # zonas do OB Detector 15M REAIS (CRP) — NUNCA inventar
E0_F = CORE.parent.parent / "external_factors_v2/snapshots/market_context.json"  # dossiê E0 (contexto SHORT)
# CALIBRAÇÃO (v3 2026-07-20: deteção por EXCURSÃO high/low, não close-to-close). Choque = maior excursão
# rápida (≤5min, high/low da barra 5M) ≥ limiar em PONTOS ABSOLUTOS. Provado nos dados reais de hoje:
# apanha 4/132 barras (spike 4040 +18, wick 4001 −11, +2 moves 10-13pts) e ignora 95% normais (range<8).
# Absoluto (não ATR) porque um trader sente PONTOS; ATR5 dava zigzag, ATR15 perdia wicks. Editável.
SHOCK_PTS = 10.0        # choque = excursão ≥ 10 pts em ≤5min (movimento real de ouro; <10 = ruído)
MAJOR_PTS = 18.0        # choque MAJOR ≥ 18 pts
WINDOW_S = 300          # a excursão de 1 barra 5M = janela ≤5 min
COOLDOWN_S = 600        # ≥10 min entre alertas Telegram
iso = lambda t: dt.datetime.fromtimestamp(int(t), LX).strftime("%H:%M:%S")


def _log(o):
    with open(LOG, "a") as fh: fh.write(json.dumps(o, ensure_ascii=False) + "\n")


def read_live():
    """Preço live do 5M (forming bar, high/low ao vivo) + ATR5 + barras, tab-pinned. None em falha.
    5M (não 15M) porque a DETEÇÃO agora é por EXCURSÃO (high/low da barra) — precisa da granularidade fina
    p/ apanhar WICKS rápidos que o close-to-close 15M perde (ex. wick a 4001 que recupera). Devolve
    (price, atr5, bars)."""
    tid = tab_pin.discover_tab("5")
    if not tid: return None, None, None
    os.environ["TVMCP_TARGET_CHART_ID"] = tid
    c = MCPClient(); c.start()
    try:
        oh = c.call_tool("data_get_ohlcv", {"count": 30}) or {}
        bars = oh.get("bars") or oh.get("ohlcv") or []
    finally:
        c.stop()
    if len(bars) < 16: return None, None, None
    H = [b.get("high") for b in bars]; L = [b.get("low") for b in bars]; C = [b.get("close") for b in bars]
    if any(x is None for x in H + L + C): return None, None, None
    atr = cs.atr(H, L, C, len(C) - 1, 14)               # ATR5 (só informativo agora; deteção = pontos absolutos)
    return C[-1], (atr or 2.0), bars                     # C[-1] = forming bar close = preço agora


def detect_excursion(bars, lookback=4):
    """Maior EXCURSÃO rápida (≤5min) nas últimas `lookback` barras 5M, medida por high/low vs o close da
    barra anterior — apanha WICKS (spikes que recuperam) que o close-to-close nunca vê. Devolve
    (mag_pts, direction, ref_close, extreme_price). Direção = lado da maior excursão."""
    best = (0.0, None, None, None)
    seg = bars[-(lookback + 1):] if len(bars) > lookback else bars
    for i in range(1, len(seg)):
        pc = seg[i - 1].get("close"); b = seg[i]
        hi, lo = b.get("high"), b.get("low")
        if pc is None or hi is None or lo is None:
            continue
        up, dn = hi - pc, pc - lo
        if up >= dn:
            if up > best[0]: best = (up, "ALTA", pc, hi)
        elif dn > best[0]:
            best = (dn, "BAIXA", pc, lo)
    return best


def _read_ob15_zones():
    """Zonas do OB Detector 15M REAIS do store (pine_boxes, CRP — NUNCA inventadas). Devolve [(hi, lo)]."""
    try:
        d = json.loads(PB15_F.read_text()).get("data") or {}
    except Exception:
        return []
    for s in d.get("studies", []):
        if "OB Detector" in (s.get("name") or ""):
            return [(z["high"], z["low"]) for z in (s.get("zones") or [])
                    if z.get("high") is not None and z.get("low") is not None]
    return []


def classify_zone(z, exc, im):
    """FRACO/FORTE com a PERNA IMEDIATA (15M ~3h) como DRIVER DE DIREÇÃO (Cris 2026-07-22, após 2 SHORTs FORTE
    stopados num markup: o motor shortava supply institucional porque o REGIME MACRO dizia BEAR, cego à perna de
    alta que consumia supply em cadeia). Correção:
      • A PERNA MANDA: leg UP → opera-se LONG (continuação, INCLUI romper supply no markup); leg DOWN → SHORT;
        leg RANGE → FADE das zonas (reversão: SUPPLY→SHORT, DEMAND→LONG).
      • 2 VETOS DUROS: (1) nunca CONTRA a perna imediata; (2) nunca CONTRA fluxo fresco esmagador (bubbles).
      • RSI muda de sentido por modo: continuação=MOMENTUM (LONG quer RSI alto), reversão=EXAUSTÃO (LONG quer RSI baixo).
    Devolve (dir, modo, q, checklist)."""
    ty = z["type"]
    mag, exc_dir, _, _ = exc
    regime = (im.get("regime") or {}).get("regime")
    leg = im.get("leg") or {}
    leg_dir = leg.get("dir"); leg_strong = bool(leg.get("strong")); consumed = leg.get("consumed") or 0
    bub = im.get("bubbles") or {}
    buy, sell = bub.get("buy") or 0, bub.get("sell") or 0
    mom = im.get("momentum") or {}
    adx, chop = mom.get("adx"), mom.get("chop")
    rsis = {"5M": mom.get("rsi_5m"), "15M": mom.get("rsi_15m"), "1H": mom.get("rsi_1h")}

    # 1) DIREÇÃO = perna (tendência) ou tipo-de-zona (range)
    if leg_dir == "UP":
        want, mode = "LONG", "continuação"
    elif leg_dir == "DOWN":
        want, mode = "SHORT", "continuação"
    else:
        want, mode = ("LONG" if ty == "DEMAND" else "SHORT"), "reversão"

    # 2) VETOS DUROS (a lição das 2 vendas stopadas)
    leg_veto = (want == "SHORT" and leg_dir == "UP") or (want == "LONG" and leg_dir == "DOWN")
    flow_veto = (want == "SHORT" and buy >= 4 and buy >= 3 * max(sell, 1)) or \
                (want == "LONG" and sell >= 4 and sell >= 3 * max(buy, 1))

    # 3) GATILHO (momentum na direção do trade)
    confirm = mag >= 6 and ((want == "SHORT" and exc_dir == "BAIXA") or (want == "LONG" and exc_dir == "ALTA"))

    # 4) SUPORTES — RSI com sentido dependente do modo
    inst = bool(z.get("institutional"))
    flow_agree = bool(z.get("nas_agree")) or (z.get("bub_agree") is True)
    def _rsi_sup(r):
        if r is None: return False
        if mode == "continuação":                              # momentum a favor da perna
            return (want == "LONG" and r > 50) or (want == "SHORT" and r < 50)
        return (want == "LONG" and r < 50) or (want == "SHORT" and r > 50)   # reversão = exaustão
    n_rsi = sum(_rsi_sup(r) for r in rsis.values()); rsi_agree = n_rsi >= 2
    if mode == "continuação":
        trend_fit = (adx is not None and adx >= 20) or leg_strong or consumed >= 1
        anchor = leg_strong or consumed >= 1                   # a perna tem convicção (força OU zonas comidas em cadeia)
    else:
        trend_fit = (chop is not None and chop >= 55) or (adx is not None and adx < 20)
        anchor = inst                                          # reversão precisa do íman institucional

    supports = sum([inst, flow_agree, rsi_agree, trend_fit])
    forte = bool(confirm and anchor and supports >= 2 and not leg_veto and not flow_veto)
    q = "FORTE" if forte else "FRACO"

    parts = []
    parts.append(f"perna {leg_dir} {leg.get('net_pts', 0):+.0f}pts{' FORTE' if leg_strong else ''}"
                 + (f" · consumiu {consumed} zona(s)" if consumed else ""))
    if leg_veto: parts.append("🛑 VETO-perna (contra a perna imediata)")
    if flow_veto: parts.append(f"🛑 VETO-fluxo (bubbles BUY{buy}/SELL{sell})")
    parts.append(("🏛️ institucional " + "/".join(z.get("ob_htf") or [])) if inst else "· local")
    if z.get("svp"): parts.append("SVP " + ", ".join(z["svp"]))
    parts.append(f"gatilho {'✓' if confirm else '✗'} {mag:.0f}pts")
    rtxt = "/".join(f"{rsis[t]:.0f}" if rsis[t] is not None else "-" for t in ("5M", "15M", "1H"))
    parts.append(f"RSI(5/15/60) {rtxt} {'✓' if rsi_agree else '·'}{n_rsi}/3")
    if adx is not None: parts.append(f"ADX {adx:.0f}")
    parts.append(f"trend-fit {'✓' if trend_fit else '·'}")
    if z.get("nas_agree"): parts.append("NAS✓")
    if z.get("bub_agree") is True: parts.append("bubbles✓")
    parts.append(f"suportes {supports}/4 · regime {regime}(contexto)")
    return want, mode, q, " · ".join(parts)


def slow_move(bars, want, price, win=8):
    """Movimento acumulado DIRECIONAL na janela (~40min de 5M): LONG=quanto recuperou do fundo, SHORT=quanto caiu
    do topo. DIAGNÓSTICO — NÃO entra na decisão. Serve p/ calibrar com dados reais o gatilho lento (a virada
    gradual que o impulso-de-barra-única não apanha), sem palpite/overfit."""
    seg = bars[-win:] if len(bars) >= win else bars
    lows = [b.get("low") for b in seg if b.get("low") is not None]
    highs = [b.get("high") for b in seg if b.get("high") is not None]
    if want == "LONG" and lows: return round(price - min(lows), 1)
    if want == "SHORT" and highs: return round(max(highs) - price, 1)
    return 0.0


def check_ob_touch(price, bars, now, exc):
    """Alerta quando o preço 5M live ENTRA numa zona OB Detector 15M REAL — direção pelo TIPO (SUPPLY→SHORT,
    DEMAND→LONG), NUNCA por aproximação. Qualidade FRACO/FORTE via cruzamento MTF (classify_zone). SÓ FORTE vai
    ao Telegram; FRACO só loga. Dedup por zona (rearma ao sair >2pts). Alert-only, gated. Devolve os toques."""
    im = mx.cross()                                            # imagem cruzada (zonas tipadas + confluência + fluxo + regime)
    zones = im.get("zones") or []
    if not zones or price is None:
        return []
    try: state = json.loads(OB_TOUCH_F.read_text())
    except Exception: state = {}
    mag = exc[0] if exc else 0.0
    send = os.environ.get("L1_PRODUCTION_AUTHORIZED") == "1"
    fired, changed = [], False
    for z in zones:
        hi, lo = z["high"], z["low"]
        zk = f"{lo:.0f}-{hi:.0f}"
        armed = state.get(zk, {}).get("armed", True)
        if lo <= price <= hi and armed:
            want, mode, q, ck = classify_zone(z, exc, im)
            state[zk] = {"armed": False, "ts": now}; changed = True
            # sharp_pts = impulso que DECIDE; slow_pts = acumulado (diagnóstico p/ calibrar o gatilho lento depois)
            fired.append({"zone": zk, "type": z["type"], "dir": want, "mode": mode, "q": q,
                          "sharp_pts": round(mag, 1), "slow_pts": slow_move(bars, want, price)})
            if q == "FORTE" and send:                          # FRACO nunca vai ao Telegram (só loga)
                arrow = "🟢" if want == "LONG" else "🔻"
                _notify(f"{arrow} <b>{want} FORTE ({mode}) — OB {z['type']} 15M {lo:.1f}-{hi:.1f}</b>\n"
                        f"{ck}\n{iso(now)} Lisboa · timing 5M · advisory — decides + marca #N (journal aprende)")
        elif not (lo <= price <= hi) and not armed and (price < lo - 2 or price > hi + 2):
            state[zk] = {"armed": True}; changed = True   # saiu da zona -> rearma p/ próximo toque
    if changed:
        tmp = OB_TOUCH_F.with_suffix(".json.tmp"); tmp.write_text(json.dumps(state, ensure_ascii=False)); os.replace(tmp, OB_TOUCH_F)
    return fired


def _notify(text):
    try:
        sys.path.insert(0, str(CORE.parent / "strategies/xau_4h_long/continuation/L1_EMA21_CONTINUATION"))
        import telegram_notify as TN
        return TN.send_telegram(text)
    except Exception as e:
        return f"ERR {str(e)[:60]}"


def main():
    now = int(time.time())
    price, atr, bars = read_live()
    out = {"ts": dt.datetime.now(dt.timezone.utc).isoformat()}
    if price is None:
        out["status"] = "NO_PRICE (no-op)"; _log(out); print(json.dumps(out)); return
    # DETEÇÃO POR EXCURSÃO (high/low das barras 5M) — apanha wicks que o close-to-close perde
    mag, direction, ref_c, extreme = detect_excursion(bars)
    ot = check_ob_touch(price, bars, now, (mag, direction, ref_c, extreme))   # toque em ZONA OB 15M REAL (timing 5M)
    if ot: out["ob_touch"] = ot
    is_major = mag >= MAJOR_PTS
    is_shock = mag >= SHOCK_PTS
    out.update({"price": price, "atr5": round(atr, 2), "excursion_pts": round(mag, 1),
                "dir": direction, "shock": is_shock, "major": is_major})
    if is_shock:
        tier = "MAJOR" if is_major else "choque"
        SHOCK_F.write_text(json.dumps({"ts": now, "price": price, "excursion_pts": round(mag, 1),
                                       "move_atr": round(mag / atr, 2) if atr else None, "dir": direction,
                                       "major": is_major}))
        try: al = json.loads(ALERT_F.read_text())
        except Exception: al = {"last_ts": 0, "last_key": None}
        key = f"{direction}:{round(extreme)}"                       # dedup por direção + preço-extremo arredondado
        send = os.environ.get("L1_PRODUCTION_AUTHORIZED") == "1"    # só o wrapper autoriza; runs de teste = DRY
        if now - al.get("last_ts", 0) >= COOLDOWN_S and key != al.get("last_key"):
            arrow = "↑" if direction == "ALTA" else "↓"
            msg = (f"⚡ <b>CHOQUE DE PREÇO XAU — {tier} {direction}</b>\n"
                   f"{arrow}{mag:.1f} pts em ≤5min · preço {price:.2f} (extremo {extreme:.2f})\n"
                   f"{iso(now)} Lisboa · verifica news (guerra/Fed/petróleo) — contexto, não ordem")
            r = _notify(msg) if send else "DRY (sem L1_PRODUCTION_AUTHORIZED)"
            if (not send) or (r is True):               # marca cooldown/dedup SÓ se entregue (ou DRY) -> falha re-tenta
                ALERT_F.write_text(json.dumps({"last_ts": now, "last_key": key, "tg": str(r)}))
            out["telegram"] = str(r)
        out["status"] = f"SHOCK {tier} {direction} {mag:.1f}pts"
    else:
        if SHOCK_F.exists() and now - json.loads(SHOCK_F.read_text()).get("ts", 0) > WINDOW_S:
            SHOCK_F.unlink(missing_ok=True)          # limpa flag antiga
        out["status"] = "OK (sem choque)"
    _log(out); print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()
