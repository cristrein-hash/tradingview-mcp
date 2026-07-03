#!/usr/bin/env python3
"""LAB G — DA-PRE probe (2026-07-03).

Adversarial audit of the two SURVIVING designer systems before execution:
  A) capitulation S2-BULL "EMA-SHAKEOUT"
  B) regimemap "PoT-Map v2"
(structure designer's S1/S2 self-killed; audited on claims only)

Probes (all reproducible, fail-loud):
 1. Regime x year composition + population drift by regime/year (2025-BULL-fit attack)
 2. Reproduce both predicates from spec text; report reproduction deltas vs claimed panels
 3. Lens/response redundancy: correlation matrix of "proof/response" family
 4. g_risk shift of selected vs pool (response lens buys WR at convexity cost?)
 5. Overlap between the two surviving systems (independent convergence or same trades?)
 6. Nulls: regime-frequency-matched (500 reps) for both reproduced sets
 7. BULL-only null for S2-BULL (is it just "being in BULL"?)
 8. Jackknife: week concentration
Outcome (g_R) used ONLY to audit frozen specs, never to build predicates.
"""
import json, random, statistics as st
from collections import defaultdict

random.seed(20260703)
ROWS = [json.loads(l) for l in open(
    '/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo/results/lab_g_candidates.jsonl')]
COST_SB = 0.80  # dollars; cost_R = 0.8/g_risk


def yr(r): return r['yr']


def panel(rows, label, cost=True):
    if not rows:
        print(f"{label}: N=0"); return
    Rs = [r['g_R'] for r in rows]
    net = [r['g_R'] - COST_SB / max(r['g_risk'], 1e-9) for r in rows]
    def stats(v):
        wr = sum(1 for x in v if x > 0) / len(v)
        s = sum(v)
        eq = mdd = pk = 0.0
        st_ = wst = 0
        for x in v:
            eq += x; pk = max(pk, eq); mdd = min(mdd, eq - pk)
            st_ = st_ - 1 if x <= 0 else 0
            wst = min(wst, st_)
        return wr, s, s / len(v), mdd, wst
    wr, s, a, dd, stk = stats(Rs)
    nwr, ns, na, ndd, nstk = stats(net)
    print(f"{label}: N={len(rows)} WR={wr:.1%} sumR={s:+.1f} avgR={a:+.3f} "
          f"maxDD={dd:.1f} streak={stk} | NET WR={nwr:.1%} sumR={ns:+.1f} avgR={na:+.3f} DD={ndd:.1f} stk={nstk}")
    by = defaultdict(list)
    for r in rows: by[yr(r)].append(r['g_R'])
    for y in sorted(by):
        v = by[y]
        print(f"   {y}: N={len(v)} WR={sum(1 for x in v if x>0)/len(v):.0%} sumR={sum(v):+.1f}")
    return s


# ---------- 1. regime x year composition + drift ----------
print("=" * 70)
print("1. REGIME x YEAR (population composition + drift)")
cell = defaultdict(list)
for r in ROWS: cell[(r['g_v5h'], yr(r))].append(r['g_R'])
for k in sorted(cell):
    v = cell[k]
    print(f"  {k}: N={len(v)} WR={sum(1 for x in v if x>0)/len(v):.1%} avgR={sum(v)/len(v):+.3f}")
wk = defaultdict(set)
for r in ROWS: wk[(r['g_v5h'], yr(r))].add(r['g_week'])
print("  regime-weeks:", {k: len(v) for k, v in sorted(wk.items())})

# ---------- 2. reproduce predicates ----------
def resp_cap(r): return r['g_rec_speed'] >= 0.69 or r['reclaim_atr'] >= 2.0

def s2_bull(r):
    return (r['g_v5h'] == 'BULL' and r['h1_trend'] == 1 and r['h1_pos'] >= 0.33
            and (r['above_ema21'] == 0 or r['reclaim_ema_bars'] <= 3)
            and (r['g_atr_spike'] >= 1.27 or r['g_downrun'] >= 3)
            and (r['in_demand'] == 1 or r['htf_demand_any'] == 1)
            and resp_cap(r) and r['g_knife'] == 0)

