#!/usr/bin/env python3
"""NULL de Cp (Cris 2026-07-15) — teste decisivo antes de desenhar. Na bear de 2026, enumera TODAS as
velas de capitulacao (range >= 1.8x ATR = o min do Cp GT, E down-candle C<O) e aplica o reclaim MB3
causal + 3R. Se o hit-3R do null ~ igual aos 5 GT (4/5), entao a selecao do Cris (que capitulacao
SEGURA) nao e mecanizavel pelos reads = survivorship. Se null << GT, a selecao e skill (nao nos reads).
Marca onde caem os 5 GT. RAW 15M. causal_entry auditado sem lookahead."""
import json, bisect, datetime as dt
from pathlib import Path
import sys; HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE))
import macro_structural_v3 as MM
from a1_causal_entry import load_series, causal_entry
ds = lambda t: dt.datetime.utcfromtimestamp(int(t)).strftime("%Y-%m-%d %H:%M")
BLK = ["XAUUSD_15m_replay_2025-11-25_to_2026-02-25.jsonl.gz",
       "XAUUSD_15m_replay_2026-02-25_to_2026-05-25_rerun_customOBbaseline.jsonl.gz",
       "XAUUSD_15m_replay_2026-05-25_to_2026-07-04.jsonl.gz"]
S = load_series(BLK); T, O, H, L, C, ATR, N = S["T"], S["O"], S["H"], S["L"], S["C"], S["ATR"], S["N"]
reg = MM.build_layer1(); KN1 = [x+86400 for x in MM.T]
macro_at = lambda t0: reg[bisect.bisect_right(KN1, t0)-1] if bisect.bisect_right(KN1, t0)-1 >= 0 else None
t_lo = int(dt.datetime(2026, 2, 1, tzinfo=dt.timezone.utc).timestamp())
t_hi = int(dt.datetime(2026, 7, 4, tzinfo=dt.timezone.utc).timestamp())
CAP_MIN = 1.8   # min capRange do Cp GT

# enumera velas de capitulacao (flush) e aplica MB3 reclaim
seen = set(); rows = []
for k in range(30, N):
    if not (t_lo <= T[k] <= t_hi): continue
    atr = ATR[k] or 5.0
    if (H[k]-L[k]) < CAP_MIN*atr: continue          # vela grande (range expansion)
    if C[k] >= O[k]: continue                        # down-flush
    e = causal_entry(S, k, "MB3")
    if not e or e["ei"] in seen: continue
    seen.add(e["ei"])
    rows.append({"t": T[k], "ei": e["ei"], "o": e["o"], "macro": macro_at(T[k]), "RATR": e["RATR"]})

def hit(sub):
    v = [r for r in sub if r["o"] in ("WIN", "LOSS")]; w = sum(1 for r in v if r["o"] == "WIN")
    return w, len(v), (100*w/len(v) if v else 0)

allw, alln, allhr = hit(rows)
bear = [r for r in rows if r["macro"] == "BEAR"]; bw, bn, bhr = hit(bear)
op = sum(1 for r in rows if r["o"] == "OPEN")
print(f"NULL Cp — velas capitulacao (range>=1.8x, down) na bear 2026: N={len(rows)} (OPEN {op})")
print(f"  TODAS:      hit-3R {allhr:.0f}% ({allw}/{alln})")
print(f"  so macro BEAR: hit-3R {bhr:.0f}% ({bw}/{bn})  N={len(bear)}")
print(f"\n  Cp GT (selecao do Cris): 4/5 WIN (~80%, 1 OPEN)")
print(f"  => se GT(80%) >> null({allhr:.0f}%), a selecao do Cris E skill (nao mecanizavel pelos reads = precisa do olho/forward).")
print(f"     se GT ~ null, e survivorship (o reclaim-MB3 funciona em qualquer flush).")
# distribuicao por RATR (os winners sao tight-R?)
import statistics
wr = [r["RATR"] for r in rows if r["o"] == "WIN"]; lr = [r["RATR"] for r in rows if r["o"] == "LOSS"]
print(f"\n  RATR med: WIN {statistics.median(wr) if wr else '-'} vs LOSS {statistics.median(lr) if lr else '-'}")