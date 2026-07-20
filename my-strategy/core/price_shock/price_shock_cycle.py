#!/usr/bin/env python3
"""DETETOR DE CHOQUE DE PREÇO (Cris 2026-07-18; 5M exato 2026-07-20) — o gatilho realtime MAIS RÁPIDO,
independente de qualquer news feed: o mercado precifica a notícia ANTES dos feeds a reportarem. Loop dedicado
30s: lê o preço live do 5M (forming bar, tab-pinned, leve) e mede velocidade vs ATR5 — escala COERENTE com a
janela de 5min (movimento de 5min contra o range típico de 5min = shocking exato; antes usava ATR15, grosso).
Choque = |Δpreço em ≤5min| ≥ 1.2·ATR5 (major ≥ 2.5). Na hora: escreve snapshot (lido pelo news_gate → E0/E2)
+ escalada Telegram imediata (dedup+cooldown). Fail-closed, horas Lisboa, py3.9. Grelha CONGELADA
(thresholds 1.2/2.5 + cooldown 600s inalterados). CLI: --once (default 1 ciclo)."""
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
SAMPLES = STATE / "samples.jsonl"
SHOCK_F = STATE / "shock.json"          # lido pelo news_gate (price_shock_now)
ALERT_F = STATE / "alert_state.json"
ZONE_F = STATE / "zone_watch.json"      # zonas de preço vigiadas (alerta ao TOCAR) — pedido do Cris
LOG = STATE / "shock_cycle.log"
# GRELHA CONGELADA
SHOCK_ATR = 1.2         # choque = movimento ≥ 1.2·ATR15 na janela
MAJOR_ATR = 2.5         # choque MAJOR
WINDOW_S = 300          # janela de velocidade = 5 min
RETAIN_S = 900          # mantém 15 min de amostras
COOLDOWN_S = 600        # ≥10 min entre alertas Telegram
iso = lambda t: dt.datetime.fromtimestamp(int(t), LX).strftime("%H:%M:%S")


def _log(o):
    with open(LOG, "a") as fh: fh.write(json.dumps(o, ensure_ascii=False) + "\n")


def _samples():
    try: return [json.loads(x) for x in SAMPLES.read_text().splitlines() if x.strip()]
    except Exception: return []


def read_live():
    """Preço live do 5M (forming bar) + ATR5, tab-pinned, leve (count 30). None em falha.
    5M (não 15M) = escala coerente com a janela de 5min do detetor: shocking mais exato/sensível."""
    tid = tab_pin.discover_tab("5")
    if not tid: return None, None
    os.environ["TVMCP_TARGET_CHART_ID"] = tid
    c = MCPClient(); c.start()
    try:
        oh = c.call_tool("data_get_ohlcv", {"count": 30}) or {}
        bars = oh.get("bars") or oh.get("ohlcv") or []
    finally:
        c.stop()
    if len(bars) < 16: return None, None
    H = [b.get("high") for b in bars]; L = [b.get("low") for b in bars]; C = [b.get("close") for b in bars]
    if any(x is None for x in H + L + C): return None, None
    atr = cs.atr(H, L, C, len(C) - 1, 14)               # ATR5 (barras agora são 5M)
    return C[-1], (atr or 2.0)                           # C[-1] = forming bar close = preço agora


