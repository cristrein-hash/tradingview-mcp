#!/usr/bin/env python3
"""
_engine_volsession.py
Lente: VOLATILIDADE / SESSAO / VOLUME.
Features de entrada (causais, no bar do reclaim): atr_regime, hour, killzone, vol_low_vs_med.
Alvo: R_reclaim (let-run, SL estrutural). Base avgR=+0.727, WR=45.4%, runner(R>=5)=6.5%.

REGRAS DURAS:
 - features ja causais; NAO usar near_M8/R_reclaim/R_8atr/held8/runner como FEATURE.
 - reportar n, WR, avgR e avgR por ano (2024/2025/2026).
 - robust = avgR>base nos 3 anos E n>=30 E nao-carregada-por-2-trades (ex-top2 ainda > base).
"""
import json
from itertools import combinations

ROWS = [json.loads(l) for l in open('entry_dataset.jsonl')]
BASE = 0.727


def stats(rs):
    n = len(rs)
    if n == 0:
        return dict(n=0, wr=0, avgr=0, run=0)
    R = [r['R_reclaim'] for r in rs]
    wr = sum(1 for x in R if x > 0) / n
    avg = sum(R) / n
    run = sum(1 for x in R if x >= 5) / n
    return dict(n=n, wr=round(wr*100, 1), avgr=round(avg, 3), run=round(run*100, 1))


def year_avgr(rs, y):
    yr = [r['R_reclaim'] for r in rs if r['yr'] == y]
    if not yr:
        return None, 0
    return round(sum(yr)/len(yr), 3), len(yr)


def extop2(rs):
    """avgR removendo as 2 maiores R (carregamento)."""
    if len(rs) <= 2:
        return None
    R = sorted((r['R_reclaim'] for r in rs), reverse=True)[2:]
    return round(sum(R)/len(R), 3)


def report(name, rs, verbose=True):
    s = stats(rs)
    if s['n'] == 0:
        return None
    y24, n24 = year_avgr(rs, 2024)
    y25, n25 = year_avgr(rs, 2025)
    y26, n26 = year_avgr(rs, 2026)
    ex2 = extop2(rs)
    sign_ok = all(x is not None and x > BASE for x in (y24, y25, y26))
    yearn_ok = all(c >= 8 for c in (n24, n25, n26))  # min per-year support
    robust = sign_ok and s['n'] >= 30 and (ex2 is not None and ex2 > BASE)
    lift = round(s['avgr'] - BASE, 3)
    if verbose:
        print(f"{name}")
        print(f"  n={s['n']} WR={s['wr']}% avgR={s['avgr']} run%={s['run']} lift={lift}")
        print(f"  y24={y24}(n{n24}) y25={y25}(n{n25}) y26={y26}(n{n26}) ex-top2={ex2}")
        print(f"  sign3yr_ok={sign_ok} yearn_ok={yearn_ok} robust={robust}")
    return dict(name=name, **s, y24=y24, y25=y25, y26=y26, n24=n24, n25=n25, n26=n26,
                ex2=ex2, lift=lift, robust=robust, sign_ok=sign_ok)


