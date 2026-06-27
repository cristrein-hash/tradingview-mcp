"""_reopt5_stack_flow.py — anchor (R2 h1-positioning) + structure->flow lens add-ons.

Tests whether adding gentle structure->flow CUTS to the robust positioning anchor
improves WR/streak while holding winners_kept>=85.

Anchor R2 = keep(h1_pos>=0.66) i.e. CUT(h1_pos<=0.65)  [robust single, WR61.97 8/8]
Anchor R2+ = CUT(h1_pos<=0.65) OR CUT(h1_dist<=1.85)   [robust pair, WR62.92]

Lens add-on CUTS (loser-dense, gentle):
  cut naslong_after_smc==1   (WR48.2 n114)
  cut smc_bos>=4             (WR<=48.5, tiny n)
Also test R_B flow: cut sell_skew_mig>=1, cut absorption==1.
PROHIBITED: R/win/cj/low_idx/block/low_t/yr.
"""
import _reopt5_lib as L

# CUT predicates (row removed if any True). keep = not any.
CUT = {
 'h1_pos<=0.65':   lambda r: r['h1_pos'] is not None and r['h1_pos'] <= 0.65,
 'h1_dist<=1.85':  lambda r: r['h1_dist'] is not None and r['h1_dist'] <= 1.85,
 'naslong==1':     lambda r: r['naslong_after_smc'] == 1,
 'smc_bos>=4':     lambda r: r['smc_bos'] >= 4,
 'skew>=1':        lambda r: r['sell_skew_mig'] is not None and r['sell_skew_mig'] >= 1,
 'absorption==1':  lambda r: r['absorption'] == 1,
 'into_supply':    lambda r: r['dist_supply_atr'] is not None and r['dist_supply_atr'] <= -0.26,
 'hd_eff<=0.12':   lambda r: r['hd_eff'] is not None and r['hd_eff'] <= 0.12,
}


def stk(rows, cuts):
    fns = [CUT[c] for c in cuts]
    kept = [r for r in rows if not any(f(r) for f in fns)]
    return L.report('CUT(' + ' OR '.join(cuts) + ')', kept, rows)


def main():
    rows = L.load()
    res = []
    A = ['h1_pos<=0.65']
    AB = ['h1_pos<=0.65', 'h1_dist<=1.85']
    # anchor + single lens add
    for add in ['naslong==1','smc_bos>=4','skew>=1','absorption==1','into_supply','hd_eff<=0.12']:
        res.append(stk(rows, A + [add]))
    # anchor pair + lens add
    for add in ['naslong==1','smc_bos>=4','into_supply']:
        res.append(stk(rows, AB + [add]))
    # flow-only orthogonal pair to compare
    res.append(stk(rows, ['naslong==1','smc_bos>=4','into_supply']))
    # best positioning + supply (orthogonal location)
    res.append(stk(rows, ['h1_pos<=0.65','into_supply']))
    res.append(stk(rows, ['h1_dist<=1.85','into_supply']))

    print('\n\n==== ROBUST (sorted by streak then wr) ====')
    rob = [m for m in res if m and m['robust']]
    for m in sorted(rob, key=lambda m: (m['streak_keep'], -m['wr_keep'])):
        print(f"  {m['name']:<48} WR={m['wr_keep']} n={m['n_keep']} "
              f"winK={m['winners_kept_pct']}% losC={m['losers_cut_pct']}% "
              f"streak{m['streak_base']}->{m['streak_keep']} blk{m['blocks_ok']}/8 "
              f"yr({m['by_year'][2024]},{m['by_year'][2025]},{m['by_year'][2026]})")
    if not rob:
        print('  none robust')


if __name__ == '__main__':
    main()
