#!/usr/bin/env python3
"""
FLOW / INDICATOR-CONFLUENCE contextual reader — threshold calibration + convergence scan.

PURPOSE (calibration, NOT validation; NOT R computation):
  Inspect distributions and cross flow/confluence features vs the FORWARD bottom-quality
  labels to (a) pick thresholds and (b) discover which CONVERGENCES separate strong/any
  bottoms from the falling-knife / NONE substrate. R is measured by the deterministic
  harness elsewhere — this only proposes/inspects the lenses.

DATA: entry_candidates_htf.jsonl (4502 knife-gated fractal-low entries, let-run).
LABELS (forward, calibration-only): MONSTRO+FORTE=58 strong, FRACO=79 weak, is_bottom=197.

KEY CONTEXT (project_xau_15m_bottom_power_engine + reference_bubbles_auction_theory):
  - strong-bottom fingerprint = SHALLOW + CONTROLLED + NON-exhausted pullback.
  - bubble-SELL at low = buyer absorption (regime-dependent: helps post-correction, not
    in strong uptrend where it = distribution).
  - 2026 = bear, LONG weak.
"""
import json
from collections import Counter

PATH = 'entry_candidates_htf.jsonl'
rows = [json.loads(l) for l in open(PATH)]
N = len(rows)

STRONG = lambda r: r['label'] in ('MONSTRO', 'FORTE')   # 58
WEAK   = lambda r: r['label'] == 'FRACO'                 # 79
BOTTOM = lambda r: r['is_bottom'] == 1                   # 197 (any-power true bottom)
NONE   = lambda r: r['label'] == 'NONE'                  # 4305 non-bottom (knife substrate)

bS, bB, bW = 58 / N, 197 / N, 79 / N


def rate(pred, group, pool=None):
    sub = [r for r in (pool or rows) if pred(r)]
    if not sub:
        return (0, 0, 0.0)
    g = sum(1 for r in sub if group(r))
    return (g, len(sub), g / len(sub))


def line(name, pred):
    n = sum(1 for r in rows if pred(r))
    if n == 0:
        print(f"{name:42s}     0")
        return
    _, _, rs = rate(pred, STRONG)
    _, _, rb = rate(pred, BOTTOM)
    _, _, rw = rate(pred, WEAK)
    print(f"{name:42s} {n:5d} {100*n/N:3.0f}% | str {100*rs:5.2f} {rs/bS:4.2f}x"
          f" | bot {100*rb:5.2f} {rb/bB:4.2f}x | weak {100*rw:5.2f} {rw/bW:4.2f}x")


def header():
    print(f"BASE: strong(MON+FORTE)={bS:.4f}  bottom={bB:.4f}  weak={bW:.4f}  N={N}\n")
    print("Counts:", Counter(r['label'] for r in rows),
          "falling_knife=", Counter(r['falling_knife'] for r in rows),
          "yr=", Counter(r['yr'] for r in rows), "\n")


# ---- helper sub-states (orthogonal voices) ----
def absorption(r):      # bubble-SELL dominance at the low = buyer absorption
    return r['sell_bub_w'] >= 8 and r['sell_bub_w'] > r['buy_bub_w']
def exhaust_anti(r):    # buy-bubble at low = exhaustion (anti-pattern)
    return r['buy_bub_w'] >= 8
def nas_voice(r):       # NAS reaction-probability confluence
    return r['nas_long_16'] >= 2 or r['h4n_nas_long_rec'] >= 1
def capit_flush(r):     # capitulation flush done: deep OS + climax vol + sweep
    return r['rsi_min8'] < 30 and r['atr_regime'] > 1.3 and r['swept_prior_low'] == 1
def snap_reclaim(r):    # strong V snap-back off the low
    return r['reclaim_atr'] >= 2.0
def htf_floor(r):       # HTF demand under price
    return r['htf_demand_confluence'] == 1 or r['h4n_in_demand'] == 1


# ---- improved FALLING-KNIFE filter (multi-condition) ----
# A knife = accelerating decline into NO reaction and NO floor.
# Exclude when: weak snap-back AND not-swept (no liquidity grab) AND flush downleg
#               AND no absorption AND below HTF demand.
def knife_v2(r):
    no_react = r['reclaim_atr'] < 1.0 and r['up_closes_pc'] <= 1
    flush = r['downleg_eff'] >= 0.45            # straight-down, efficient decline
    no_absorb = r['sell_bub_w'] < 8
    no_sweep = r['swept_prior_low'] == 0        # falling without grabbing liquidity
    no_floor = r['htf_demand_any'] == 0
    # require accelerating/uncontrolled context too
    hot = r['atr_regime'] > 1.2
    return flush and hot and no_react and (no_absorb or no_floor or no_sweep)


