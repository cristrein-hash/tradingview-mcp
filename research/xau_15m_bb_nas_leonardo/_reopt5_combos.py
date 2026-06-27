"""_reopt5_combos.py — combo search + re-test of 8ATR-calibrated filters for 5ATR.

 (A) Re-test 8ATR filters on 5ATR:
     R2 = multi-TF eff/pos quality
     R_B = sell-exhaustion-in-overheating
 (B) Lens combos (structure->flow)
 reported via L.report; robust summary at end.

All filters are KEEP predicates. CUT-when-loser-dense = NOT(loser condition).
PROHIBITED: R/win/cj/low_idx/block/low_t/yr.
"""
import _reopt5_lib as L


def show(name, rows, fn):
    return L.report(name, [r for r in rows if fn(r)], rows)


def main():
    rows = L.load()
    res = []

    # ---------- (A) 8ATR filters re-tested ----------
    res.append(show('R2a h1_pos>=0.68 (multiTF-pos)', rows,
                    lambda r: r['h1_pos'] is not None and r['h1_pos'] >= 0.68))
    res.append(show('R2b h1_pos>=0.54 & h1_eff>=0', rows,
                    lambda r: r['h1_pos'] is not None and r['h1_pos'] >= 0.54
                              and r['h1_eff'] is not None and r['h1_eff'] >= 0.0))
    res.append(show('R_Ba rsi>=53 & bars_since_sell>=20', rows,
                    lambda r: r['rsi'] is not None and r['rsi'] >= 53 and r['bars_since_sell'] >= 20))
    res.append(show('R_Bb rsi>=47.7 & sell_skew_mig<=0.43', rows,
                    lambda r: r['rsi'] >= 47.7 and r['sell_skew_mig'] <= 0.43))

    # ---------- (B) structure->flow lens combos ----------
    res.append(show('Lns1 smc_bos<=1', rows, lambda r: r['smc_bos'] <= 1))
    res.append(show('Lns2 smc_bos<=1 & naslong_after_smc==0', rows,
                    lambda r: r['smc_bos'] <= 1 and r['naslong_after_smc'] == 0))
    res.append(show('Lns3 smc_bos<=1 & h1_pos>=0.54', rows,
                    lambda r: r['smc_bos'] <= 1 and r['h1_pos'] is not None and r['h1_pos'] >= 0.54))
    res.append(show('Lns4 buy_after_smc==1 & naslong_after_smc==0', rows,
                    lambda r: r['buy_after_smc'] == 1 and r['naslong_after_smc'] == 0))
    res.append(show('Lns5 buy_after_smc==1 & h1_pos>=0.54', rows,
                    lambda r: r['buy_after_smc'] == 1 and r['h1_pos'] is not None and r['h1_pos'] >= 0.54))
    res.append(show('Lns6 naslong_after_smc==0 & smc_bos<=1 & h1_pos>=0.54', rows,
                    lambda r: r['naslong_after_smc'] == 0 and r['smc_bos'] <= 1
                              and r['h1_pos'] is not None and r['h1_pos'] >= 0.54))

    print('\n\n==== ROBUST SUMMARY ====')
    for m in res:
        if m and m['robust']:
            print(' ', m['name'], '| WR', m['wr_keep'], 'winK', m['winners_kept_pct'],
                  'losC', m['losers_cut_pct'], 'streak', m['streak_base'], '->', m['streak_keep'],
                  'blk', m['blocks_ok'])


if __name__ == '__main__':
    main()
