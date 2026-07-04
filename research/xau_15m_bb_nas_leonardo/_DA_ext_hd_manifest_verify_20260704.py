#!/usr/bin/env python3
"""DA independente — 9º bloco no HD externo: manifest existe, sha256 do gz no HD bate (recompute),
roundtrip gunzip|sha256 == original_sha256 do manifest == sha256 do original local (normalized.jsonl)."""
import gzip, hashlib, re
from pathlib import Path
HD = Path("/Volumes/GUTS_ LACIE/TradingData")
MAN = HD / "manifests" / "XAUUSD_15m_replay_2026-05-25_to_2026-07-04_manifest.txt"
LOCAL = Path("/Users/cristrein/tradingview-mcp/alert-bridge/logs/backtests/XAUUSD_15m_replay_2026-05-25_to_2026-07-04.normalized.jsonl")

txt = MAN.read_text()
print("manifest:", MAN)
print(txt)
sha_gz_man = re.search(r"gz_sha256\s*[:=]\s*([0-9a-f]{64})", txt) or re.search(r"([0-9a-f]{64}).*\.gz", txt)
sha_orig_man = re.search(r"original_sha256\s*[:=]\s*([0-9a-f]{64})", txt)
gz_candidates = list(HD.rglob("XAUUSD_15m_replay_2026-05-25_to_2026-07-04*.gz"))
print("gz no HD:", gz_candidates)
gz = gz_candidates[0]

def sha(fh, chunk=1 << 20):
    h = hashlib.sha256()
    while True:
        b = fh.read(chunk)
        if not b: break
        h.update(b)
    return h.hexdigest()

with open(gz, "rb") as f: sha_gz = sha(f)
with gzip.open(gz, "rb") as f: sha_round = sha(f)
with open(LOCAL, "rb") as f: sha_local = sha(f)
print("sha256 gz (recompute):     ", sha_gz)
print("sha256 gunzip (roundtrip): ", sha_round)
print("sha256 original local:     ", sha_local)
if sha_gz_man: print("gz bate manifest:", sha_gz == sha_gz_man.group(1))
if sha_orig_man: print("roundtrip bate original_sha256 manifest:", sha_round == sha_orig_man.group(1))
print("roundtrip bate original local:", sha_round == sha_local)