def check_zones(price, now):
    """Zonas de preço vigiadas (zone_watch.json): alerta Telegram UMA vez quando o preço ENTRA na banda
    [lo,hi]; re-arma quando sai >2pts fora (permite avisar um retest genuíno mais tarde). Alert-only,
    gated pelo mesmo L1_PRODUCTION_AUTHORIZED. Nunca negoceia. Devolve lista de labels disparados."""
    try:
        zones = json.loads(ZONE_F.read_text())
    except Exception:
        return []
    send = os.environ.get("L1_PRODUCTION_AUTHORIZED") == "1"
    fired, changed = [], False
    for z in zones:
        lo, hi = z.get("lo"), z.get("hi")
        if lo is None or hi is None:
            continue
        inside = lo <= price <= hi
        if inside and z.get("armed", True):
            z["armed"] = False; z["fired_ts"] = now; changed = True; fired.append(z.get("label") or f"{lo}-{hi}")
            if send:
                msg = (f"🎯 <b>XAU TOCOU A ZONA — {z.get('label') or f'{lo}-{hi}'}</b>\n"
                       f"preço {price:.2f} dentro de {lo:.0f}-{hi:.0f} · {iso(now)} Lisboa\n"
                       f"{z.get('note') or 'a tua zona de entrada — vê a reação (rejeição vs rompimento)'}")
                z["tg"] = str(_notify(msg))
        elif not inside and not z.get("armed", True) and (price < lo - 2 or price > hi + 2):
            z["armed"] = True; changed = True                # saiu da banda: re-arma p/ próximo retest
    if changed:
        tmp = ZONE_F.with_suffix(".json.tmp"); tmp.write_text(json.dumps(zones, ensure_ascii=False)); os.replace(tmp, ZONE_F)
    return fired


BB15M_F = STATE / "bb15m_watch.json"      # BB 15M dinâmico (computado dos closes) — alerta ao TOCAR a banda