def pot_lenses(r):
    return sum([
        1 if (r['sell_bub_w'] >= 4 or r['g_rsi_div'] == 1) else 0,
        1 if (r['h1n_choch_up_rec'] == 1 or r['nas_long_16'] >= 1) else 0,
        1 if (r['h1n_in_demand'] == 1 or r['htf_demand_confluence'] == 1) else 0,
        1 if r['g_rec_speed'] >= 0.65 else 0])

def pot_core(r):
    if not (r['reclaim_atr'] >= 1.35 and (r['g_cj_body'] >= 0.40 or r['up_closes_pc'] >= 3)):
        return False
    if r['g_knife'] == 1 and not (r['g_rsi_div'] == 1 or r['sell_bub_w'] >= 4):
        return False
    return True

def pot_pred(r, eff_veto_low=True):
    if not pot_core(r): return False
    k = 2 + (1 if r['g_regime_flip5d'] == 1 else 0)
    reg = r['g_v5h']
    if reg == 'BEAR':
        return r['g_bear_pullback_ok'] == 1
    if pot_lenses(r) < k: return False
    if reg == 'RANGE':
        if r['g_box96'] > 0.60: return False
        veto = (r['downleg_eff'] <= 0.33) if eff_veto_low else (r['downleg_eff'] >= 0.33)
        return not veto
    # BULL
    return (r['h1n_trend'] == 1 and r['h4n_trend'] == 1
            and (r['g_ema21_dist'] <= 0.20 or r['in_demand'] == 1))

def daycap(rows, cap=2):
    out, cnt = [], defaultdict(int)
    for r in sorted(rows, key=lambda x: x['cj_t']):
        d = r['cj_t'] // 86400
        if cnt[d] < cap: cnt[d] += 1; out.append(r)
    return out

print("=" * 70)
print("2. REPRODUCTION")
A = [r for r in ROWS if s2_bull(r)]
panel(A, "A) capit S2-BULL EMA-SHAKEOUT (claim N53 WR62.3% +29.8R/+25.9R net, stk-3)")
for tag, ev in (("veto_low", True), ("veto_high", False)):
    B = daycap([r for r in ROWS if pot_pred(r, ev)])
    print(f"-- PoT-Map v2 downleg_eff {tag}:")
    panel(B, "B) PoT-Map v2 (claim N197 WR48.2% +51.3R/+31.6R net, DD11.8, stk8)")
B = daycap([r for r in ROWS if pot_pred(r, True)])

# ---------- 3. response-family redundancy ----------
print("=" * 70)
print("3. RESPONSE/PROOF FAMILY CORRELATION (pool)")
import math
def corr(a, b):
    ma, mb = sum(a)/len(a), sum(b)/len(b)
    ca = sum((x-ma)*(y-mb) for x, y in zip(a, b))
    return ca / math.sqrt(sum((x-ma)**2 for x in a) * sum((y-mb)**2 for y in b))
fam = ['reclaim_atr', 'g_rec_speed', 'g_cj_body', 'up_closes_pc', 'confirm_body_atr']
for i in range(len(fam)):
    for j in range(i+1, len(fam)):
        a = [r[fam[i]] for r in ROWS]; b = [r[fam[j]] for r in ROWS]
        print(f"  corr({fam[i]},{fam[j]}) = {corr(a,b):+.2f}")

