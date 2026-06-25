#!/usr/bin/env python3
"""VIA A — RÉGUA sob SL ESTRUTURAL (SL_CONTEXT) + let-run. Reusa a logica de exit EXATA de
l2_bpt_exit_calibration_full276.py, só troca setup() (SL tight 1.5-ceil → SL_CONTEXT sl_atr, sem teto).
(1) AUTO-VALIDA: SL tight reproduz a tabela salva (motor fiel?). (2) Calibracao sob SL_CONTEXT (let-run lidera? +P1/P2?).
(3) GT-validacao: SL_CONTEXT stop vs gt_stop_cris (price-match). (4) Dump per-trade R-estrutural (capped=rotulo, letrun=diagnostico).
Causal stop-first. Calibracao 276 (canon). Verified 2026-06-25."""
import json, csv
from pathlib import Path
V1 = Path(__file__).resolve().parents[1]
RR = V1 / "repro_recovery"
frozen = [json.loads(l) for l in open(RR / "raw_features_2020_2026.jsonl")]
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
def fn(v):
    try: return float(v)
    except Exception: return None

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
    risk = SLCTX[i] * atr; sl = p - risk
    if risk <= 0: return None
    return p, sl, risk

STAIR = [(2, 0), (5, 2), (8, 5), (12, 8), (16, 12), (20, 16)]
def exits(i, setup, HZ=120):
    s = setup(i)
    if not s: return None
    p, sl, risk = s; end = min(i + HZ, N - 1)
    peak = 0.0; lock = -1.0; capped_done = None
    for j in range(i + 1, end + 1):
        highR = (H[j] - p) / risk
        if capped_done is None:
            if L[j] <= sl: capped_done = -1.0
            elif highR >= 4.0: capped_done = 4.0
        if L[j] > sl: peak = max(peak, highR)
        for trig, lk in STAIR:
            if peak >= trig and lk > lock: lock = float(lk)
        if L[j] <= sl: break
    close_end = (C[end] - p) / risk
    stopped = any(L[j] <= sl for j in range(i + 1, end + 1))
    mfe_struct = max(((H[j] - p) / risk for j in range(i + 1, end + 1)), default=0.0)
    return {"capped": capped_done if capped_done is not None else close_end,
            "letrun": -1.0 if stopped else close_end, "mfe_s": mfe_struct, "risk": risk, "sl": sl, "entry": p}

def calib(setup, label, cost=0.35):
    per = {}
    for b in sorted(unc):
        r = exits(b, setup)
        if r: per[b] = r
    def agg(sub=None, key="letrun"):
        bs = [b for b in per if (sub is None or sub(b))]
        rs = [per[b][key] - cost for b in bs]; n = len(rs)
        if not n: return None
        order = sorted(bs, key=lambda b: T[b]); cum = peak = mdd = ls = best = 0
        for b in order:
            r = per[b][key] - cost; cum += r; peak = max(peak, cum); mdd = max(mdd, peak - cum)
            ls = 0 if r > 0 else ls + 1; best = max(best, ls)
        wins = sum(1 for r in rs if r > 0)
        return dict(n=n, sumR=round(sum(rs), 1), WR=round(100 * wins / n, 1), maxDD=round(mdd, 1), streak=best)
    P1 = lambda b: T[b] < 1672531200  # 2023-01-01
    P2 = lambda b: T[b] >= 1672531200
    print(f"\n=== {label} (cost {cost}) ===  [n trades={len(per)}]")
    for key in ("capped", "letrun"):
        a = agg(None, key); a1 = agg(P1, key); a2 = agg(P2, key)
        print(f"  {key:>7}: ALL sumR={a['sumR']:>7} WR={a['WR']:>5} maxDD={a['maxDD']:>5} streak={a['streak']:>3} | "
              f"P1 sumR={a1['sumR']:>7} P2 sumR={a2['sumR']:>7}")
    return per

print("=" * 70)
print("(1) AUTO-VALIDACAO — SL tight deve reproduzir a tabela salva (letrun~+144.6, capped~+68.8 @0.35)")
calib(setup_tight, "SL TIGHT (reproducao)")
print("\n" + "=" * 70)
print("(2) REGUA SOB SL_CONTEXT (estrutural) — let-run ainda lidera? +nos dois periodos?")
per_ctx = calib(setup_ctx, "SL_CONTEXT (estrutural)")

# (3) GT-validacao: SL_CONTEXT stop vs gt_stop_cris (price-match ao frozen)
print("\n" + "=" * 70 + "\n(3) GT-VALIDACAO — SL_CONTEXT reproduz teus stops? (price-match)")
gt = list(csv.DictReader(open(V1 / "results/l2_bpt_real_outcome_sl_validation.csv")))
import statistics
diffs = []; ctx_vs_gt = []
for g in gt:
    entry = float(g['entry']); gt_stop = float(g['gt_stop_cris'])
    cands = [(abs(C[i] - entry), i) for i in SLCTX if abs(C[i] - entry) < 1.0 and ATR[i]]
    if not cands: continue
    _, i = min(cands); ctx_stop = C[i] - SLCTX[i] * ATR[i]
    diffs.append(abs(ctx_stop - gt_stop)); ctx_vs_gt.append((C[i] - ctx_stop) / max(1e-9, (entry - gt_stop)))
if diffs:
    print(f"  matched {len(diffs)}/{len(gt)} GT entries | |SL_CONTEXT_stop - gt_stop| mediano = {statistics.median(diffs):.1f} preco")
    print(f"  razao risco SL_CONTEXT/gt mediano = {statistics.median(ctx_vs_gt):.2f} (1.0=igual, <1=mais tight que tu, >1=mais largo)")

# (4) dump per-trade R-estrutural (rotulo=capped, diagnostico=letrun)
with open(V1 / "results/l2_bpt_regua_structural.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["bar_idx", "entry", "sl", "risk", "capped_struct", "letrun_struct", "mfe_struct"])
    for b in sorted(per_ctx):
        r = per_ctx[b]; w.writerow([b, round(r['entry'], 2), round(r['sl'], 2), round(r['risk'], 2),
                                    round(r['capped'], 2), round(r['letrun'], 2), round(r['mfe_s'], 2)])
print(f"\nper-trade R-estrutural -> results/l2_bpt_regua_structural.csv ({len(per_ctx)} trades). capped=rotulo, letrun=diagnostico (DA).")
