#!/usr/bin/env python3
"""Extrai OHLC 30M do RAW replay (HD) -> raw_30m_ohlc.jsonl. MESMO método canônico do extract_raw_ohlc.py:
dedup por time via campo ohlcv (última ocorrência = barra finalizada). RAW ONLY. Determinístico."""
import json,gzip,datetime as dt,os,sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # repo root for config import
from config import paths as CP
RAW=CP.raw("raw_replay","XAUUSD","30M")
OUT=Path(os.environ.get("RTSE_30M_OUT_DIR", Path(__file__).parent))  # default byte-identical; override for sandbox test
files=["XAUUSD_30m_replay_2024-05-25_to_2024-11-25.jsonl.gz","XAUUSD_30m_replay_2024-11-25_to_2025-05-25.jsonl.gz",
       "XAUUSD_30m_replay_2025-05-25_to_2025-11-25.jsonl.gz","XAUUSD_30m_replay_2025-11-25_to_2026-05-25.jsonl.gz"]
bars={}
for f in files:
    with gzip.open(RAW/f,"rt") as fh:
        for line in fh:
            try: d=json.loads(line)
            except: continue
            for b in d.get("ohlcv",[]):
                if b.get("close") is None: continue
                bars[b["time"]]={"t":b["time"],"o":b["open"],"h":b["high"],"l":b["low"],"c":b["close"]}
ser=[bars[t] for t in sorted(bars)]
with open(OUT/"raw_30m_ohlc.jsonl","w") as fh:
    for b in ser: fh.write(json.dumps(b)+"\n")
print(f"raw_30m_ohlc.jsonl: {len(ser)} bars {dt.datetime.utcfromtimestamp(ser[0]['t']).strftime('%Y-%m-%d')} -> {dt.datetime.utcfromtimestamp(ser[-1]['t']).strftime('%Y-%m-%d')}")