def check_bb15m(price, now):
    """BB de 15M DINÂMICO (não há indicador no chart → computo de bars_15m.jsonl). Bandas = SMA(len) ±
    mult·stdev(len) sobre os últimos closes 15M COM a barra viva (=preço) na cauda, p/ bater com o que o Cris
    vê live. Alerta Telegram UMA vez ao TOCAR (>=upper / <=lower); re-arma ao voltar >3pts p/ dentro. Settings
    default 20/2.0 ambas as bandas (editáveis em bb15m_watch.json). Alert-only, gated L1_PRODUCTION_AUTHORIZED."""
    try:
        cfg = json.loads(BB15M_F.read_text())
    except Exception:
        cfg = {"len": 20, "mult": 2.0, "bands": "both", "armed_up": True, "armed_dn": True, "fired_ts": 0}
    L = int(cfg.get("len", 20)); M = float(cfg.get("mult", 2.0)); bands = cfg.get("bands", "both")
    S15 = CORE / "bar_store/store/bars_15m.jsonl"
    try:
        closes = [json.loads(x)["c"] for x in S15.read_text().splitlines() if x.strip()]
    except Exception:
        return []
    if len(closes) < L:
        return []
    win = closes[-(L - 1):] + [price]                    # inclui a barra viva na cauda (= BB live do chart)
    mean = sum(win) / L
    sd = (sum((x - mean) ** 2 for x in win) / L) ** 0.5  # population stdev (convenção TradingView)
    upper, lower = mean + M * sd, mean - M * sd
    send = os.environ.get("L1_PRODUCTION_AUTHORIZED") == "1"
    fired, changed = [], False
    hit_up = bands in ("both", "upper") and price >= upper and cfg.get("armed_up", True)
    hit_dn = bands in ("both", "lower") and price <= lower and cfg.get("armed_dn", True)
    if hit_up:
        cfg["armed_up"] = False; cfg["fired_ts"] = now; changed = True; fired.append("BB15M_SUP")
        if send:
            _notify(f"📐 <b>XAU TOCOU O BB 15M SUPERIOR</b> ({L}/{M:g}σ)\n"
                    f"preço {price:.2f} ≥ banda {upper:.2f} · basis {mean:.2f} · {iso(now)} Lisboa\n"
                    "íman de venda — vê rejeição vs rompimento (contexto SHORT, não é sinal)")
    if hit_dn:
        cfg["armed_dn"] = False; cfg["fired_ts"] = now; changed = True; fired.append("BB15M_INF")
        if send:
            _notify(f"📐 <b>XAU TOCOU O BB 15M INFERIOR</b> ({L}/{M:g}σ)\n"
                    f"preço {price:.2f} ≤ banda {lower:.2f} · basis {mean:.2f} · {iso(now)} Lisboa\n"
                    "íman de compra/oversold — vê reação (contexto LONG, não é sinal)")
    if not cfg.get("armed_up", True) and price < upper - 3:
        cfg["armed_up"] = True; changed = True     # voltou p/ dentro: re-arma superior
    if not cfg.get("armed_dn", True) and price > lower + 3:
        cfg["armed_dn"] = True; changed = True     # re-arma inferior
    if changed:
        tmp = BB15M_F.with_suffix(".json.tmp"); tmp.write_text(json.dumps(cfg, ensure_ascii=False)); os.replace(tmp, BB15M_F)
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
    price, atr = read_live()
    out = {"ts": dt.datetime.now(dt.timezone.utc).isoformat()}
    if price is None:
        out["status"] = "NO_PRICE (no-op)"; _log(out); print(json.dumps(out)); return
    zt = check_zones(price, now)                          # zonas vigiadas (alerta ao tocar) — independente do choque
    if zt: out["zone_touch"] = zt
    bt = check_bb15m(price, now)                           # BB 15M dinâmico (alerta ao tocar banda)
    if bt: out["bb15m_touch"] = bt
    # amostras (retenção 15min)
    sm = [s for s in _samples() if s["t"] >= now - RETAIN_S]
    sm.append({"t": now, "p": price})
    SAMPLES.write_text("\n".join(json.dumps(s) for s in sm) + "\n")
    # velocidade: preço agora vs amostra mais antiga dentro da janela
    win = [s for s in sm if s["t"] >= now - WINDOW_S]
    ref = min(win, key=lambda s: s["t"]) if len(win) >= 2 else None
    out.update({"price": price, "atr5": round(atr, 2), "n_samples": len(sm)})
    if ref is None:
        out["status"] = "SEED (a acumular janela)"; _log(out); print(json.dumps(out)); return
    move = price - ref["p"]; move_atr = round(abs(move) / atr, 2); dtmin = round((now - ref["t"]) / 60, 1)
    out.update({"move": round(move, 2), "move_atr": move_atr, "window_min": dtmin,
                "shock": move_atr >= SHOCK_ATR, "major": move_atr >= MAJOR_ATR})
    if move_atr >= SHOCK_ATR:
        direction = "ALTA" if move > 0 else "BAIXA"
        tier = "MAJOR" if move_atr >= MAJOR_ATR else "choque"
        SHOCK_F.write_text(json.dumps({"ts": now, "price": price, "move_atr": move_atr, "dir": direction,
                                       "window_min": dtmin, "major": move_atr >= MAJOR_ATR}))
        # escalada Telegram (dedup por direção+preço arredondado, cooldown)
        try: al = json.loads(ALERT_F.read_text())
        except Exception: al = {"last_ts": 0, "last_key": None}
        key = f"{direction}:{round(price)}"
        send = os.environ.get("L1_PRODUCTION_AUTHORIZED") == "1"   # só o wrapper autoriza; runs de teste = DRY
        if now - al.get("last_ts", 0) >= COOLDOWN_S and key != al.get("last_key"):
            msg = (f"⚡ <b>CHOQUE DE PREÇO XAU — {tier} {direction}</b>\n"
                   f"{move:+.2f} ({move_atr:.1f}×ATR5) em {dtmin}min · preço {price:.2f}\n"
                   f"{iso(now)} Lisboa · verifica news (guerra/Fed/petróleo) — contexto, não ordem")
            r = _notify(msg) if send else "DRY (sem L1_PRODUCTION_AUTHORIZED)"
            ALERT_F.write_text(json.dumps({"last_ts": now, "last_key": key, "tg": str(r)}))
            out["telegram"] = str(r)
        out["status"] = f"SHOCK {tier} {direction} {move_atr}xATR"
    else:
        if SHOCK_F.exists() and now - json.loads(SHOCK_F.read_text()).get("ts", 0) > WINDOW_S:
            SHOCK_F.unlink(missing_ok=True)          # limpa flag antiga
        out["status"] = "OK (sem choque)"
    _log(out); print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()
