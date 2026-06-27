"""
DEVIL'S ADVOCATE verification of the entry rule:
  RULE: disp4<=-0.65 & in_demand
  Definition: disp4_atr <= -0.649  AND  in_demand == 1
  (entering on a short-term pullback/discount, NOT chasing momentum,
   with the low inside a pre-existing RAW demand zone)

Reported: n=1096 WR=48.1 avgR=1.058 y24=1.13 y25=1.04 y26=1

Conventions (matching sibling _verify_*.py in this dir):
  - dataset = entry_dataset_novel.jsonl  (in_demand only exists here, not entry_dataset.jsonl)
  - R field = R_reclaim
  - blocks = the 'block' field (8 replay collection blocks)

Régua (Cris): NÃO vetar por tail/WR-only/sem-OOS.
  VETAR só por: look-ahead, não-estacionariedade (avgR muda de sinal
  entre anos OU blocos), carregada por 1-2 trades (ex-top2 colapsa),
  n frágil, near_M8/outcome usados como feature.

Checks:
  1. reproduce base n/WR/avgR
  2. per-year avgR sign stability
  3. leave-one-block-out: worst remaining-fold avgR + held-out block avgR sign
  4. ex-top1 / ex-top2 collapse
  5. look-ahead: features are bar-of-reclaim; in_demand causal-guarded in builder;
     neither feature is an outcome field
  6. multiple-testing: rank of this avgR among many 2-feature threshold rules (n>=MIN_N)
"""
import json
from collections import defaultdict

DS = 'entry_dataset_novel.jsonl'
RF = 'R_reclaim'
rows = [json.loads(l) for l in open(DS)]


def rule(r):
    return r.get('disp4_atr', 99) <= -0.649 and r.get('in_demand', 0) == 1


sel = [r for r in rows if rule(r) and r.get(RF) is not None]
vals = [r[RF] for r in sel]
n = len(vals)
avg = sum(vals) / n
wr = sum(1 for x in vals if x > 0) / n * 100
print(f"=== BASE: n={n} WR={wr:.1f} avgR={avg:.3f} sumR={sum(vals):.1f}")
print(f"    reported: n=1096 WR=48.1 avgR=1.058")

# ---- 1. per year ----
print("\n[1] per-year:")
peryear = defaultdict(list)
for r in sel:
    peryear[r['yr']].append(r[RF])
year_avgs = {}
for y in sorted(peryear):
    v = peryear[y]
    a = sum(v) / len(v)
    year_avgs[y] = a
    w = sum(1 for x in v if x > 0) / len(v) * 100
    print(f"  y{y}: n={len(v):4d} avgR={a:.3f} WR={w:.1f}")
peryear_ok = all(a > 0 for a in year_avgs.values())
print(f"  per-year all positive sign: {peryear_ok}")

# ---- 2. leave-one-block-out ----
print("\n[2] leave-one-block-out (rest = trained-on-rest, block = held-out):")
byblock = defaultdict(list)
for r in sel:
    byblock[r['block']].append(r[RF])
block_avgs = []
worst_rest = 99
for b in sorted(byblock):
    rest = [r[RF] for r in sel if r['block'] != b]
    blk = byblock[b]
    arest = sum(rest) / len(rest)
    ablk = sum(blk) / len(blk)
    worst_rest = min(worst_rest, arest)
    block_avgs.append((b, ablk, arest))
    print(f"  block {b}: rest n={len(rest):4d} restAvgR={arest:.3f} | "
          f"held n={len(blk):3d} blkAvgR={ablk:.3f}")
min_block_avg = min(ab for _, ab, _ in block_avgs)
print(f"  worst remaining-fold (rest) avgR = {worst_rest:.3f}")
print(f"  min held-out block avgR        = {min_block_avg:.3f}")
n_neg_blocks = sum(1 for _, ab, _ in block_avgs if ab <= 0)
print(f"  held-out blocks with avgR<=0   = {n_neg_blocks}/{len(block_avgs)}")

# ---- 3. ex-top concentration ----
print("\n[3] ex-top concentration:")
s = sorted(vals, reverse=True)
for k in (1, 2, 3):
    rem = s[k:]
    a = sum(rem) / len(rem)
    print(f"  ex-top{k}: n={len(rem)} avgR={a:.3f} (top{k} sum={sum(s[:k]):.1f})")
extop2 = sum(s[2:]) / len(s[2:])

# ---- 4. look-ahead ----
print("\n[4] look-ahead audit:")
print("  disp4_atr = displacement over 4 bars ending at reclaim bar (past-only).")
print("  in_demand = low inside zone with born_t<=low_t (causal guard in builder).")
print("  Neither is an outcome field (R_reclaim/held8/runner/R_8atr/near_M8).")

# ---- 5. multiple-testing ----
print("\n[5] multiple-testing context:")
MIN_N = 300
feats = ['macro_drop_atr', 'macro_retr', 'rsi', 'rsi_low', 'dist_ema_atr',
         'ema_slope_atr', 'sweep_depth_atr', 'disp4_atr', 'disp8_atr',
         'up_closes8', 'range_exp', 'leg_ext', 'room_atr', 'low_wick',
         'low_closepos', 'atr_regime', 'vol_low_vs_med', 'dz_dist_atr',
         'decel_ratio', 'since_pivot']
allr = [r for r in rows if r.get(RF) is not None]
results = []
import numpy as np
for f in feats:
    xs = sorted(set(r[f] for r in allr if isinstance(r.get(f), (int, float))))
    if len(xs) < 5:
        continue
    qs = [xs[int(len(xs) * q)] for q in (0.1, 0.25, 0.5, 0.75, 0.9)]
    for thr in qs:
        for direc in ('<=', '>='):
            for f2, d2 in [('in_demand', 1)]:
                if direc == '<=':
                    grp = [r[RF] for r in allr
                           if isinstance(r.get(f), (int, float)) and r[f] <= thr
                           and r.get(f2, 0) == d2]
                else:
                    grp = [r[RF] for r in allr
                           if isinstance(r.get(f), (int, float)) and r[f] >= thr
                           and r.get(f2, 0) == d2]
                if len(grp) >= MIN_N:
                    results.append((sum(grp) / len(grp), f, direc, thr, len(grp)))
results.sort(reverse=True)
better = sum(1 for a, *_ in results if a >= avg)
print(f"  scanned {len(results)} 2-feature rules (X{{<=,>=}}thr & in_demand) n>={MIN_N}")
print(f"  top avgR={results[0][0]:.3f} ({results[0][1]} {results[0][2]} {results[0][3]:.3f})")
print(f"  rules reaching avgR>={avg:.3f}: {better}/{len(results)} "
      f"({better/len(results)*100:.1f}%)")

# ---- verdict ----
print("\n=== SUMMARY ===")
print(f"avgR={avg:.3f} WR={wr:.1f} n={n}")
print(f"per-year sign-stable: {peryear_ok}  | min year avgR={min(year_avgs.values()):.3f}")
print(f"worst-rest fold avgR={worst_rest:.3f} | min held block avgR={min_block_avg:.3f} "
      f"| neg blocks={n_neg_blocks}")
print(f"ex-top2 avgR={extop2:.3f} (vs base {avg:.3f})")