if __name__ == '__main__':
    header()
    print("=== SINGLE-CONDITION CALIBRATION (threshold inspection only) ===")
    singles = {
        'sell_bub_w>=8': lambda r: r['sell_bub_w'] >= 8,
        'buy_bub_w>=8 (anti)': lambda r: r['buy_bub_w'] >= 8,
        'sell>buy bub': lambda r: r['sell_bub_w'] > r['buy_bub_w'],
        'nas_long_16>=2': lambda r: r['nas_long_16'] >= 2,
        'h4n_nas_long_rec>=1': lambda r: r['h4n_nas_long_rec'] >= 1,
        'rsi_min8<28 (deep OS)': lambda r: r['rsi_min8'] < 28,
        'reclaim_atr>=2.0': lambda r: r['reclaim_atr'] >= 2.0,
        'downleg_eff>=0.45 (flush)': lambda r: r['downleg_eff'] >= 0.45,
        'atr_regime>1.6 (climax)': lambda r: r['atr_regime'] > 1.6,
        'h1_pos<=0.2 (deep)': lambda r: r['h1_pos'] <= 0.2,
        'swept_prior_low=1': lambda r: r['swept_prior_low'] == 1,
        'htf_demand_confl=1': lambda r: r['htf_demand_confluence'] == 1,
    }
    for nm, p in singles.items():
        line(nm, p)

    print("\n=== ORTHOGONAL VOICES (each a sub-state) ===")
    voices = {
        'V_absorb (sell_bub>=8 & >buy)': absorption,
        'V_nas (nas16>=2 | h4nNAS>=1)': nas_voice,
        'V_capit (rsi<30 & atrhot & swept)': capit_flush,
        'V_snap (reclaim>=2.0)': snap_reclaim,
        'V_htf (demand_confl | h4n_demand)': htf_floor,
        'V_exhaust_ANTI (buy_bub>=8)': exhaust_anti,
    }
    for nm, p in voices.items():
        line(nm, p)

    print("\n=== CONVERGENCE: k-of-voices {absorb, nas, snap, capit} ===")
    base4 = [absorption, nas_voice, snap_reclaim, capit_flush]
    for k in (1, 2, 3):
        pred = (lambda kk: (lambda r: sum(v(r) for v in base4) >= kk))(k)
        line(f'>= {k} of 4 voices', pred)

    print("\n=== CONVERGENCE PAIRS / TRIPLES (capitulation-done reading) ===")
    combos = {
        'absorb & snap': lambda r: absorption(r) and snap_reclaim(r),
        'capit & snap (flush+reclaim)': lambda r: capit_flush(r) and snap_reclaim(r),
        'absorb & nas': lambda r: absorption(r) and nas_voice(r),
        'absorb & snap & nas': lambda r: absorption(r) and snap_reclaim(r) and nas_voice(r),
        'capit & snap & absorb': lambda r: capit_flush(r) and snap_reclaim(r) and absorption(r),
        '(absorb|capit) & snap & !exhaust':
            lambda r: (absorption(r) or capit_flush(r)) and snap_reclaim(r) and not exhaust_anti(r),
    }
    for nm, p in combos.items():
        line(nm, p)

    print("\n=== IMPROVED FALLING-KNIFE FILTER (knife_v2) ===")
    nk = sum(1 for r in rows if knife_v2(r))
    print(f"knife_v2 flags {nk} ({100*nk/N:.1f}% of pool)  vs existing falling_knife=17")
    line('knife_v2 (REMOVE these)', knife_v2)
    # what remains after removing knives:
    keep = [r for r in rows if not knife_v2(r)]
    gs = sum(1 for r in keep if STRONG(r)); gb = sum(1 for r in keep if BOTTOM(r))
    print(f"AFTER removing knife_v2: kept={len(keep)}  strong kept={gs}/58  bottom kept={gb}/197")

    print("\n=== knife_v2 ENRICHMENT among NONE (should over-target NONE) ===")
    knsub = [r for r in rows if knife_v2(r)]
    if knsub:
        non = sum(1 for r in knsub if NONE(r))
        print(f"of {len(knsub)} knife_v2: NONE={non} ({100*non/len(knsub):.1f}%), "
              f"bottom={sum(1 for r in knsub if BOTTOM(r))}, strong={sum(1 for r in knsub if STRONG(r))}")

    print("\n=== PER-YEAR robustness of top convergence (capit&snap) ===")
    top = lambda r: capit_flush(r) and snap_reclaim(r)
    for yr in (2024, 2025, 2026):
        pool = [r for r in rows if r['yr'] == yr]
        _, n, rb = rate(top, BOTTOM, pool)
        bbase = sum(1 for r in pool if BOTTOM(r)) / len(pool)
        print(f"  {yr}: n={n} bottom%={100*rb:.1f} (base {100*bbase:.1f}) "
              f"lift={rb/bbase if bbase else 0:.2f}x")
