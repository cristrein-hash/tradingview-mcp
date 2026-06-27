#!/usr/bin/env python3
"""
_reopt5_univar.py — univariate threshold scan, MULTI-TF lens first.
For each numeric feature, scan keep-when-(>=t) and keep-when-(<=t) cuts;
report best lift over base while keeping >=70% of rows (loose at univariate stage).
NULL POLICY: a row with null on the scanned feature is treated as FAIL the
condition (i.e. excluded from KEEP) — conservative; we record null behaviour.
Goal axis R2 (multi-TF eff/pos): loser = 15M no drive + HTF range/topo.
"""
import json

ROWS = [json.loads(l) for l in open('dataset_5atr.jsonl')]
N = len(ROWS)
BASE_WR = sum(r['win'] for r in ROWS) / N
TOT_WIN = sum(r['win'] for r in ROWS)


def evalmask(mask):
    keep = [r for r in ROWS if mask(r)]
    if not keep:
        return None
    nk = len(keep)
    wk = sum(r['win'] for r in keep)
    return dict(n=nk, wr=wk/nk, wkept=wk/TOT_WIN, dn=nk/N)


def scan(name, lo, hi, steps=20):
    out = []
    for i in range(steps + 1):
        t = lo + (hi - lo) * i / steps
        for op, fn in [('>=', lambda r, t=t: r[name] is not None and r[name] >= t),
                       ('<=', lambda r, t=t: r[name] is not None and r[name] <= t)]:
            res = evalmask(fn)
            if res and res['dn'] >= 0.5:  # keep at least half
                out.append((res['wr'], name, op, round(t, 3), res))
    out.sort(reverse=True)
    return out[:3]


# multi-TF focus features + thresholds inferred from quantiles
SCANS = [
    ('h1_eff', 0.0, 0.8), ('h4_eff', 0.0, 0.8), ('hd_eff', 0.0, 0.8),
    ('h1_pos', 0.5, 1.5), ('h4_pos', 0.3, 1.2), ('hd_pos', 0.3, 1.2),
    ('h1_dist', -2, 8), ('h4_dist', -2, 12), ('hd_dist', -5, 25),
    ('path_eff', 0.05, 1.0), ('disp4_atr', 0, 5), ('macro_drop_atr', 1, 20),
    ('macro_retr', 0.2, 1.5), ('rsi', 40, 85), ('rsi_low', 20, 70),
    ('regime_age_h', 0, 120), ('vpnode_dist_atr', 0, 8), ('atr_regime', 0.5, 2),
    ('dist_demand_atr', -0.3, 3), ('bars_to_base', 1, 150),
]

if __name__ == '__main__':
    print(f"BASE_WR={BASE_WR:.4f} N={N}")
    print("\n=== TOP univariate cuts (multi-TF + context) ===")
    for name, lo, hi in SCANS:
        top = scan(name, lo, hi)
        for wr, nm, op, t, res in top:
            flag = '*' if wr > BASE_WR else ' '
            print(f"{flag} {nm:16s} {op} {t:7.3f}  WR={wr:.4f} n={res['n']:4d} "
                  f"wkept={res['wkept']:.3f} keepN={res['dn']:.3f}")

    # binary / categorical features
    print("\n=== binary/cat single-value WR ===")
    for name in ['h1_trend', 'h4_trend', 'hd_trend', 'macro_bull', 'macro_bear',
                 'in_demand', 'demand_fresh', 'killzone', 'is_london_open',
                 'is_ny_overlap', 'is_deadzone', 'absorption', 'buy_after_smc',
                 'naslong_after_smc', 'buy_L_recent', 'smc_bos', 'flow_accel']:
        vals = sorted(set(r[name] for r in ROWS if r[name] is not None))
        if len(vals) > 8:
            continue
        for v in vals:
            sub = [r for r in ROWS if r[name] == v]
            if len(sub) < 100:
                continue
            wr = sum(x['win'] for x in sub) / len(sub)
            flag = '*' if wr > BASE_WR else ' '
            print(f"{flag} {name:16s} =={v}  WR={wr:.4f} n={len(sub):4d}")