def main():
    print("="*70)
    print("BASE:", stats(ROWS))
    for y in (2024, 2025, 2026):
        print(" ", y, year_avgr(ROWS, y))
    print("="*70)

    results = []

    # ---- single-feature univariate scans ----
    # atr_regime bins
    print("\n### atr_regime thresholds ###")
    for thr in (0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.5):
        results.append(report(f"atr_regime<={thr}", [r for r in ROWS if r['atr_regime'] <= thr]))
        results.append(report(f"atr_regime>={thr}", [r for r in ROWS if r['atr_regime'] >= thr]))

    # vol_low_vs_med bins (volume climax at the low: HIGH vol_low_vs_med = climax)
    print("\n### vol_low_vs_med thresholds ###")
    for thr in (0.7, 0.9, 1.0, 1.1, 1.3, 1.5, 1.7, 2.0):
        results.append(report(f"vol_low_vs_med>={thr}", [r for r in ROWS if r['vol_low_vs_med'] >= thr]))
        results.append(report(f"vol_low_vs_med<={thr}", [r for r in ROWS if r['vol_low_vs_med'] <= thr]))

    # killzone
    print("\n### killzone ###")
    results.append(report("killzone==1", [r for r in ROWS if r['killzone'] == 1]))
    results.append(report("killzone==0", [r for r in ROWS if r['killzone'] == 0]))

    # hour buckets (sessions). UTC assumed.
    print("\n### hour session windows ###")
    sessions = {
        'asia(0-6)': lambda h: 0 <= h <= 6,
        'london(7-11)': lambda h: 7 <= h <= 11,
        'ny_am(12-16)': lambda h: 12 <= h <= 16,
        'ny_pm(17-20)': lambda h: 17 <= h <= 20,
        'late(21-23)': lambda h: 21 <= h <= 23,
        'london+nyam(7-16)': lambda h: 7 <= h <= 16,
        'ny_overlap(13-16)': lambda h: 13 <= h <= 16,
    }
    for nm, fn in sessions.items():
        results.append(report(f"hour {nm}", [r for r in ROWS if fn(r['hour'])]))

    # per-hour scan (find strong individual hours)
    print("\n### per-hour avgR (n>=80) ###")
    for h in range(24):
        sub = [r for r in ROWS if r['hour'] == h]
        if len(sub) >= 80:
            s = stats(sub)
            if s['avgr'] > BASE:
                report(f"hour=={h}", sub)

    # ---- 2-way combos within lens ----
    print("\n" + "="*70)
    print("### 2-way combos (lens-only) ###")
    combo_specs = {
        'klz1': lambda r: r['killzone'] == 1,
        'klz0': lambda r: r['killzone'] == 0,
        'atr_lo': lambda r: r['atr_regime'] <= 0.9,
        'atr_hi': lambda r: r['atr_regime'] >= 1.2,
        'vol_climax': lambda r: r['vol_low_vs_med'] >= 1.3,
        'vol_quiet': lambda r: r['vol_low_vs_med'] <= 0.9,
        'london': lambda r: 7 <= r['hour'] <= 11,
        'nyam': lambda r: 12 <= r['hour'] <= 16,
        'session_active(7-16)': lambda r: 7 <= r['hour'] <= 16,
        'asia': lambda r: 0 <= r['hour'] <= 6,
    }
    for a, b in combinations(combo_specs, 2):
        fa, fb = combo_specs[a], combo_specs[b]
        sub = [r for r in ROWS if fa(r) and fb(r)]
        if len(sub) >= 30:
            res = report(f"{a} & {b}", sub, verbose=False)
            if res and res['avgr'] > BASE + 0.15:
                report(f"{a} & {b}", sub)

    # ---- 3-way promising combos ----
    print("\n" + "="*70)
    print("### 3-way combos (lens-only) ###")
    for a, b, c in combinations(combo_specs, 3):
        fs = [combo_specs[a], combo_specs[b], combo_specs[c]]
        sub = [r for r in ROWS if all(f(r) for f in fs)]
        if len(sub) >= 30:
            res = report(f"{a} & {b} & {c}", sub, verbose=False)
            if res and res['avgr'] > BASE + 0.25 and res['sign_ok']:
                report(f"{a} & {b} & {c}", sub)

    # collect robust
    print("\n" + "="*70)
    print("### ROBUST RULES (sign3yr + n>=30 + ex-top2>base) ###")
    seen = set()
    rob = [x for x in results if x and x['robust']]
    rob.sort(key=lambda x: -x['lift'])
    for x in rob:
        if x['name'] in seen:
            continue
        seen.add(x['name'])
        print(f"  {x['name']}: n={x['n']} WR={x['wr']}% avgR={x['avgr']} lift={x['lift']} "
              f"y24={x['y24']} y25={x['y25']} y26={x['y26']} ex2={x['ex2']}")


if __name__ == '__main__':
    main()
