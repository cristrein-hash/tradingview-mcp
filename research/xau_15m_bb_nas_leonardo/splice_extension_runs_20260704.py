#!/usr/bin/env python3
"""Extensão 2026-07-04 — SPLICE run-2 (payload completo, 17 buracos de 1 barra) + run-1 (série limpa,
sem SMC/NAS). Regra: run-2 é a base; barras ausentes na run-2 e presentes na run-1 entram VERBATIM da
run-1 (documentadas). Conservador-causal: SMC/NAS de eventos nascidos nessas barras aparecem 1 barra
depois (known_at +15min, nunca antecipado). Verificações: (a) OHLC idêntico entre runs numa amostra de
barras comuns (determinismo do replay); (b) merged sem buracos de 1 barra; (c) monotonia/dup zero.
Saída: XAUUSD_15m_replay_2026-05-25_to_2026-07-04.merged.jsonl + atualização do validation JSON."""
import json, hashlib, datetime as dt
from pathlib import Path

BT = Path("/Users/cristrein/tradingview-mcp/alert-bridge/logs/backtests")
R2 = BT / "XAUUSD_15m_replay_2026-05-25_to_2026-07-04.normalized.jsonl"
R1 = BT / "forensics_20260704_run1" / "XAUUSD_15m_replay_2026-05-25_to_2026-07-04.normalized.jsonl"
OUT = BT / "XAUUSD_15m_replay_2026-05-25_to_2026-07-04.merged.jsonl"
HERE = Path(__file__).parent

def load(p):
    recs = {}
    for l in open(p, "rb"):
        r = json.loads(l)
        t = r["ohlcv"][-1]["time"]
        if t not in recs: recs[t] = (r, l)
    return recs

r2, r1 = load(R2), load(R1)
print(f"run-2: {len(r2)} barras · run-1: {len(r1)} barras")

# (a) determinismo: OHLC idêntico nas barras comuns (amostra completa)
common = sorted(set(r2) & set(r1))
mism = 0
for t in common:
    a, b = r2[t][0]["ohlcv"][-1], r1[t][0]["ohlcv"][-1]
    if any(abs(a[k] - b[k]) > 1e-9 for k in ("open", "high", "low", "close")): mism += 1
print(f"(a) OHLC run-2 vs run-1 em {len(common)} barras comuns: {mism} mismatches")
assert mism == 0, "replay não-determinístico entre runs — PARAR"

# splice
only1 = sorted(set(r1) - set(r2))
print(f"(b) barras só na run-1 (entram no splice): {len(only1)}")
for t in only1: print("   +", dt.datetime.utcfromtimestamp(t).isoformat())
merged = sorted(set(r2) | set(r1))
sha = hashlib.sha256()
with open(OUT, "wb") as fo:
    for t in merged:
        raw = (r2.get(t) or r1.get(t))[1]
        fo.write(raw); sha.update(raw)

# (c) revalidação série
holes = []
for i in range(1, len(merged)):
    d = merged[i] - merged[i - 1]
    if d == 1800:
        a = dt.datetime.utcfromtimestamp(merged[i - 1])
        if a.weekday() < 5 and a.hour not in (20, 21, 22): holes.append(a.isoformat())
print(f"(c) merged: {len(merged)} barras · buracos de 1 barra restantes: {len(holes)} {holes}")
print(f"merged sha256: {sha.hexdigest()}")
info = {"merged_file": str(OUT), "merged_sha256": sha.hexdigest(), "bars": len(merged),
        "from_run2": len(r2), "spliced_from_run1": len(only1),
        "spliced_timestamps": [dt.datetime.utcfromtimestamp(t).isoformat() for t in only1],
        "ohlc_mismatches_common": mism, "holes_remaining": holes,
        "caveat": "SMC/NAS de eventos nascidos nas barras spliced aparecem 1 barra depois (known_at +15min, conservador-causal)"}
json.dump(info, open(HERE / "results" / "raw_15m_extension_splice_20260704.json", "w"), indent=1)
print("OK → results/raw_15m_extension_splice_20260704.json")
