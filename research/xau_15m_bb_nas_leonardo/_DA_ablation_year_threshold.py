#!/usr/bin/env python3
"""DA ATTACKS 3/4/5 sobre htf_demand_retest.
3: ablacao DEMAND vs MATURITY/POSITION — qual sub-conjunto carrega o sinal? proxy p/ reclaim_lag?
4: 2026 vs 2025 — o lift vive so em 2025?
5: estabilidade do keep-threshold.
"""
import sys, json
sys.path.insert(0, "/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo")
import numpy as np, datetime as dt
from mtf_kit import _loo
from agent_ctx_kit import ENTRIES

HERE = "/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo"
NS = [e["n"] for e in ENTRIES]
y = np.array([e["out"] for e in ENTRIES], dtype=float)
YR = np.array([dt.datetime.utcfromtimestamp(int(e["t"])).year for e in ENTRIES])
RLAG = np.array([e["reclaim_lag"] for e in ENTRIES], dtype=float)

rows = json.load(open(f"{HERE}/results/mtf_feat_htf_demand_retest.json"))
by_n = {r["n"]: r for r in rows}
KEYS = [k for k in rows[0].keys() if k != "n"]
Xraw = np.array([[by_n[n][k] for k in KEYS] for n in NS], dtype=float)
Xraw = np.nan_to_num(Xraw)

DEMAND = [k for k in KEYS if any(s in k for s in ("demand", "retest"))]
MATPOS = [k for k in KEYS if any(s in k for s in ("leg_maturity", "leg_pos"))]
print("DEMAND feats:", DEMAND)
print("MATPOS feats:", MATPOS)

def run(subset, thr=0.5):
    idx = [KEYS.index(k) for k in subset]
    X = Xraw[:, idx]
    mu = X.mean(0); sd = X.std(0) + 1e-9; Xs = (X - mu) / sd
    P = _loo(Xs, y); keep = P > thr
    if keep.sum() == 0: return None
    hit = y[keep].mean()
    m25 = keep & (YR == 2025); m26 = keep & (YR == 2026)
    return dict(N=int(keep.sum()), hit=round(float(hit), 3),
                y2025=f"{int(y[m25].sum())}/{int(m25.sum())}",
                y2026=f"{int(y[m26].sum())}/{int(m26.sum())}",
                hit25=round(float(y[m25].mean()), 3) if m25.sum() else None,
                hit26=round(float(y[m26].mean()), 3) if m26.sum() else None,
                P=P)

print("\n=== ATTACK 3: ABLACAO ===")
for name, sub in [("ALL(12)", KEYS), ("DEMAND-only(8)", DEMAND), ("MATPOS-only(4)", MATPOS)]:
    r = run(sub)
    print(f"  {name:16s} N={r['N']:3d} oof_hit={r['hit']:.3f}  2025={r['y2025']}({r['hit25']}) 2026={r['y2026']}({r['hit26']})")

# proxy check: correlacao das features MATPOS/DEMAND com reclaim_lag
print("\n  corr(feature, reclaim_lag):")
for k in KEYS:
    c = np.corrcoef(Xraw[:, KEYS.index(k)], RLAG)[0, 1]
    print(f"    {k:26s} r={c:+.3f}")

# baseline: reclaim_lag SOZINHO consegue o mesmo?
Xr = RLAG.reshape(-1, 1); Xrs = (Xr - Xr.mean()) / (Xr.std() + 1e-9)
Pr = _loo(Xrs, y); kr = Pr > 0.5
print(f"\n  reclaim_lag SOZINHO: N={int(kr.sum())} oof_hit={y[kr].mean():.3f}" if kr.sum() else "  reclaim_lag sozinho: keep vazio")

print("\n=== ATTACK 4: 2026 vs 2025 (base: 2025=29/46=63.0% · 2026=23/50=46.0%) ===")
r = run(KEYS)
lift25 = (r['hit25'] or 0) - 29/46
lift26 = (r['hit26'] or 0) - 23/50
print(f"  kept 2025 hit={r['hit25']} (base .630, LIFT {lift25:+.3f})")
print(f"  kept 2026 hit={r['hit26']} (base .460, LIFT {lift26:+.3f})")

print("\n=== ATTACK 5: ESTABILIDADE THRESHOLD ===")
for thr in (0.45, 0.48, 0.50, 0.52, 0.55, 0.60):
    r = run(KEYS, thr)
    if r: print(f"  thr={thr:.2f}  N={r['N']:3d} oof_hit={r['hit']:.3f}  2025={r['y2025']} 2026={r['y2026']}")
    else: print(f"  thr={thr:.2f}  keep vazio")
