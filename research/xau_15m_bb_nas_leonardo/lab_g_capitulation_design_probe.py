#!/usr/bin/env python3
"""LAB G — Capitulation-physics designer: PROBE stage (features only, no outcome).

Reproducible probe used to design the capitulation entry systems.
Reads results/lab_g_candidates.jsonl. Prints regime-conditional quantiles,
lens overlap structure, weekly frequency scaffolding.
NO g_R usage in this file (design stage is outcome-blind by protocol).
"""
import json, collections, statistics, itertools, os

HERE = os.path.dirname(os.path.abspath(__file__))
ROWS = [json.loads(l) for l in open(os.path.join(HERE, 'results/lab_g_candidates.jsonl'))]


def qs(f, sub):
    vals = sorted(r[f] for r in sub if r.get(f) is not None)
    n = len(vals)
    if not n:
        return 'EMPTY'
    def q(p):
        return vals[min(n - 1, int(p * n))]
    return f'q25={q(.25):.3g} q50={q(.5):.3g} q75={q(.75):.3g} q90={q(.9):.3g}'


def main():
    rows = ROWS
    for reg in ['RANGE', 'BULL', 'BEAR']:
        sub = [r for r in rows if r['g_v5h'] == reg]
        print(f'--- {reg} n={len(sub)}')
        for f in ['g_box96', 'g_box480', 'g_atr_spike', 'g_sweep_depth', 'rsi_min8',
                  'g_flush_wick', 'g_rec_speed', 'g_ema21_dist', 'g_ema50_dist', 'h1_pos',
                  'pullback_depth', 'g_downrun', 'downleg_eff', 'reclaim_atr']:
            print(f'  {f}: {qs(f, sub)}')
        print('  swept:', sum(r['swept_prior_low'] for r in sub) / len(sub),
              ' sellbub>0:', sum(1 for r in sub if r['sell_bub_w'] > 0) / len(sub),
              ' rsi_div:', sum(r['g_rsi_div'] for r in sub) / len(sub),
              ' decel:', sum(r['downleg_decel'] for r in sub) / len(sub),
              ' knife:', sum(r['g_knife'] for r in sub) / len(sub),
              ' in_demand:', sum(r['in_demand'] for r in sub) / len(sub),
              ' htf_dem:', sum(r['htf_demand_any'] for r in sub) / len(sub))

    wk = collections.defaultdict(collections.Counter)
    for r in rows:
        wk[r['g_week']][r['g_v5h']] += 1
    print('weeks total', len(wk), collections.Counter(c.most_common(1)[0][0] for c in wk.values()))

    ts = sorted(r['t'] for r in rows)
    gaps = [b - a for a, b in zip(ts, ts[1:])]
    print('median gap (min):', statistics.median(gaps) / 60,
          'frac gap<2h:', sum(1 for g in gaps if g < 7200) / len(gaps))

    bp = [r for r in rows if r['g_bear_pullback_ok'] == 1]
    print('bear_pullback_ok n=', len(bp), collections.Counter(r['g_v5h'] for r in bp))

    def lens(r):
        return {
            'viol': r['g_atr_spike'] >= 1.27 or r['g_downrun'] >= 3,
            'exh_rsi': r['rsi_min8'] <= 33 or r['g_rsi_div'] == 1,
            'wick': r['g_flush_wick'] >= 0.55,
            'sweepd': r['swept_prior_low'] == 1 and r['g_sweep_depth'] >= 1.0,
            'absorb': r['sell_bub_w'] >= 1,
            'resp': r['g_rec_speed'] >= 0.69 or r['reclaim_atr'] >= 2.0,
        }
    L = [lens(r) for r in rows]
    keys = list(L[0])
    for k in keys:
        print(k, sum(l[k] for l in L) / len(L))
    for a, b in itertools.combinations(keys, 2):
        pa = sum(l[a] for l in L) / len(L)
        pb = sum(l[b] for l in L) / len(L)
        pab = sum(l[a] and l[b] for l in L) / len(L)
        print(f'{a}&{b}: joint={pab:.3f} indep={pa*pb:.3f} lift={pab/(pa*pb):.2f}')
    print('score dist', sorted(collections.Counter(sum(l.values()) for l in L).items()))


if __name__ == '__main__':
    main()
