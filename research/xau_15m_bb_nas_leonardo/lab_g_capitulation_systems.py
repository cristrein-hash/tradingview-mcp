#!/usr/bin/env python3
"""LAB G — Capitulation-physics entry systems: FREEZE + measurement.

Two stages, run separately (design discipline):
  stage=freq  : frequency-per-regime-week of the frozen predicates (NO outcome).
                Used ONLY to pick K (S1) inside the 1-3/wk RANGE-BULL band.
  stage=panel : full raw panel (N, WR, sumR, avgR, DD, r/DD, streaks, per-year,
                per-regime freq) + frequency-matched random null. Run ONCE per
                frozen spec. Every invocation is declared in the round ledger.

SYSTEM 1 — "VEXA-R" (Violence-Exhaustion-Sweep-Absorption + mandatory Response)
  Hard gates: swept_prior_low==1 ; regime router (BEAR only via g_bear_pullback_ok).
  Mandatory lens: RESPONSE. Score >= K-1 of the 5 physics lenses L1..L5.
  Thresholds = global q75 of the candidate universe (frozen numbers below).

SYSTEM 2 — "REGIME-FLOOR TRIPTYCH" (distinct predicate per regime)
  BULL: EMA-shakeout — h1 trend intact, flush under EMA21 (or just reclaimed),
        violence, demand context, response, not knifing.
  RANGE: box-floor raid — bottom 35% of 5-day box, deep sweep, absorption or
        RSI exhaustion, response.
  BEAR: pullback-bull only — g_bear_pullback_ok + response + one exhaustion/violence.

Exit/SL are NOT redesigned: g_R is the approved let-run outcome, SL=flush-0.1ATR
(already baked into g_R / g_risk by the builder). Entry = close of cj.
Status of the round: EXPLORATORY_CALIBRATION.
"""
import json, os, sys, random, collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROWS = [json.loads(l) for l in open(os.path.join(HERE, 'results/lab_g_candidates.jsonl'))]

# ---------------- FROZEN THRESHOLDS (global q75-family, from design probe) ----
TH = dict(
    atr_spike=1.27,      # q75
    downrun=3,           # ~q85
    rsi_min8=33,         # ~q20 (oversold tail)
    flush_wick=0.55,     # ~q70
    sweep_depth=1.0,     # ~q75
    rec_speed=0.69,      # q75
    reclaim=2.0,         # ~q75
    box480_floor=0.35,   # RANGE floor band (bottom ~30-35% of 5d box)
)

def lens_response(r):
    return r['g_rec_speed'] >= TH['rec_speed'] or r['reclaim_atr'] >= TH['reclaim']

def s1_lenses(r):
    return [
        r['g_atr_spike'] >= TH['atr_spike'] or r['g_downrun'] >= TH['downrun'],   # L1 violence
        r['rsi_min8'] <= TH['rsi_min8'] or r['g_rsi_div'] == 1,                    # L2 exhaustion-momentum
        r['g_flush_wick'] >= TH['flush_wick'],                                     # L3 exhaustion-rejection
        r['g_sweep_depth'] >= TH['sweep_depth'],                                   # L4 sweep depth
        r['sell_bub_w'] >= 1,                                                      # L5 absorption (contextual polarity)
    ]

def s1_pass(r, kminus1):
    if r['swept_prior_low'] != 1:
        return False
    if r['g_v5h'] == 'BEAR' and r['g_bear_pullback_ok'] != 1:
        return False
    if not lens_response(r):
        return False
    return sum(s1_lenses(r)) >= kminus1

def s2_pass(r):
    reg = r['g_v5h']
    resp = lens_response(r)
    if reg == 'BULL':
        return (r['h1_trend'] == 1 and (r.get('h1_pos') or 0) >= 0.33
                and (r['above_ema21'] == 0 or r['reclaim_ema_bars'] <= 3)
                and (r['g_atr_spike'] >= TH['atr_spike'] or r['g_downrun'] >= TH['downrun'])
                and (r['in_demand'] == 1 or r['htf_demand_any'] == 1)
                and resp and r['g_knife'] == 0)
    if reg == 'RANGE':
        return (r['g_box480'] <= TH['box480_floor']
                and r['swept_prior_low'] == 1 and r['g_sweep_depth'] >= TH['sweep_depth']
                and (r['sell_bub_w'] >= 1 or r['rsi_min8'] <= TH['rsi_min8'] or r['g_rsi_div'] == 1)
                and resp)
    if reg == 'BEAR':
        return (r['g_bear_pullback_ok'] == 1 and resp
                and (r['g_atr_spike'] >= TH['atr_spike'] or r['rsi_min8'] <= TH['rsi_min8']
                     or r['g_flush_wick'] >= TH['flush_wick']))
    return False

# ---------------- measurement helpers ----------------------------------------
def week_regime_map():
    wk = collections.defaultdict(collections.Counter)
    for r in ROWS:
        wk[r['g_week']][r['g_v5h']] += 1
    return {w: c.most_common(1)[0][0] for w, c in wk.items()}

