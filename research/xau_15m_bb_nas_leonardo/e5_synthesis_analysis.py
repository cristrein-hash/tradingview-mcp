#!/usr/bin/env python3
"""
E5 OPEN SYNTHESIS — deterministic calibration aggregation across the 61 MON+FORTE
bottoms vs 144 MED/FRACO control. Multi-factorial convergence (not single-axis),
trajectory features included, dual objective (recall of 61 AND specificity vs control).
CALIBRATION on the 61/144 curated dossiers, NOT validation. SANITY_PROBE / descriptive.
Run from research/xau_15m_bb_nas_leonardo/.
"""
import json
from statistics import median

def load(fn): return [json.loads(l) for l in open(fn)]
mon = load('dossier_monforte.jsonl')
con = load('dossier_control.jsonl')

def g(d, *p, default=None):
    cur = d
    for k in p:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(k)
    return cur if cur is not None else default

# ---------- trajectory shape helpers (from reaction_seq, post-low closed bars) ----------
def monotone_run(d):
    seq = g(d, 'reaction_seq', default=[])
    if len(seq) < 2: return 0
    run = 0
    for w in range(1, min(5, len(seq))):
        if seq[w]['l_atr'] > seq[w-1]['l_atr']: run += 1
        else: break
    return run

def maxc_by4(d):
    seq = g(d, 'reaction_seq', default=[])
    if len(seq) < 4: return None
    return max(seq[w]['c_atr'] for w in range(4))

# ---------- predicate set (as-of entry, SHIFT-safe per angle defs) ----------
def P_htf1_bull(d):    return g(d, 'htf1_native', 'trend') == 1
def P_htf1_room(d):    return g(d, 'htf1_native', 'in_demand') == 0
def P_offkz(d):        return g(d, 'features_E1', 'killzone') == 0
def P_calm(d):
    v = g(d, 'features_E1', 'atr_regime'); return v is not None and v < 1.0
def P_quietsell(d):
    v = g(d, 'features_E1', 'sell_bub_w'); return v is not None and v <= 2
def P_shallowsweep(d):
    v = g(d, 'features_E1', 'sweep_depth_atr'); return v is not None and v < 1.8
def P_grindleg(d):
    v = g(d, 'features_E1', 'downleg_eff'); return v is not None and v < 0.30
def P_h1pos(d):
    v = g(d, 'features_E1', 'h1_pos'); return v is not None and v >= 0.10
def P_nobreak(d):
    v = g(d, 'features_E1', 'dealing_range_pos'); return v is not None and v > -1.0
def P_notdeepOS(d):
    v = g(d, 'features_E1', 'rsi_min8'); return v is not None and v >= 30
def P_choch(d):        return g(d, 'entry_mechanics', 'choch_15m_after') == 1
def P_fastreclaim(d):
    v = g(d, 'entry_mechanics', 'reclaim_ema_bars'); return v is not None and v <= 3
def P_h1rsi_strong(d):
    v = g(d, 'htf1_native', 'rsi'); return v is not None and v >= 52

def rate(group, fn):
    vals = [fn(d) for d in group]
    fired = sum(1 for v in vals if v)
    return fired, len(vals)

def report(label, fn):
    mf, mn = rate(mon, fn); cf, cn = rate(con, fn)
    mr = mf/mn; cr = cf/cn
    print(f"{label:42s} MON {mf:2d}/{mn}={mr:4.0%}  CON {cf:3d}/{cn}={cr:4.0%}  lift {mr/(cr+1e-9):4.2f}")
    return mr, cr

PREDS = {
    'htf1_bull (1H trend +1)': P_htf1_bull,
    'htf1_room (1H above demand)': P_htf1_room,
    'off_killzone': P_offkz,
    'calm_regime (atr_regime<1.0)': P_calm,
    'quiet_sell (sell_bub_w<=2)': P_quietsell,
    'shallow_sweep (<1.8 ATR)': P_shallowsweep,
    'grind_leg (downleg_eff<0.30)': P_grindleg,
    'h1_pos>=0.10': P_h1pos,
    'no_range_break (drp>-1)': P_nobreak,
    'not_deep_OS (rsi_min8>=30)': P_notdeepOS,
    'choch_15m_after': P_choch,
    'fast_reclaim (ema<=3 bars)': P_fastreclaim,
    'h1_rsi_strong (>=52)': P_h1rsi_strong,
}

