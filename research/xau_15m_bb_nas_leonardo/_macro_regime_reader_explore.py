#!/usr/bin/env python3
"""
Macro/Regime contextual reader — EXPLORATION ONLY (distributions to set thresholds).
NOT an R evaluator. Proposes convergent macro-context qualification rules whose
R must be measured by the deterministic harness.

Paradigm: risk-shaping of the 4502 knife-gated fractal-low universe, NOT label isolation.
label-rate is shown only as a weak structural co-signal (label != R, precision wall ~6%).
We mainly characterize: coverage, knife-density, year mix, and continuous HTF geometry,
to define sensible thresholds for convergent (2-4 condition) macro contexts.
"""
import json
from collections import defaultdict, Counter

ROWS = [json.loads(l) for l in open(
    '/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo/entry_candidates_htf.jsonl')]
N = len(ROWS)


def pct(vals, ps=(5, 25, 50, 75, 95)):
    v = sorted(x for x in vals if x is not None)
    if not v:
        return {}
    return {p: round(v[min(len(v) - 1, int(p / 100 * len(v)))], 3) for p in ps}


def q(r):   # weak structural quality co-signal
    return r['label'] in ('MONSTRO', 'FORTE')


def med(r):
    return r['label'] in ('MONSTRO', 'FORTE', 'MEDIO')


BASE_Q = sum(q(r) for r in ROWS) / N
BASE_MED = sum(med(r) for r in ROWS) / N


def report(name, pred):
    sub = [r for r in ROWS if pred(r)]
    if not sub:
        print(f'{name:60s} EMPTY')
        return
    n = len(sub)
    qr = sum(q(r) for r in sub) / n
    mr = sum(med(r) for r in sub) / n
    fk = sum(r['falling_knife'] for r in sub) / n
    yr = dict(sorted(Counter(r['yr'] for r in sub).items()))
    print(f'{name:60s} n={n:4d} ({n/N*100:4.1f}%) Q={qr:.4f}({qr/BASE_Q:4.2f}x) '
          f'med={mr:.4f}({mr/BASE_MED:4.2f}x) knife={fk:.4f} yr={yr}')


