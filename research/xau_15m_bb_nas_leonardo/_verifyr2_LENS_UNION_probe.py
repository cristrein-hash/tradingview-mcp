#!/usr/bin/env python3
"""DA supplementary probe for LENS UNION: effect size, OR-arm overlap, young-only baseline."""
import json
ROWS = [json.loads(l) for l in open('dataset_r2refine.jsonl')]
K = [r for r in ROWS if r['r2_keep'] == 1]


def cut(r, ta=24.0, tv=1.5):
    return r['regime_age_h'] < ta and (r['absorption'] == 1 or r['low_vol_rel'] >= tv)


def wr(s):
    return 100 * sum(x['win'] for x in s) / len(s) if s else 0


keep = [r for r in K if not cut(r)]
print('WR lift total: %.2f pp' % (wr(keep) - wr(K)))

a = [r for r in K if r['regime_age_h'] < 24 and r['absorption'] == 1]
b = [r for r in K if r['regime_age_h'] < 24 and r['low_vol_rel'] >= 1.5]
sa = set(r['low_t'] for r in a); sb = set(r['low_t'] for r in b)
print('young&absorb n%d  young&vol n%d  overlap %d  union %d'
      % (len(a), len(b), len(sa & sb), len(sa | sb)))

yall = [r for r in K if r['regime_age_h'] < 24]
keepy = [r for r in K if not (r['regime_age_h'] < 24)]
print('young-only cut: n_cut %d WR %.2f -> keep WR %.2f winners_kept %.1f%%'
      % (len(yall), wr(yall), wr(keepy), 100 * sum(r['win'] for r in keepy) / sum(r['win'] for r in K)))
