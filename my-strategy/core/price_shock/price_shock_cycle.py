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


def _short_context(mag, exc_dir):
    """Monitor de contexto SHORT (Cris 2026-07-21): lê o dossiê E0 (market_context.json, zero MCP) e compõe o
    checklist dos 6 fatores + qualidade. ADVISORY — a qualidade REALÇA (FORTE/MÉDIO/FRACO), NUNCA veta (o Cris
    é o árbitro). Encoda os 2 exemplos: 4040=FORTE (perna madura+íman+rejeição), sexta=FRACO (perna imatura).
    Devolve (linha_checklist, qualidade) ou (None, None) se o E0 não estiver disponível."""
    try:
        ax = json.loads(E0_F.read_text()).get("axes") or {}
    except Exception:
        return None, None
    reg = ax.get("regime") or {}
    r5 = (reg.get("v5_4h") or {}).get("regime"); r1 = (reg.get("structural_1d") or {}).get("regime")
    regime_ok = r5 in ("BEAR", "RANGE")
    mtf = ax.get("mtf") or {}
    def _num(x):
        try: return float(str(x).replace(",", ""))
        except Exception: return None
    def _pos(tf):
        m = mtf.get(tf) or {}; return m.get("trend"), _num((m.get("leg") or {}).get("pos_in_leg"))
    t15, p15 = _pos("15"); t60, p60 = _pos("60")
    pos = p15 if (t15 == "UP" and p15 is not None) else (p60 if p60 is not None else 0.0)
    mature = (pos or 0) >= 0.5                                  # perna de alta madura/esticada (>=0.5) vs 1ª pullback
    rejection = mag >= 6 and exc_dir == "BAIXA"                 # rejeição da subida (excursão p/ baixo)
    mi = ax.get("micro_15m") or {}
    rsi = _num(mi.get("rsi")); rma = _num(mi.get("rsi_ma"))
    stretch = bool(rsi is not None and rma is not None and rsi > 55 and rsi > rma)   # esticado (RSI alto e > MA)
    cf = (ax.get("confluence") or {}).get("15") or {}
    sell_init = (_num(cf.get("sell")) or 0) > (_num(cf.get("buy")) or 0)   # iniciativa vendedora na perna
    fav = sum([regime_ok, mature, rejection, stretch, sell_init])
    q = "FORTE" if (mature and rejection and fav >= 4) else ("FRACO" if (not mature or not rejection) else "MÉDIO")
    ck = (f"regime {r5}/{r1} {'✓' if regime_ok else '·'} · perna {'madura ✓' if mature else 'imatura ✗'} "
          f"(pos {pos:.2f}) · rejeição {'✓' if rejection else '·'} {mag:.0f}pts · "
          f"RSI {(rsi or 0):.0f} {'esticado ✓' if stretch else '·'} · "
          f"iniciativa {'SELL ✓' if sell_init else 'buy/neutra ·'}")
    return ck, q


def check_ob_touch(price, bars, now, exc):
    """Alerta quando o preço 5M live ENTRA numa zona do OB Detector 15M REAL. A subir para a zona = teste de
    RESISTÊNCIA (contexto short); a descer = SUPORTE (contexto long). Dedup por zona (rearma ao sair >2pts).
    Realça a rejeição (excursão contra a aproximação). Alert-only, gated. Timing 5M, zona 15M. Devolve labels."""
    zones = _read_ob15_zones()
    if not zones or price is None:
        return []
    try: state = json.loads(OB_TOUCH_F.read_text())
    except Exception: state = {}
    prev = bars[-4].get("close") if bars and len(bars) >= 4 else price   # aproximação: preço vs ~3 barras 5M atrás
    rising = price > (prev or price)
    mag, exc_dir, _, _ = exc
    send = os.environ.get("L1_PRODUCTION_AUTHORIZED") == "1"
    fired, changed = [], False
    for hi, lo in zones:
        zk = f"{lo:.0f}-{hi:.0f}"
        armed = state.get(zk, {}).get("armed", True)
        if lo <= price <= hi and armed:
            state[zk] = {"armed": False, "ts": now}; changed = True; fired.append(zk)
            if send:
                if rising:                                       # RESISTÊNCIA = MONITOR DE CONTEXTO SHORT (E0)
                    ck, q = _short_context(mag, exc_dir)
                    body = (f"{ck}\nqualidade: {q}") if ck else f"rejeição {mag:.0f}pts {exc_dir}"
                    _notify(f"🔻 <b>SHORT-context a formar — zona OB 15M {lo:.1f}-{hi:.1f}</b> (íman testado ✓)\n"
                            f"{body}\n{iso(now)} Lisboa · timing 5M · advisory — decides + marca #N short (journal aprende)")
                else:                                            # SUPORTE = contexto long (só aviso simples)
                    _notify(f"🎯 <b>XAU tocou ZONA OB 15M — SUPORTE (contexto LONG)</b>\n"
                            f"zona {lo:.1f}-{hi:.1f} · preço {price:.2f} ↓ a descer para\n"
                            f"{iso(now)} Lisboa · OB Detector real · timing 5M — contexto, não ordem")
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
