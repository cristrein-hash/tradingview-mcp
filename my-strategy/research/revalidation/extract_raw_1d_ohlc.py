#!/usr/bin/env python3
"""Extrai OHLC 1D NATIVO do RAW replay do HD externo (GUTS LACIE) -> raw_1d_ohlc.jsonl.
Mesma maquinaria do extract_raw_ohlc.py (dedup por time via campo ohlcv; última ocorrência =
barra finalizada). RAW ONLY. Cobertura nativa: 2012-06-19 → 2026-05-25 (declarado: features 1D
congelam em 2026-05-25; depois disso fallback = resample do RAW 4H, marcado)."""
import json, gzip
from pathlib import Path
SRC = Path("/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/1D/XAUUSD_1D_replay_2012-06-19_to_2026-05-25.jsonl.gz")
OUT = Path(__file__).resolve().parent/"raw_1d_ohlc.jsonl"

def main():
    bars = {}
    with gzip.open(SRC, "rt", errors="replace") as fh:
        for line in fh:
            try: d = json.loads(line)
            except Exception: continue
            for b in d.get("ohlcv", []):
                if b.get("close") is None: continue
                bars[b["time"]] = {"t": b["time"], "o": b["open"], "h": b["high"],
                                   "l": b["low"], "c": b["close"]}
    ser = [bars[t] for t in sorted(bars)]
    with open(OUT, "w") as fh:
        for r in ser: fh.write(json.dumps(r)+"\n")
    import datetime as dt
    f = "%Y-%m-%d"
    print(f"raw_1d_ohlc.jsonl: {len(ser)} barras "
          f"{dt.datetime.utcfromtimestamp(ser[0]['t']).strftime(f)}→"
          f"{dt.datetime.utcfromtimestamp(ser[-1]['t']).strftime(f)}")

if __name__ == "__main__":
    main()
