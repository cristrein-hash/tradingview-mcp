#!/usr/bin/env python3
"""
_reopt5_explore.py — RAW-causal feature exploration for 5ATR dataset.
Base: candidatos 5ATR-confirm, SEM dedup. n=3047, WR base=60.5%, avgR +0.30.
win = R>0. PROIBIDO usar R/win/cj/low_idx como feature.
Lente: MULTI-TF (h1/h4/hd trend/dist/pos/eff) -> re-derivar eixo R2 p/ 5ATR.
"""
import json
from collections import Counter

ROWS = [json.loads(l) for l in open('dataset_5atr.jsonl')]
N = len(ROWS)
BASE_WR = sum(r['win'] for r in ROWS) / N
YEARS = sorted(set(r['yr'] for r in ROWS))
BLOCKS = sorted(set(r['block'] for r in ROWS))

# per-year / per-block base WR
YEAR_BASE = {}
for yr in YEARS:
    sub = [r for r in ROWS if r['yr'] == yr]
    YEAR_BASE[yr] = sum(x['win'] for x in sub) / len(sub)
BLOCK_BASE = {}
for b in BLOCKS:
    sub = [r for r in ROWS if r['block'] == b]
    BLOCK_BASE[b] = sum(x['win'] for x in sub) / len(sub)

FORBIDDEN = {'R', 'win', 'cj', 'low_idx', 'block', 'low_t', 'yr'}
FEATURES = [k for k in ROWS[0].keys() if k not in FORBIDDEN]


def feat_stats(name):
    vals = [r[name] for r in ROWS if r[name] is not None]
    nnull = sum(1 for r in ROWS if r[name] is None)
    if not vals:
        return
    uniq = set(vals)
    const = len(uniq) == 1
    try:
        vs = sorted(vals)
        q = lambda p: vs[min(len(vs)-1, int(p*len(vs)))]
        print(f"{name:20s} null={nnull:4d} const={const} min={min(vals):.3g} "
              f"q25={q(.25):.3g} med={q(.5):.3g} q75={q(.75):.3g} max={max(vals):.3g} nuniq={len(uniq)}")
    except TypeError:
        print(f"{name:20s} null={nnull:4d} non-numeric uniq={list(uniq)[:5]}")


if __name__ == '__main__':
    print(f"n={N} WR_base={BASE_WR:.4f}")
    print("YEAR_BASE:", {k: round(v, 4) for k, v in YEAR_BASE.items()})
    print("BLOCK_BASE:", {k: round(v, 4) for k, v in BLOCK_BASE.items()})
    print("\n=== FEATURE STATS ===")
    for f in FEATURES:
        feat_stats(f)
    # null coverage on HTF features (h4_/hd_)
    print("\n=== HTF null coverage ===")
    for f in ['h1_trend', 'h4_trend', 'hd_trend']:
        nn = sum(1 for r in ROWS if r[f] is None)
        print(f"{f}: null={nn} ({nn/N:.1%})")
