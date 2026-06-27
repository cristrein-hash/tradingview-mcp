#!/usr/bin/env python3
"""
_engine_rsi_ema_momentum.py

Lente RSI/EMA/momentum sobre entry_dataset.jsonl.
Universo = reclaim-entries (n=3519). Alvo = R_reclaim (let-run, SL estrutural).
Base avgR=+0.7265, WR=45.4%.

REGRAS DURAS:
 - Features de entrada SÓ as causais no bar do reclaim. NUNCA usar
   near_M8/R_reclaim/R_8atr/held8/runner como feature (são alvo).
 - Reportar n, WR, avgR, avgR por ano (2024/2025/2026).
 - robust = avgR > base nos 3 anos E n>=30 E nao-carregada-por-2-trades (ex-top2 ainda > base).

Lente: rsi, rsi_head, rsi_low, dist_ema_atr, ema_slope_atr, disp4/8_atr, up_closes8, range_exp.
"""
import json, itertools
from collections import defaultdict

BASE_AVGR = 0.7265
ROWS = [json.loads(l) for l in open('entry_dataset.jsonl')]
N = len(ROWS)

def stats(sub):
    if not sub:
        return None
    R = [r['R_reclaim'] for r in sub]
    n = len(R)
    avg = sum(R)/n
    wr = sum(1 for x in R if x > 0)/n
    by = {}
    for y in (2024, 2025, 2026):
        ys = [r['R_reclaim'] for r in sub if r['yr'] == y]
        by[y] = (len(ys), (sum(ys)/len(ys) if ys else None),
                 (sum(1 for x in ys if x > 0)/len(ys) if ys else None))
    # ex-top2 robustness
    Rs = sorted(R, reverse=True)
    extop2 = (sum(Rs[2:])/(n-2)) if n > 2 else None
    runners = sum(1 for x in R if x >= 5)
    return dict(n=n, wr=wr, avg=avg, by=by, extop2=extop2, runners=runners)

def is_robust(s):
    if s is None or s['n'] < 30:
        return False
    for y in (2024, 2025, 2026):
        ny, ay, _ = s['by'][y]
        if ny < 5 or ay is None or ay <= BASE_AVGR:
            return False
    if s['extop2'] is None or s['extop2'] <= BASE_AVGR:
        return False
    return True

def fmt(name, s):
    if s is None:
        print(f"{name}: EMPTY")
        return
    b = s['by']
    print(f"\n=== {name} ===")
    print(f" n={s['n']} WR={s['wr']*100:.1f}% avgR={s['avg']:+.3f} "
          f"lift={s['avg']-BASE_AVGR:+.3f} runners={s['runners']} extop2={s['extop2']:+.3f}")
    print(f"  y24 n={b[2024][0]} avgR={fnum(b[2024][1])} | "
          f"y25 n={b[2025][0]} avgR={fnum(b[2025][1])} | "
          f"y26 n={b[2026][0]} avgR={fnum(b[2026][1])}  ROBUST={is_robust(s)}")

def fnum(x):
    return f"{x:+.3f}" if x is not None else "NA"

# ---------------------------------------------------------------------------
# PHASE 1: single-feature threshold sweep (lente features only)
# ---------------------------------------------------------------------------
LENS = ['rsi', 'rsi_head', 'rsi_low', 'dist_ema_atr', 'ema_slope_atr',
        'disp4_atr', 'disp8_atr', 'up_closes8', 'range_exp']

def sweep_feature(feat, qs=(0.2,0.3,0.4,0.5,0.6,0.7,0.8)):
    vals = sorted(r[feat] for r in ROWS)
    cuts = [vals[int(q*len(vals))] for q in qs]
    out = []
    for c in sorted(set(cuts)):
        for op, lab in [('>=', f'{feat}>={c:.3f}'), ('<', f'{feat}<{c:.3f}')]:
            if op == '>=':
                sub = [r for r in ROWS if r[feat] >= c]
            else:
                sub = [r for r in ROWS if r[feat] < c]
            s = stats(sub)
            if s and s['n'] >= 30:
                out.append((lab, s))
    return out

print("#"*70)
print("# PHASE 1 — single-feature sweeps (sorted by avgR, n>=100)")
print("#"*70)
all_single = []
for f in LENS:
    all_single += sweep_feature(f)
all_single = [(l, s) for (l, s) in all_single if s['n'] >= 100]
all_single.sort(key=lambda x: -x[1]['avg'])
for lab, s in all_single[:18]:
    fmt(lab, s)

# ---------------------------------------------------------------------------
# PHASE 2: robust single rules (any n>=30)
# ---------------------------------------------------------------------------
print("\n" + "#"*70)
print("# PHASE 2 — ROBUST single rules (3-year stable, n>=30)")
print("#"*70)
robust_single = []
for f in LENS:
    for lab, s in sweep_feature(f, qs=(0.1,0.2,0.25,0.3,0.4,0.5,0.6,0.7,0.75,0.8,0.9)):
        if is_robust(s):
            robust_single.append((lab, s))
# dedup by label
seen = set()
robust_single = [(l, s) for (l, s) in robust_single if not (l in seen or seen.add(l))]
robust_single.sort(key=lambda x: -x[1]['avg'])
for lab, s in robust_single[:15]:
    fmt(lab, s)

# ---------------------------------------------------------------------------
# PHASE 3: 2-feature combos among lens. Grid of percentile cuts.
# ---------------------------------------------------------------------------
print("\n" + "#"*70)
print("# PHASE 3 — 2-feature combos (ROBUST, n>=30, sorted by avgR)")
print("#"*70)

def cut_options(feat):
    vals = sorted(r[feat] for r in ROWS)
    opts = []
    for q in (0.25, 0.4, 0.5, 0.6, 0.75):
        c = vals[int(q*len(vals))]
        opts.append(('>=', c, f'{feat}>={c:.3f}'))
        opts.append(('<', c, f'{feat}<{c:.3f}'))
    return opts

combos = []
for fa, fb in itertools.combinations(LENS, 2):
    for (oa, ca, la) in cut_options(fa):
        for (ob, cb, lb) in cut_options(fb):
            def keep(r):
                a = (r[fa] >= ca) if oa == '>=' else (r[fa] < ca)
                b = (r[fb] >= cb) if ob == '>=' else (r[fb] < cb)
                return a and b
            sub = [r for r in ROWS if keep(r)]
            s = stats(sub)
            if s and is_robust(s):
                combos.append((f'{la} AND {lb}', s))

# dedup + rank by avgR, prefer larger n among similar
seen = set()
ded = []
for l, s in combos:
    key = (round(s['avg'], 3), s['n'])
    if key in seen:
        continue
    seen.add(key)
    ded.append((l, s))
ded.sort(key=lambda x: (-x[1]['avg']))
for lab, s in ded[:20]:
    fmt(lab, s)

print("\n" + "#"*70)
print(f"# TOTAL robust 2-combos found: {len(combos)}")
print("#"*70)
