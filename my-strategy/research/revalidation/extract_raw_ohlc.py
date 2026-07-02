#!/usr/bin/env python3
"""Extrai série OHLC limpa do RAW replay (raw_replay/XAUUSD) -> caches locais. 4H 2020-2026 + 1H 2024-2026.
Dedup por time via campo ohlcv (snapshots sobrepostos; última ocorrência = barra finalizada). RAW ONLY."""
import json,gzip,os,sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))  # repo root for config import
from config import paths as CP
RAW=CP.raw("raw_replay","XAUUSD")
OUT=Path(os.environ.get("L2_OHLC_OUT_DIR", CP.private("research","revalidation")))  # default byte-identical; override for sandbox test
def extract(files,outname):
    bars={}
    for f in files:
        with gzip.open(f,"rt") as fh:
            for line in fh:
                try: d=json.loads(line)
                except: continue
                for b in d.get("ohlcv",[]):
                    if b.get("close") is None: continue
                    bars[b["time"]]={"t":b["time"],"o":b["open"],"h":b["high"],"l":b["low"],"c":b["close"]}
    ser=[bars[t] for t in sorted(bars)]
    with open(OUT/outname,"w") as fh:
        for b in ser: fh.write(json.dumps(b)+"\n")
    import datetime as dt
    print(f"{outname}: {len(ser)} bars  {dt.datetime.utcfromtimestamp(ser[0]['t']).strftime('%Y-%m-%d')} -> {dt.datetime.utcfromtimestamp(ser[-1]['t']).strftime('%Y-%m-%d')}")
extract([RAW/"4H/XAUUSD_240m_replay_2020-01-01_to_2023-01-01.jsonl.gz",
         RAW/"4H/XAUUSD_240m_replay_2023-01-03_to_2026-05-25.jsonl.gz"],"raw_4h_ohlc.jsonl")
extract([RAW/"1H/XAUUSD_60m_replay_2024-05-25_to_2025-05-25.jsonl.gz",
         RAW/"1H/XAUUSD_60m_replay_2025-05-25_to_2025-11-25.jsonl.gz",
         RAW/"1H/XAUUSD_60m_replay_2025-11-25_to_2026-05-25.jsonl.gz"],"raw_1h_ohlc.jsonl")