# ---------- 4. g_risk shift ----------
print("=" * 70)
print("4. g_risk MEDIAN (convexity attack): pool vs selected")
print("  pool:", st.median(r['g_risk'] for r in ROWS))
print("  A sel:", st.median(r['g_risk'] for r in A) if A else None)
print("  B sel:", st.median(r['g_risk'] for r in B) if B else None)
print("  pool avg R of winners:", st.mean(r['g_R'] for r in ROWS if r['g_R'] > 0))
if A: print("  A avg R of winners:", st.mean(r['g_R'] for r in A if r['g_R'] > 0))
if B: print("  B avg R of winners:", st.mean(r['g_R'] for r in B if r['g_R'] > 0))
if B: print("  B runners share (R>=3):", sum(1 for r in B if r['g_R'] >= 3)/len(B),
            "pool:", sum(1 for r in ROWS if r['g_R'] >= 3)/len(ROWS))

# ---------- 5. overlap ----------
print("=" * 70)
setA = {r['cj_t'] for r in A}; setB = {r['cj_t'] for r in B}
print(f"5. OVERLAP A∩B = {len(setA & setB)} (A={len(setA)}, B={len(setB)})")
Bbull = [r for r in B if r['g_v5h'] == 'BULL']
print(f"   B BULL-cell N={len(Bbull)} sumR={sum(r['g_R'] for r in Bbull):+.1f}; overlap w/ A = {len({r['cj_t'] for r in Bbull} & setA)}")

# ---------- 6. nulls regime-frequency-matched ----------
print("=" * 70)
print("6. NULLS (500 reps, regime-frequency-matched draws from pool)")
byreg = defaultdict(list)
for r in ROWS: byreg[r['g_v5h']].append(r)
def null_pct(sel, reps=500):
    need = defaultdict(int)
    for r in sel: need[r['g_v5h']] += 1
    obs = sum(r['g_R'] for r in sel)
    sums = []
    for _ in range(reps):
        s = 0.0
        for reg, n in need.items():
            s += sum(x['g_R'] for x in random.sample(byreg[reg], n))
        sums.append(s)
    sums.sort()
    pct = sum(1 for x in sums if x < obs) / reps
    return obs, st.median(sums), sums[int(0.95*reps)], pct
for nm, sel in (("A", A), ("B", B)):
    if sel:
        o, m, p95, pc = null_pct(sel)
        print(f"  {nm}: obs={o:+.1f} null_med={m:+.1f} null_p95={p95:+.1f} percentile={pc:.1%}")
# BULL-only harder null for A: match also response condition (is it just BULL+response?)
poolBR = [r for r in ROWS if r['g_v5h'] == 'BULL' and resp_cap(r) and r['g_knife'] == 0]
if A:
    obs = sum(r['g_R'] for r in A)
    sums = sorted(sum(x['g_R'] for x in random.sample(poolBR, len(A))) for _ in range(500))
    pc = sum(1 for x in sums if x < obs)/500
    print(f"  A vs BULL+response+noknife pool (N={len(poolBR)}, avgR={st.mean(r['g_R'] for r in poolBR):+.3f}):"
          f" obs={obs:+.1f} null_med={st.median(sums):+.1f} percentile={pc:.1%}")
# proof-core-matched null for B
poolC = [r for r in ROWS if pot_core(r)]
if B:
    obs = sum(r['g_R'] for r in B)
    sums = sorted(sum(x['g_R'] for x in random.sample(poolC, len(B))) for _ in range(500))
    pc = sum(1 for x in sums if x < obs)/500
    print(f"  B vs proof-core pool (N={len(poolC)}, avgR={st.mean(r['g_R'] for r in poolC):+.3f}):"
          f" obs={obs:+.1f} null_med={st.median(sums):+.1f} percentile={pc:.1%}")

# ---------- 7. jackknife week concentration ----------
print("=" * 70)
print("7. WEEK CONCENTRATION")
for nm, sel in (("A", A), ("B", B)):
    bw = defaultdict(float)
    for r in sel: bw[r['g_week']] += r['g_R']
    top = sorted(bw.values(), reverse=True)[:3]
    tot = sum(bw.values())
    print(f"  {nm}: total={tot:+.1f} top3wk={sum(top):+.1f} (-top3 = {tot-sum(top):+.1f}); active weeks={len(bw)}")
