#!/usr/bin/env python3
"""FOLLOW-UP aos checks do DA. Reusa motor validado. (OBJ-1) capped/letrun × tight/structural no COMMON-245 +
grade de custo 0.2/0.35/0.5. (OBJ-3) fracao em que o cap +4R BINDA (tight vs struct) + bars-held + mfe mediano.
(OBJ-5) capped vs letrun nos teus STOPS GT diretos (n matched). Calibracao 276 (canon). Verified 2026-06-25."""
import json, csv, statistics
from pathlib import Path
V1 = Path(__file__).resolve().parents[1]
frozen = [json.loads(l) for l in open(V1 / "repro_recovery/raw_features_2020_2026.jsonl")]
N = len(frozen); H = [r['high'] for r in frozen]; L = [r['low'] for r in frozen]; C = [r['close'] for r in frozen]
T = [int(r['ts_epoch']) for r in frozen]
ATR = [None] * N; trs = []
for i in range(1, N):
    trs.append(max(H[i] - L[i], abs(H[i] - C[i - 1]), abs(L[i] - C[i - 1])))
    if i >= 14: ATR[i] = sum(trs[i - 14:i]) / 14
unc = {int(r['bar_idx']): r for r in csv.DictReader(open(V1 / "results/l2_bpt_uncapped_or_proxy_outcomes_276.csv"))}
SLCTX = {}
for r in csv.DictReader(open(V1 / "results/l2_bpt_sl_context_policy_results.csv")):
    try: SLCTX[int(float(r['i']))] = float(r['sl_atr'])
    except Exception: pass
RW = 6; R_FLOOR = 0.3; R_CEIL = 1.5
def setup_tight(i):
    p = C[i]; atr = ATR[i]
    if not atr: return None
    lo = min(L[max(0, i - RW + 1):i + 1]); sl = lo - 0.1 * atr; risk = p - sl
    if risk <= 0: return None
    if risk < R_FLOOR * atr: risk = R_FLOOR * atr; sl = p - risk
    if risk > R_CEIL * atr: risk = R_CEIL * atr; sl = p - risk
    return p, sl, risk
def setup_ctx(i):
    p = C[i]; atr = ATR[i]
    if not atr or i not in SLCTX: return None
    risk = SLCTX[i] * atr
    return (p, p - risk, risk) if risk > 0 else None
STAIR = [(2, 0), (5, 2), (8, 5), (12, 8), (16, 12), (20, 16)]
def sim(i, p, sl, risk, HZ=120):
    end = min(i + HZ, N - 1); capped_done = None; cap_bound = False; held = HZ
    for j in range(i + 1, end + 1):
        highR = (H[j] - p) / risk
        if capped_done is None:
            if L[j] <= sl: capped_done = -1.0; held = j - i
            elif highR >= 4.0: capped_done = 4.0; cap_bound = True; held = j - i
        if L[j] <= sl: break
    close_end = (C[end] - p) / risk
    stopped = any(L[j] <= sl for j in range(i + 1, end + 1))
    mfe = max(((H[j] - p) / risk for j in range(i + 1, end + 1)), default=0.0)
    return {"capped": capped_done if capped_done is not None else close_end,
            "letrun": -1.0 if stopped else close_end, "cap_bound": cap_bound, "held": held, "mfe": mfe}

def stats(per, key, cost, bs):
    rs = [per[b][key] - cost for b in bs]; n = len(rs)
    if not n: return None
    order = sorted(bs, key=lambda b: T[b]); cum = peak = mdd = ls = best = 0
    for b in order:
        r = per[b][key] - cost; cum += r; peak = max(peak, cum); mdd = max(mdd, peak - cum)
        ls = 0 if r > 0 else ls + 1; best = max(best, ls)
    return dict(n=n, sumR=round(sum(rs), 1), WR=round(100 * sum(1 for r in rs if r > 0) / n, 1), maxDD=round(mdd, 1), streak=best)

# motores por conjunto
COMMON = sorted(SLCTX.keys())  # 245
per_t = {b: sim(b, *setup_tight(b)) for b in COMMON if setup_tight(b)}
per_c = {b: sim(b, *setup_ctx(b)) for b in COMMON if setup_ctx(b)}
common = sorted(set(per_t) & set(per_c))
print(f"COMMON-245 = {len(common)} trades (mesmo conjunto, isola efeito-SL)\n")
print("(OBJ-1/2) capped vs letrun × tight/struct no COMMON, grade de custo:")
print(f"{'régua':>10} {'exit':>7} | " + " | ".join(f"cost{c}" for c in (0.2, 0.35, 0.5)))
for lbl, per in (("TIGHT", per_t), ("STRUCT", per_c)):
    for key in ("capped", "letrun"):
        cells = " | ".join(f"{stats(per, key, c, common)['sumR']:>7}" for c in (0.2, 0.35, 0.5))
        print(f"{lbl:>10} {key:>7} | {cells}")
print("\n  detalhe @0.35 COMMON:")
for lbl, per in (("TIGHT", per_t), ("STRUCT", per_c)):
    for key in ("capped", "letrun"):
        a = stats(per, key, 0.35, common); print(f"    {lbl} {key}: sumR={a['sumR']} WR={a['WR']} maxDD={a['maxDD']} streak={a['streak']}")

# (OBJ-3) cap-binding fraction + held + mfe
print("\n(OBJ-3) cap +4R BINDA? (mecânica da convergência):")
for lbl, per in (("TIGHT", per_t), ("STRUCT", per_c)):
    cb = sum(1 for b in common if per[b]["cap_bound"]) / len(common)
    held = statistics.median(per[b]["held"] for b in common)
    mfe = statistics.median(per[b]["mfe"] for b in common)
    print(f"  {lbl}: cap binda em {cb:.0%} dos trades | bars-held mediano={held:.0f} | mfe mediano={mfe:.2f}R")

# (OBJ-5) capped vs letrun nos teus STOPS GT diretos
print("\n(OBJ-5) capped vs letrun nos teus STOPS GT diretos (decisivo p/ tua previsão):")
gt = list(csv.DictReader(open(V1 / "results/l2_bpt_real_outcome_sl_validation.csv")))
B276 = sorted(unc.keys())
per_gt = {}; ratios = []
for k, g in enumerate(gt):
    entry = float(g['entry']); gt_stop = float(g['gt_stop_cris'])
    cand = [(abs(C[i] - entry), i) for i in B276 if ATR[i] and abs(C[i] - entry) < 1.0]
    if not cand: continue
    _, i = min(cand); risk = C[i] - gt_stop
    if risk <= 0: continue
    per_gt[k] = sim(i, C[i], gt_stop, risk)
    if i in SLCTX: ratios.append((SLCTX[i] * ATR[i]) / risk)
ng = len(per_gt)
if ng:
    for key in ("capped", "letrun"):
        rs = [per_gt[k][key] - 0.35 for k in per_gt]
        print(f"  {key}: n={ng} sumR={sum(rs):+.1f} avgR={sum(rs)/ng:+.3f} WR={100*sum(1 for r in rs if r>0)/ng:.0f}%")
    print(f"  (razao SL_CONTEXT/GT mediano nos matched = {statistics.median(ratios):.2f})" if ratios else "")
print("\nCalibracao 276 (canon). capped=rotulo só calibra; nada vira gate/validação.")
