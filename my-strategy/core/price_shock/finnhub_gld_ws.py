#!/usr/bin/env python3
"""FINNHUB GLD WEBSOCKET (Cris 2026-07-18) — 2ª fonte de choque de preço, SUB-SEGUNDO, horas US.
GLD = ETF de ouro (~$368) que segue XAUUSD em %; ticks push (~150ms) via wss://ws.finnhub.io. Deteta
choque na velocidade % (|Δ%| ≥ 0.30% em ≤90s = choque · ≥0.60% = MAJOR) e escreve gld_shock.json (lido
pelo news_gate) + escalada Telegram na hora (GATE L1_PRODUCTION_AUTHORIZED — só wrapper envia). Fora de
horas US GLD não negoceia: o socket fica quieto, o detetor TradingView (24h, 30s) cobre. Reconecta com
backoff; heartbeat p/ o watchdog. Horas Lisboa. Daemon persistente (launchd KeepAlive). py3.9 + websockets."""
import os, sys, json, time, asyncio, datetime as dt
from pathlib import Path
from zoneinfo import ZoneInfo
import websockets
HERE = Path(__file__).resolve().parent
sys.path.insert(0, "/Users/cristrein/tradingview-mcp/external_factors_v2/runtime")
try: from load_env import load_env; load_env()
except Exception: pass
LX = ZoneInfo("Europe/Lisbon")
STATE = HERE / ".shock_state"; STATE.mkdir(exist_ok=True)
GLD_SHOCK = STATE / "gld_shock.json"
HB = STATE / "gld_ws_heartbeat.json"
ALERT = STATE / "gld_alert_state.json"
LOG = STATE / "gld_ws.log"
KEY = os.environ.get("FINNHUB_API_KEY")
# GRELHA CONGELADA
SHOCK_PCT = 0.30        # |Δ%| ≥ 0.30% na janela = choque
MAJOR_PCT = 0.60
WINDOW_S = 90           # janela de velocidade
RETAIN_S = 300
COOLDOWN_S = 600
iso = lambda t: dt.datetime.fromtimestamp(int(t), LX).strftime("%H:%M:%S")


def _log(o):
    try:
        with open(LOG, "a") as fh: fh.write(json.dumps(o, ensure_ascii=False) + "\n")
        # poda
        lines = LOG.read_text().splitlines()
        if len(lines) > 500: LOG.write_text("\n".join(lines[-300:]) + "\n")
    except Exception: pass


def _hb(status, extra=None):
    HB.write_text(json.dumps({"ts": int(time.time()), "status": status, **(extra or {})}))


def _notify(text):
    if os.environ.get("L1_PRODUCTION_AUTHORIZED") != "1":
        return "DRY (sem L1_PRODUCTION_AUTHORIZED)"
    try:
        sys.path.insert(0, str(HERE.parent.parent / "strategies/xau_4h_long/continuation/L1_EMA21_CONTINUATION"))
        import telegram_notify as TN
        return str(TN.send_telegram(text))
    except Exception as e:
        return f"ERR {str(e)[:60]}"


def check_shock(samples, price, now):
    win = [s for s in samples if s["t"] >= now - WINDOW_S]
    if len(win) < 2: return None
    ref = min(win, key=lambda s: s["t"])
    if not ref["p"]: return None
    pct = (price - ref["p"]) / ref["p"] * 100.0
    if abs(pct) < SHOCK_PCT: return None
    return {"pct": round(pct, 3), "dir": "ALTA" if pct > 0 else "BAIXA",
            "major": abs(pct) >= MAJOR_PCT, "window_min": round((now - ref["t"]) / 60, 1), "price": price}


async def run():
    if not KEY:
        _log({"fatal": "FINNHUB_API_KEY ausente"}); _hb("NO_KEY"); return
    url = f"wss://ws.finnhub.io?token={KEY}"
    backoff = 2
    while True:
        try:
            async with websockets.connect(url, ping_interval=20, ping_timeout=20) as ws:
                await ws.send(json.dumps({"type": "subscribe", "symbol": "GLD"}))
                _log({"ts": int(time.time()), "event": "conectado+subscrito GLD"}); _hb("connected"); backoff = 2
                samples = []
                while True:
                    try:
                        raw = await asyncio.wait_for(ws.recv(), timeout=30)
                    except asyncio.TimeoutError:
                        _hb("idle (sem trades — GLD fechado?)"); continue      # heartbeat mesmo parado
                    now = int(time.time())
                    try: msg = json.loads(raw)
                    except Exception: continue
                    if msg.get("type") != "trade": continue
                    for tr in (msg.get("data") or []):
                        price = tr.get("p")
                        if price is None: continue
                        samples = [s for s in samples if s["t"] >= now - RETAIN_S]
                        samples.append({"t": now, "p": price})
                        sh = check_shock(samples, price, now)
                        _hb("live", {"last_price": price})
                        if sh:
                            tier = "MAJOR" if sh["major"] else "choque"
                            GLD_SHOCK.write_text(json.dumps({"ts": now, "source": "finnhub_gld_ws", **sh}))
                            try: al = json.loads(ALERT.read_text())
                            except Exception: al = {"last_ts": 0, "last_key": None}
                            key = f"{sh['dir']}:{round(price,1)}"
                            if now - al.get("last_ts", 0) >= COOLDOWN_S and key != al.get("last_key"):
                                m = (f"⚡ <b>CHOQUE OURO (GLD tick) — {tier} {sh['dir']}</b>\n"
                                     f"{sh['pct']:+.2f}% em {sh['window_min']}min · GLD {price:.2f}\n"
                                     f"{iso(now)} Lisboa · sub-segundo · verifica news — contexto, não ordem")
                                r = _notify(m)
                                ALERT.write_text(json.dumps({"last_ts": now, "last_key": key, "tg": r}))
                                _log({"ts": now, "SHOCK": tier, "dir": sh["dir"], "pct": sh["pct"], "tg": r})
        except Exception as e:
            _log({"ts": int(time.time()), "reconnect": str(e)[:80], "backoff_s": backoff}); _hb("reconnecting")
            await asyncio.sleep(backoff); backoff = min(backoff * 2, 60)


if __name__ == "__main__":
    if "--once-test" in sys.argv:
        # teste offline: injeta samples e valida check_shock (sem WS)
        now = int(time.time())
        s = [{"t": now - 60, "p": 366.0}, {"t": now, "p": 368.2}]
        print("check_shock teste:", check_shock(s, 368.2, now))
    else:
        try: asyncio.run(run())
        except KeyboardInterrupt: pass
