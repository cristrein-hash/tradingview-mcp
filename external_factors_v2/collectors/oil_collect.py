#!/usr/bin/env python3
"""COLETOR PETRÓLEO (Cris 2026-07-18) — canal de transmissão nº1 para o ouro no regime geopolítico atual:
oil↑ → inflação↑ → Fed hawkish → ouro↓ (e choque agudo → refúgio → ouro↑). Brent (FMP /stable/quote
BZUSD, funciona no FMP free; WTI CLUSD é premium — Brent é o benchmark internacional que move a inflação).
SHOCK flag: |change_pct| ≥ 3% = movimento relevante para o ouro. Determinístico, py3.9, degradação graciosa.
Saída: snapshots/oil_data.json (lido pelo news_gate p/ high_impact + pelo consolidador latest.json)."""
import json, os, sys, subprocess, datetime as dt
from pathlib import Path
H = Path(__file__).resolve().parent.parent; SNAP = H / "snapshots"; SNAP.mkdir(exist_ok=True)
sys.path.insert(0, str(H / "runtime"))
try: from load_env import load_env; load_env()
except Exception: pass
NOWT = int(dt.datetime.now(dt.timezone.utc).timestamp())
FMP = os.environ.get("FMP_API_KEY")
SHOCK_PCT = 3.0
OUT = SNAP / "oil_data.json"


def curl(url):
    return subprocess.run(["curl", "-sS", "--http1.1", "--max-time", "40", url], capture_output=True, text=True).stdout


def quote(sym):
    if not FMP:
        return {"error": "FMP_API_KEY ausente"}
    raw = curl(f"https://financialmodelingprep.com/stable/quote?symbol={sym}&apikey={FMP}")
    try:
        d = json.loads(raw)
        if isinstance(d, list) and d:
            q = d[0]
            return {"symbol": sym, "name": q.get("name"), "price_usd": q.get("price"),
                    "change": q.get("change"), "change_pct": q.get("changePercentage"),
                    "day_low": q.get("dayLow"), "day_high": q.get("dayHigh"),
                    "year_high": q.get("yearHigh"), "year_low": q.get("yearLow")}
        return {"error": f"FMP inesperado: {str(d)[:100]}"}
    except Exception:
        return {"error": f"FMP não-JSON: {raw[:100]}"}


def main():
    brent = quote("BZUSD")
    pct = brent.get("change_pct")
    shock = pct is not None and abs(pct) >= SHOCK_PCT
    out = {"_meta": {"built_ts": NOWT, "source": "FMP /stable BZUSD (Brent, key grátis)",
                     "purpose": "canal petróleo->inflação->ouro; SHOCK≥3%"},
           "fetch_ok": "error" not in brent, "fetch_ts": NOWT,
           "brent": brent,
           "shock": bool(shock),
           "shock_dir": (None if not shock else ("up" if pct > 0 else "down")),
           "read": (None if pct is None else
                    (f"Brent {brent.get('price_usd')} ({pct:+.1f}%) — SHOCK {'ALTA' if pct>0 else 'BAIXA'}: "
                     f"{'inflação↑→Fed hawkish→pressão baixista no ouro (ou refúgio se choque agudo)' if pct>0 else 'alívio inflação→suporte ouro'}"
                     if shock else f"Brent {brent.get('price_usd')} ({pct:+.1f}%) — sem choque"))}
    tmp = OUT.with_suffix(".json.tmp"); tmp.write_text(json.dumps(out, indent=1, ensure_ascii=False)); os.replace(tmp, OUT)
    print(f"oil_collect: Brent {brent.get('price_usd')} ({pct}%) shock={shock}")


if __name__ == "__main__":
    main()