if __name__ == '__main__':
    print(f"MON n={len(mon)}  CON n={len(con)}\n")
    print("=== SINGLE PREDICATE recall vs specificity ===")
    for lab, fn in PREDS.items():
        report(lab, fn)

    print("\n=== CONVERGENCE: count of N core predicates fired ===")
    # core convergent stack (orthogonal: regime / cross-TF / liquidity / structure)
    core = [P_calm, P_htf1_bull, P_quietsell, P_grindleg, P_h1pos, P_offkz, P_nobreak]
    def nfired(d): return sum(1 for p in core if p(d))
    for thr in range(0, 8):
        mf = sum(1 for d in mon if nfired(d) >= thr)
        cf = sum(1 for d in con if nfired(d) >= thr)
        mr = mf/len(mon); cr = cf/len(con)
        print(f"  >= {thr}/7 core   MON {mf:2d}/{len(mon)}={mr:4.0%}  CON {cf:3d}/{len(con)}={cr:4.0%}  lift {mr/(cr+1e-9):4.2f}")

    print("\n=== CANDIDATE RULES (2-of-3 / AND combos) ===")
    rules = {
      'R1 REGIME-ONSET: calm AND htf1_bull AND h1_pos>=.1':
          lambda d: P_calm(d) and P_htf1_bull(d) and P_h1pos(d),
      'R2 QUIET-LIQUIDITY: off_kz AND quiet_sell AND shallow_sweep':
          lambda d: P_offkz(d) and P_quietsell(d) and P_shallowsweep(d),
      'R3 ABSORPTION: grind_leg AND calm AND quiet_sell':
          lambda d: P_grindleg(d) and P_calm(d) and P_quietsell(d),
      'R4 CROSS-TF SPRING: htf1_bull AND htf1_room AND h1_pos>=.1':
          lambda d: P_htf1_bull(d) and P_htf1_room(d) and P_h1pos(d),
      'R5 DISCOUNT-NOBREAK: no_break AND off_kz AND not_deep_OS':
          lambda d: P_nobreak(d) and P_offkz(d) and P_notdeepOS(d),
      'R6 2of3{calm,htf1_bull,quiet_sell}':
          lambda d: sum([P_calm(d),P_htf1_bull(d),P_quietsell(d)])>=2,
      'R7 2of3{calm,off_kz,grind_leg}':
          lambda d: sum([P_calm(d),P_offkz(d),P_grindleg(d)])>=2,
      'R8 3of4{calm,htf1_bull,quiet_sell,off_kz}':
          lambda d: sum([P_calm(d),P_htf1_bull(d),P_quietsell(d),P_offkz(d)])>=3,
    }
    for lab, fn in rules.items():
        report(lab, fn)

    print("\n=== R-DEMANDSTACK (family A) + union with CONV4 ===")
    def R_ds(d):
        cs = g(d, 'htf4_native', 'clean_sky_atr')
        return (g(d, 'htf4_native', 'in_demand') == 1 and
                g(d, 'htf1_native', 'trend') == 1 and
                cs is not None and cs < 0.5)
    report('R-DEMANDSTACK: 4H in_demand AND htf1_bull AND h4 clean_sky<0.5', R_ds)
    def conv4(d): return nfired(d) >= 4
    miss = [d for d in mon if not conv4(d)]
    recov = sum(1 for d in miss if R_ds(d))
    print(f"  CONV4 misses {len(miss)}/61; DEMANDSTACK recovers {recov}")
    report('UNION CONV4 OR DEMANDSTACK', lambda d: conv4(d) or R_ds(d))