def main():
    print(f'N={N}  baseQ(MON+FORTE)={BASE_Q:.4f}  baseMed+={BASE_MED:.4f}')
    print('NOTE: label!=R. Q/med shown as weak structural co-signal only.\n')

    print('=== continuous HTF geometry distributions (p5/25/50/75/95) ===')
    for k in ['h4n_dist_demand_atr', 'h1n_dist_demand_atr', 'h4n_clean_sky_atr',
              'h1n_clean_sky_atr', 'h4n_rsi', 'h1n_rsi', 'h1_pos', 'h1_dist',
              'dist_demand_atr', 'clean_sky_atr', 'atr_regime', 'legpos60',
              'legpos90', 'rsi_min8', 'n_supply_overhead', 'n_demand_near']:
        print(f'  {k:24s}', pct([r.get(k) for r in ROWS]))
    print()

    print('=== SINGLE LENSES ===')
    report('h4n_trend==1', lambda r: r['h4n_trend'] == 1)
    report('h4n_trend==-1', lambda r: r['h4n_trend'] == -1)
    report('h1n_trend==1', lambda r: r['h1n_trend'] == 1)
    report('h4n_trend==1 & h1n_trend==1 (ALIGN up)',
           lambda r: r['h4n_trend'] == 1 and r['h1n_trend'] == 1)
    report('h4n_trend==-1 & h1n_trend==1 (4H pullback in 1D up)',
           lambda r: r['h4n_trend'] == -1 and r['h1n_trend'] == 1)
    report('h4n_choch_up_rec==1', lambda r: r['h4n_choch_up_rec'] == 1)
    report('h1n_choch_up_rec==1', lambda r: r['h1n_choch_up_rec'] == 1)
    print()

    print('=== CONVERGENT MACRO CONTEXTS (proposals to evaluate) ===')

    # R1: 1D-up regime-turn confirmed by 4H CHoCH-up onset, near demand
    report('R1 1Dup+4HCHoCHup+4Hdemand',
           lambda r: r['h1n_trend'] == 1 and r['h4n_choch_up_rec'] == 1
           and r['h4n_in_demand'] == 1)

    # R2: bull-leg-pullback — 1D up, 4H pullback (down), entry into 4H demand, not stretched
    report('R2 bull-leg-pullback (1Dup,4Hdown,4Hdemand,dist<=0.5)',
           lambda r: r['h1n_trend'] == 1 and r['h4n_trend'] == -1
           and r['h4n_in_demand'] == 1 and (r['h4n_dist_demand_atr'] or 9) <= 0.5)

    # R3: trend alignment up + room above (clean sky) + demand confluence
    report('R3 ALIGNup+cleansky4H>=1.0+demandconf',
           lambda r: r['h4n_trend'] == 1 and r['h1n_trend'] == 1
           and (r['h4n_clean_sky_atr'] or 0) >= 1.0
           and r['htf_demand_confluence'] == 1)

    # R4: regime-turn onset cross-TF (either-TF CHoCH up) + 1D not deep-bear + near demand
    report('R4 (4H|1D CHoCHup)+1Dup+near-demand(h4dist<=0.5)',
           lambda r: (r['h4n_choch_up_rec'] == 1 or r['h1n_choch_up_rec'] == 1)
           and r['h1n_trend'] == 1 and (r['h4n_dist_demand_atr'] or 9) <= 0.5)

    # R5: HTF demand reaction with NAS-long confirm (institutional bottom)
    report('R5 4Hdemand+NASlong>=1+1Dup',
           lambda r: r['h4n_in_demand'] == 1 and r['h4n_nas_long_rec'] >= 1
           and r['h1n_trend'] == 1)

    # R6: anti-knife exclusion — NOT(4H down & 1D down & far from demand & no choch)
    report('R6 NOT deep-bear-air (excl 4Hdn&1Ddn&h4dist>1&nochoch)',
           lambda r: not (r['h4n_trend'] == -1 and r['h1n_trend'] == -1
                          and (r['h4n_dist_demand_atr'] or 0) > 1.0
                          and r['h4n_choch_up_rec'] == 0))

    # R7: stretched-RSI overhead exclusion (avoid buying into resistance roof)
    report('R7 room above: h4n_clean_sky>=0.8 & h4n_rsi<55',
           lambda r: (r['h4n_clean_sky_atr'] or 0) >= 0.8 and (r['h4n_rsi'] or 99) < 55)

    print('\n=== KNIFE SIGNATURE (causal anti-knife) ===')
    knife_sig = lambda r: r['h4n_trend'] == -1 and r['h4n_in_demand'] == 0
    cap = sum(r['falling_knife'] for r in ROWS if knife_sig(r))
    tot = sum(r['falling_knife'] for r in ROWS)
    nsig = sum(knife_sig(r) for r in ROWS)
    print(f'  4Hdown & NOT-in-4Hdemand: n={nsig} captures {cap}/{tot} knives; '
          f'excluding -> {N-nsig} rows ({(N-nsig)/N*100:.1f}%), 0 knives')
    report('  KEEP = NOT knife_sig', lambda r: not knife_sig(r))

    print('\n=== FINAL CONVERGENT PROPOSALS (clean cohorts) ===')
    report('P-supported-pullback (1Dup & in-4Hdem & h4dist<=0.3)',
           lambda r: r['h1n_trend'] == 1 and r['h4n_in_demand'] == 1
           and (r['h4n_dist_demand_atr'] or 9) <= 0.3)
    report('P-supported+room (above & clean_sky4H>=0.5)',
           lambda r: r['h1n_trend'] == 1 and r['h4n_in_demand'] == 1
           and (r['h4n_dist_demand_atr'] or 9) <= 0.3
           and (r['h4n_clean_sky_atr'] or 0) >= 0.5)
    report('P-reclaimed-above-demand (in-dem & h4dist<=0)',
           lambda r: r['h4n_in_demand'] == 1 and (r['h4n_dist_demand_atr'] or 1) <= 0)


if __name__ == '__main__':
    main()
