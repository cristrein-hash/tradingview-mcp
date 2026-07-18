#!/usr/bin/env python3
"""FINANCIAL JUICE WEBSOCKET (Cris 2026-07-18) — lane de CONTEXTO/CURADORIA (free = ATRASADO 10min).
NÃO é gatilho nem breaking-flag (o atraso desqualifica-o) — é curadoria editorial de terminal (Bloomberg/
Reuters squawk) para enriquecer o read E2. wss://stream.financialjuice.com/v1/stream (X-API-Key header).
Recebe {type:news|calendar}, filtra por relevância XAU, escreve fj_news.json (shape news_gate, high_impact
SEMPRE False por ser atrasado). Daemon persistente (KeepAlive), reconnect backoff, heartbeat. py3.9+websockets."""
import os, sys, json, time, asyncio, hashlib, datetime as dt
from pathlib import Path
import websockets
H = Path(__file__).resolve().parent.parent; SNAP = H / "snapshots"; SNAP.mkdir(exist_ok=True)
sys.path.insert(0, str(H / "runtime"))
try: from load_env import load_env; load_env()
except Exception: pass
KEY = os.environ.get("FJ_API_KEY")
URL = "wss://stream.financialjuice.com/v1/stream"
OUT = SNAP / "fj_news.json"
HB = SNAP / "fj_ws_heartbeat.json"
LOG = SNAP / "fj_ws.log"
RETAIN_S = 6 * 3600
TOP = ["hormuz", "tanker", "missile", "strike", "killed", "escalat", "ceasefire", "nuclear", "blockade",
       "attack", "opec", "sanction", "war", "rate cut", "rate hike", "fomc", "cpi", "ppi", "nfp", "nonfarm",
       "jobs", "inflation", "powell", "fed chair", "unemployment", "gdp", "pce"]
MED = ["iran", "israel", "oil", "brent", "crude", "gold", "dollar", "fed", "trump", "tariff", "yields", "ecb"]


def _log(o):
    try:
        with open(LOG, "a") as fh: fh.write(json.dumps(o, ensure_ascii=False) + "\n")
        ln = LOG.read_text().splitlines()
        if len(ln) > 500: LOG.write_text("\n".join(ln[-300:]) + "\n")
    except Exception: pass


def _hb(status, extra=None):
    HB.write_text(json.dumps({"ts": int(time.time()), "status": status, **(extra or {})}))


def _text(data):
    if isinstance(data, str): return data
    if isinstance(data, dict):
        return data.get("headline") or data.get("title") or data.get("text") or data.get("message") or json.dumps(data)[:200]
    return str(data)


def _score(t):
    tl = (t or "").lower()
    top = [k for k in TOP if k in tl]; med = [k for k in MED if k in tl]
    return ("high" if top else ("med" if med else "low")), (top + med)


def _items():
    try: return json.loads(OUT.read_text()).get("items", [])
    except Exception: return []


def _write(items):
    now = int(time.time())
    OUT.write_text(json.dumps({
        "_meta": {"built_ts": now, "source": "FinancialJuice stream (free, DELAY 600s)", "delay_s": 600},
        "fetch_ok": True, "fetch_ts": now, "n_relevant": len(items),
        "high_impact_now": False,          # ATRASADO 10min -> NUNCA breaking; só contexto/curadoria
        "urgency": "context", "items": items[:15],
        "gate": {"high_impact_headline": False, "escalate": False, "reason": "FJ contexto (10min atraso)",
                 "session": None, "ff_event_le_min": None}}, indent=1, ensure_ascii=False))


async def run():
    if not KEY:
        _log({"fatal": "FJ_API_KEY ausente"}); _hb("NO_KEY"); return
    backoff = 2
    while True:
        try:
            try:
                ws = await websockets.connect(URL, additional_headers={"X-API-Key": KEY}, open_timeout=15, ping_interval=20)
            except TypeError:
                ws = await websockets.connect(URL, extra_headers={"X-API-Key": KEY}, open_timeout=15, ping_interval=20)
            _log({"ts": int(time.time()), "event": "conectado FJ"}); _hb("connected"); backoff = 2
            items = _items()
            async with ws:
                while True:
                    try:
                        raw = await asyncio.wait_for(ws.recv(), timeout=60)
                    except asyncio.TimeoutError:
                        _hb("idle"); continue
                    now = int(time.time())
                    try: msg = json.loads(raw)
                    except Exception: continue
                    typ = msg.get("type")
                    if typ == "hello":
                        _hb("connected", {"delay_s": msg.get("delay_seconds")}); continue
                    if typ not in ("news", "calendar"):
                        _hb("live"); continue
                    txt = _text(msg.get("data"))
                    urg, kws = _score(txt)
                    _hb("live", {"last_type": typ})
                    if urg == "low":
                        continue
                    it = {"id": hashlib.md5(txt.encode()).hexdigest()[:12], "title": txt[:200],
                          "keywords": kws, "urgency": urg, "type": typ, "recv_ts": now,
                          "age_min": 10}      # atraso fixo do feed free
                    items = [x for x in items if x.get("recv_ts", 0) >= now - RETAIN_S]
                    if it["id"] not in {x["id"] for x in items}:
                        items.insert(0, it); _write(items)
                        _log({"ts": now, typ: txt[:80], "urg": urg})
        except Exception as e:
            _log({"ts": int(time.time()), "reconnect": str(e)[:80]}); _hb("reconnecting")
            await asyncio.sleep(backoff); backoff = min(backoff * 2, 60)


if __name__ == "__main__":
    try: asyncio.run(run())
    except KeyboardInterrupt: pass