def freq_report(sel, name):
    wr = week_regime_map()
    weeks_by_reg = collections.Counter(wr.values())
    trades_by_regweek = collections.Counter(wr[r['g_week']] for r in sel)
    trades_by_sigreg = collections.Counter(r['g_v5h'] for r in sel)
    print(f'[{name}] N={len(sel)}  ({len(sel)/104:.2f}/wk overall)')
    for reg in ['RANGE', 'BULL', 'BEAR']:
        nw = weeks_by_reg.get(reg, 0)
        print(f'  {reg}: sig-regime N={trades_by_sigreg.get(reg,0)} | in {reg}-weeks '
              f'{trades_by_regweek.get(reg,0)} over {nw} wks = {trades_by_regweek.get(reg,0)/max(nw,1):.2f}/wk')
    active = collections.Counter(r['g_week'] for r in sel)
    print(f'  weeks with >=1 trade: {len(active)}/104 · max wk load {max(active.values()) if active else 0}')

def panel(sel, name):
    if not sel:
        print(f'[{name}] EMPTY'); return
    sel = sorted(sel, key=lambda r: r['cj_t'])
    Rs = [r['g_R'] for r in sel]
    n = len(Rs); wins = sum(1 for x in Rs if x > 0)
    eq = mx = dd = 0.0
    for x in Rs:
        eq += x; mx = max(mx, eq); dd = max(dd, mx - eq)
    ls = ws = cls = cws = 0
    for x in Rs:
        if x <= 0: cls += 1; cws = 0
        else: cws += 1; cls = 0
        ls = max(ls, cls); ws = max(ws, cws)
    per_yr = collections.defaultdict(float); nyr = collections.Counter()
    for r in sel: per_yr[r['yr']] += r['g_R']; nyr[r['yr']] += 1
    ov = sum(r['g_in_base435'] for r in sel)
    print(f'[{name}] N={n} WR={100*wins/n:.1f}% sumR={sum(Rs):+.1f} avgR={sum(Rs)/n:+.3f} '
          f'DD={-dd:.1f} r/DD={sum(Rs)/dd if dd else float("inf"):.2f} streak=-{ls}/+{ws} '
          f'overlap_base435={ov}')
    print('  per-year: ' + ' · '.join(f'{y}: N{nyr[y]} {per_yr[y]:+.1f}R' for y in sorted(per_yr)))
    for reg in ['RANGE', 'BULL', 'BEAR']:
        sub = [r['g_R'] for r in sel if r['g_v5h'] == reg]
        if sub:
            print(f'  {reg}: N={len(sub)} WR={100*sum(1 for x in sub if x>0)/len(sub):.1f}% sumR={sum(sub):+.1f}')
    # halves sub-window sanity
    h = n // 2
    for tag, part in [('H1', Rs[:h]), ('H2', Rs[h:])]:
        print(f'  {tag}: N={len(part)} WR={100*sum(1 for x in part if x>0)/len(part):.1f}% sumR={sum(part):+.1f}')

def null_check(sel, name, iters=500, seed=7):
    """Frequency-matched null: same N drawn at random per signal-regime bucket."""
    rng = random.Random(seed)
    by_reg = collections.Counter(r['g_v5h'] for r in sel)
    pool = {reg: [r['g_R'] for r in ROWS if r['g_v5h'] == reg] for reg in by_reg}
    obs = sum(r['g_R'] for r in sel)
    obs_wr = sum(1 for r in sel if r['g_R'] > 0) / len(sel)
    sums, wrs = [], []
    for _ in range(iters):
        draw = []
        for reg, k in by_reg.items():
            draw += rng.sample(pool[reg], k)
        sums.append(sum(draw)); wrs.append(sum(1 for x in draw if x > 0) / len(draw))
    ps = sum(1 for s in sums if s >= obs) / iters
    pw = sum(1 for w in wrs if w >= obs_wr) / iters
    med = sorted(sums)[iters // 2]
    print(f'  [null x{iters}] sumR: obs {obs:+.1f} vs null med {med:+.1f} → p={ps:.3f} | '
          f'WR: obs {100*obs_wr:.1f} vs null med {100*sorted(wrs)[iters//2]:.1f} → p={pw:.3f}')

FROZEN_K = 3  # S1: response + >=3 of 5 physics lenses (set after freq stage; see ledger)

if __name__ == '__main__':
    stage = sys.argv[1] if len(sys.argv) > 1 else 'freq'
    if stage == 'freq':
        for k in (2, 3, 4):
            freq_report([r for r in ROWS if s1_pass(r, k)], f'S1 VEXA-R (resp + >={k}/5)')
        freq_report([r for r in ROWS if s2_pass(r)], 'S2 TRIPTYCH')
        # S2 per-branch
        for reg in ['BULL', 'RANGE', 'BEAR']:
            n = sum(1 for r in ROWS if r['g_v5h'] == reg and s2_pass(r))
            print(f'  S2 branch {reg}: N={n}')
    elif stage == 'panel':
        s1 = [r for r in ROWS if s1_pass(r, FROZEN_K)]
        s2 = [r for r in ROWS if s2_pass(r)]
        panel(s1, f'S1 VEXA-R (resp + >={FROZEN_K}/5)'); null_check(s1, 'S1')
        panel(s2, 'S2 TRIPTYCH'); null_check(s2, 'S2')
        both = [r for r in ROWS if s1_pass(r, FROZEN_K) and s2_pass(r)]
        print(f'[S1∩S2] N={len(both)}')
