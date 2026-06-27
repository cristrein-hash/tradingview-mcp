"""_reopt5_lens_flow.py — structure->flow lens.

Lens features: smc_lag_bars, buy_after_smc, naslong_after_smc, smc_bos,
bars_since_sell. Idea: confirmation that the 5ATR impulse is backed by a recent
structural break (smc_bos / low smc_lag_bars) AND fresh flow (buy_after_smc,
naslong_after_smc=continuation, bars_since_sell large = sell exhausted).

Step 1: tabulate WR by value for each lens feature (incl distribution).
Step 2: build 2-3 feature combos within the lens and report robustness.
PROHIBITED: R/win/cj/low_idx/block/low_t/yr as features.
"""
import _reopt5_lib as L
import collections

LENS = ['smc_lag_bars','buy_after_smc','naslong_after_smc','smc_bos','bars_since_sell']


def tab(rows, f, bins=None):
    print(f'--- {f} ---')
    if bins is None:
        d = collections.defaultdict(list)
        for r in rows:
            d[r.get(f)].append(r)
        for k in sorted(d, key=lambda x: (x is None, x)):
            v = d[k]
            wr = 100*sum(r['win'] for r in v)/len(v)
            print(f'  {f}={k}: n={len(v)} WR={wr:.1f} avgR={sum(r["R"] for r in v)/len(v):.3f}')
    else:
        for lo, hi in bins:
            v = [r for r in rows if r.get(f) is not None and lo <= r[f] < hi]
            if not v:
                continue
            wr = 100*sum(r['win'] for r in v)/len(v)
            print(f'  {f} in [{lo},{hi}): n={len(v)} WR={wr:.1f} avgR={sum(r["R"] for r in v)/len(v):.3f}')


def main():
    rows = L.load()
    tab(rows, 'smc_bos')
    tab(rows, 'buy_after_smc')
    tab(rows, 'naslong_after_smc')
    tab(rows, 'smc_lag_bars', bins=[(0,3),(3,6),(6,12),(12,24),(24,1000)])
    tab(rows, 'bars_since_sell', bins=[(0,5),(5,10),(10,20),(20,40),(40,1000)])


if __name__ == '__main__':
    main()
