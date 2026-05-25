#!/usr/bin/env python3
"""
analyze_xau_cvd_local.py — CVD divergence detection em Python local.

Implementa Bull Regular Divergence (e Hidden + Absorption) replicando UAlgo
sem dependência do TV LTF security (que não funciona em replay).

CVD approximação: single-candle (TradingFinder-style):
  buying = volume * (close-low) / (high-low)
  selling = volume * (high-close) / (high-low)
  delta = buying - selling

CVD cumulative = cumsum(delta) (igual UAlgo Raw mode)

Pivot detection (window 5+5):
  Bull Regular Div: price LL + CVD HL em pivots low
  Bull Hidden Div: price HL + CVD LL
  Bull Absorption: price equal + CVD lower

Testar sobre T1+T3 base com lookbacks 5/10/15/20.
"""
from pathlib import Path
from datetime import datetime, timezone
from statistics import mean, median
import json, sys
from collections import defaultdict

BASE = Path(__file__).parent.parent
JSONL_DIR = BASE / "alert-bridge" / "logs" / "backtests"

WINDOWS_V6 = [
    ("W1_2023H1",    "XAUUSD_240_2023-01-19_to_2026-05-21_v6.jsonl"),
    ("W2_2023H2",    "XAUUSD_240_2023-07-19_to_2026-05-21_v6.jsonl"),
    ("W3_2024H1",    "XAUUSD_240_2024-01-19_to_2026-05-21_v6.jsonl"),
    ("W4_2024H2",    "XAUUSD_240_2024-07-19_to_2026-05-21_v6.jsonl"),
    ("W5_2025May",   "XAUUSD_240_2025-05-19_to_2026-05-21_v6.jsonl"),
    ("W6_2025Sep",   "XAUUSD_240_2025-09-15_to_2026-05-21_v6.jsonl"),
    ("W7_2025Nov",   "XAUUSD_240_2025-11-19_to_2026-05-21_v6.jsonl"),
    ("W8_2026Mar",   "XAUUSD_240_2026-03-19_to_2026-05-21_v6.jsonl"),
]

DREAM_LONG = [
    ("#1",  "2026-05-04 15:00"),("#6","2026-03-12 10:00"),("#8","2026-03-20 14:00"),
    ("#10","2026-03-24 10:00"),("#11","2026-01-29 19:00"),("#13","2026-02-03 03:00"),
]
LUX_BULL = 4286683400
LUX_BEAR = 4282726130
HORIZON = 20
WIN_GATE = 70.0
TOL = 7200
BSEC = 14400
SELL_PLOTS = {"plot_0", "plot_10"}
PIVOT_WINDOW = 5
DIV_LOOKBACK_PIVOTS = 60  # max bars to look back for prev pivot
EQUAL_TOL_PCT = 0.001  # 0.1% pra absorption (price equal)


def load_bars(p):
    bars=[]
    with Path(p).open() as f:
        for line in f:
            try: bars.append(json.loads(line))
            except: pass
    for i,b in enumerate(bars):
        if b.get('_error') or not (b.get('ohlcv_last_40_bars') or []):
            bars = bars[:i]; break
    return bars


def synth_daily(bars):
    series = []
    for b in bars:
        oh = b.get('ohlcv_last_40_bars') or []
        if oh and oh[-1].get('time'): series.append(oh[-1])
    seen = {c['time']: c for c in series}
    series = sorted(seen.values(), key=lambda x: x['time'])
    bd = {}
    for c in series:
        if c.get('close') is None: continue
        dt = datetime.fromtimestamp(c['time'], tz=timezone.utc)
        dk = int(datetime(dt.year,dt.month,dt.day,tzinfo=timezone.utc).timestamp())
        if dk not in bd:
            bd[dk] = {'time':dk,'high':c['high'],'low':c['low'],'close':c['close']}
        else:
            d = bd[dk]
            if c['high'] and (d['high'] is None or c['high']>d['high']): d['high']=c['high']
            if c['low'] and (d['low'] is None or c['low']<d['low']): d['low']=c['low']
            d['close']=c['close']
    return sorted(bd.values(), key=lambda x: x['time'])


def get_atr14(bar):
    oh = bar.get('ohlcv_last_40_bars') or []
    if len(oh)<=1: return None
    closed = oh[:-1][-14:]
    r=[b['high']-b['low'] for b in closed if b.get('high') and b.get('low')]
    return mean(r) if r else None


def has_nas_label(bar, want_text, max_delta=5):
    for s in (bar.get('pine_labels') or []):
        if 'NAS' not in s.get('name','').upper(): continue
        labels = s.get('labels') or []
        xs=[l.get('x') for l in labels if l.get('x') is not None]
        if not xs: continue
        max_x = max(xs)
        for l in labels:
            lx=l.get('x'); txt=(l.get('text') or '').upper()
            if lx is None or txt!=want_text: continue
            if 0<=max_x-lx<=max_delta: return True
    return False


def get_nas_dist(bar):
    for s in (bar.get('study_values') or []):
        if 'NAS' in s.get('name',''):
            try: return float(s.get('values',{}).get('NAS_DISTANCE_FROM_EMA_ATR','').replace('−','-'))
            except: return None
    return None


def get_lux_labels(bar, max_delta=20):
    out=[]
    for s in (bar.get('pine_labels') or []):
        if 'LUXALGO' not in s.get('name','').upper(): continue
        labels = s.get('labels') or []
        xs=[l.get('x') for l in labels if l.get('x') is not None]
        if not xs: continue
        max_x=max(xs)
        for l in labels:
            lx=l.get('x'); txt=l.get('text','')
            if lx is None: continue
            delta=max_x-lx
            if 0<=delta<=max_delta:
                tc=l.get('textColor')
                d='BULL' if tc==LUX_BULL else 'BEAR' if tc==LUX_BEAR else '?'
                out.append((delta,txt,d))
        return out
    return out


def check_T1(lux):
    for d,txt,dirn in lux:
        if d<=2 and dirn=='BEAR' and txt in ('BOS','CHoCH'): return True
    return False


def check_T3(lux):
    for d,txt,dirn in lux:
        if d<=5 and dirn=='BULL' and txt=='BOS': return True
    return False


def has_bubble_sell(bar, lookback=10):
    et = (bar.get('ohlcv_last_40_bars') or [{}])[-1].get('time')
    if et is None: return False
    t_lb = et - (lookback-1)*BSEC
    for s in (bar.get('pine_shapes_bubbles') or []):
        if 'Bubbles' not in s.get('name',''): continue
        for act in s.get('activations',[]):
            t = act.get('time')
            if t is None: continue
            if t_lb<=t<=et:
                for p in (act.get('shapes') or {}):
                    if p in SELL_PLOTS: return True
    return False


def has_ob_demand(bar):
    close = (bar.get('ohlcv_last_40_bars') or [{}])[-1].get('close')
    if close is None: return False
    for s in (bar.get('pine_boxes') or []):
        if 'Custom OB' not in s.get('name',''): continue
        for box in (s.get('all_boxes') or []):
            hi,lo = box.get('high'), box.get('low')
            txt = box.get('text')
            if hi is None or lo is None or txt!='DEMAND': continue
            sz = hi-lo
            if sz<=0: continue
            if lo<=close<=hi: return True
            dist = max((close-hi) if close>hi else 0, (lo-close) if close<lo else 0)
            if dist <= sz*0.5: return True
    return False


def stats_block(rs):
    if not rs: return None
    wins=sum(1 for r in rs if r>0)
    return {'n':len(rs),'win%':100*wins/len(rs),'avg_R':mean(rs),'sum_R':sum(rs)}


def compute_cvd_features(bars_arr):
    """Pra cada bar, computa CVD cumulativo + detecta bull divergences nos últimos bars."""
    n = len(bars_arr)
    closes = [None]*n
    highs = [None]*n
    lows = [None]*n
    vols = [None]*n
    for i, b in enumerate(bars_arr):
        oh = b.get('ohlcv_last_40_bars') or []
        if not oh: continue
        last = oh[-1]
        closes[i] = last.get('close')
        highs[i] = last.get('high')
        lows[i] = last.get('low')
        vols[i] = last.get('volume', 0) or 0

    # Compute delta per bar (single-candle approx)
    deltas = [0.0]*n
    for i in range(n):
        if closes[i] is None or highs[i] is None or lows[i] is None: continue
        rng = highs[i] - lows[i]
        if rng <= 0: continue
        buying = vols[i] * (closes[i] - lows[i]) / rng
        selling = vols[i] * (highs[i] - closes[i]) / rng
        deltas[i] = buying - selling

    # Cumulative CVD
    cvd = [0.0]*n
    for i in range(1, n):
        cvd[i] = cvd[i-1] + deltas[i]

    # Detect pivot lows (window PIVOT_WINDOW)
    is_pivot_low = [False]*n
    for i in range(PIVOT_WINDOW, n - PIVOT_WINDOW):
        if lows[i] is None: continue
        is_pl = True
        for j in range(1, PIVOT_WINDOW+1):
            if lows[i-j] is None or lows[i-j] <= lows[i]: is_pl=False; break
            if lows[i+j] is None or lows[i+j] <= lows[i]: is_pl=False; break
        if is_pl: is_pivot_low[i] = True

    # Detect pivot highs (window)
    is_pivot_high = [False]*n
    for i in range(PIVOT_WINDOW, n - PIVOT_WINDOW):
        if highs[i] is None: continue
        is_ph = True
        for j in range(1, PIVOT_WINDOW+1):
            if highs[i-j] is None or highs[i-j] >= highs[i]: is_ph=False; break
            if highs[i+j] is None or highs[i+j] >= highs[i]: is_ph=False; break
        if is_ph: is_pivot_high[i] = True

    # Pra cada bar, encontrar último pivot low confirmado (i - PIVOT_WINDOW) e o anterior
    # Computar Bull Reg/Hid/Abs Div pra cada pivot
    bull_reg_div_at_bar = [False]*n  # True se algum pivot recente teve Bull Reg Div confirmada
    bull_hid_div_at_bar = [False]*n
    bull_abs_at_bar = [False]*n
    last_div_pivot_idx = [None]*n  # idx do pivot mais recente com qualquer Bull Div

    for i in range(n):
        # Pivot mais recente confirmado é i - PIVOT_WINDOW (precisa 5 bars de futuro)
        # Procura últimos 2 pivots low <= i-PIVOT_WINDOW
        pivots = []
        for j in range(i - PIVOT_WINDOW, max(0, i - DIV_LOOKBACK_PIVOTS), -1):
            if is_pivot_low[j]:
                pivots.append(j)
                if len(pivots) >= 2: break
        if len(pivots) < 2: continue
        p1, p2 = pivots[0], pivots[1]  # p1 mais recente
        if lows[p1] is None or lows[p2] is None: continue
        # Bull Regular: price LL + CVD HL
        if lows[p1] < lows[p2] and cvd[p1] > cvd[p2]:
            bull_reg_div_at_bar[i] = True
            last_div_pivot_idx[i] = p1
        # Bull Hidden: price HL + CVD LL
        elif lows[p1] > lows[p2] and cvd[p1] < cvd[p2]:
            bull_hid_div_at_bar[i] = True
            if last_div_pivot_idx[i] is None: last_div_pivot_idx[i] = p1
        # Bull Absorption: price approx equal + CVD lower
        else:
            price_diff_pct = abs(lows[p1] - lows[p2]) / lows[p2]
            if price_diff_pct <= EQUAL_TOL_PCT and cvd[p1] < cvd[p2]:
                bull_abs_at_bar[i] = True
                if last_div_pivot_idx[i] is None: last_div_pivot_idx[i] = p1

    return {
        'cvd': cvd,
        'bull_reg': bull_reg_div_at_bar,
        'bull_hid': bull_hid_div_at_bar,
        'bull_abs': bull_abs_at_bar,
        'last_pivot': last_div_pivot_idx,
    }


def main():
    print(f"=== CVD LOCAL (Python) — Bull Regular/Hidden/Absorption ===\n")

    per_w = {}
    for label, fname in WINDOWS_V6:
        p = JSONL_DIR / fname
        if not p.exists(): continue
        bars = load_bars(p)
        daily = synth_daily(bars)
        closes = [b['close'] for b in daily]; highs=[b['high'] for b in daily]
        dist14 = [None]*len(daily)
        for i in range(len(daily)):
            w = highs[max(0,i-13):i+1]
            dist14[i] = (closes[i]-max(w))/max(w)*100
        per_w[label] = {'bars':bars,'daily':daily,'dist14':dist14}

    master={}; bt_window={}; bt_dist={}
    for label, data in per_w.items():
        for b in data['bars']:
            oh = b.get('ohlcv_last_40_bars') or []
            if not oh: continue
            t = oh[-1].get('time')
            if t is None or t in master: continue
            master[t]=b; bt_window[t]=label
            di = None
            for i in range(len(data['daily'])-1,-1,-1):
                if data['daily'][i]['time']<=t:
                    di=i; break
            if di is not None and di<len(data['dist14']):
                bt_dist[t] = data['dist14'][di]
    times = sorted(master.keys())
    bars_arr = [master[t] for t in times]
    print(f"Master: {len(times)} bars 4H\n")

    # Compute CVD features
    print("Computing local CVD divergences...")
    cvd_f = compute_cvd_features(bars_arr)
    n_reg = sum(cvd_f['bull_reg'])
    n_hid = sum(cvd_f['bull_hid'])
    n_abs = sum(cvd_f['bull_abs'])
    print(f"  Bull Reg Div detected in {n_reg} bars  Hid in {n_hid}  Abs in {n_abs}\n")

    print("Computing features per eligible bar...")
    rows = []
    for i, t in enumerate(times):
        b = bars_arr[i]
        oh = b.get('ohlcv_last_40_bars') or []
        close = oh[-1].get('close') if oh else None
        if close is None: continue
        atr = get_atr14(b)
        if not atr or atr<=0: continue
        if i+HORIZON >= len(bars_arr): continue
        nc = (bars_arr[i+HORIZON].get('ohlcv_last_40_bars') or [{}])[-1].get('close')
        if nc is None: continue
        r = (nc-close)/atr
        if not has_nas_label(b, "LONG", 5): continue
        nd = get_nas_dist(b)
        if nd is None or nd > -1: continue
        d14 = bt_dist.get(t)
        if d14 is None or d14 > -5: continue
        lux = get_lux_labels(b, 20)
        t1 = check_T1(lux); t3 = check_T3(lux)
        if not (t1 or t3): continue

        # Local CVD features (looking back N bars from current i)
        # Bull div RECENT: any bull_reg/hid/abs True in last K bars?
        def bull_in_last_k(arr, k):
            for j in range(max(0, i-k), i+1):
                if arr[j]: return True
            return False

        rows.append({
            'time':t,'window':bt_window[t],'r':round(r,2),
            't1':t1,'t3':t3,
            'breg_5':bull_in_last_k(cvd_f['bull_reg'], 5),
            'breg_10':bull_in_last_k(cvd_f['bull_reg'], 10),
            'breg_15':bull_in_last_k(cvd_f['bull_reg'], 15),
            'breg_20':bull_in_last_k(cvd_f['bull_reg'], 20),
            'bhid_15':bull_in_last_k(cvd_f['bull_hid'], 15),
            'babs_15':bull_in_last_k(cvd_f['bull_abs'], 15),
            'bany_15':bull_in_last_k(cvd_f['bull_reg'], 15) or bull_in_last_k(cvd_f['bull_hid'], 15) or bull_in_last_k(cvd_f['bull_abs'], 15),
            'bany_20':bull_in_last_k(cvd_f['bull_reg'], 20) or bull_in_last_k(cvd_f['bull_hid'], 20) or bull_in_last_k(cvd_f['bull_abs'], 20),
            'bs':has_bubble_sell(b, 10),
            'ob':has_ob_demand(b),
        })
    print(f"  {len(rows)} bars elegíveis (T1 ou T3)\n")

    dream_ts = [(int(datetime.strptime(dt+"+0000","%Y-%m-%d %H:%M%z").timestamp()), tid) for tid,dt in DREAM_LONG]

    variants = [
        ("BASE T1+T3",                                          lambda r: r['t1'] or r['t3']),
        # Bull Reg Div em lookbacks
        ("T1+T3 + bull_reg_5",                                  lambda r: (r['t1'] or r['t3']) and r['breg_5']),
        ("T1+T3 + bull_reg_10",                                 lambda r: (r['t1'] or r['t3']) and r['breg_10']),
        ("T1+T3 + bull_reg_15",                                 lambda r: (r['t1'] or r['t3']) and r['breg_15']),
        ("T1+T3 + bull_reg_20",                                 lambda r: (r['t1'] or r['t3']) and r['breg_20']),
        # Hidden e Absorption
        ("T1+T3 + bull_hid_15",                                 lambda r: (r['t1'] or r['t3']) and r['bhid_15']),
        ("T1+T3 + bull_abs_15",                                 lambda r: (r['t1'] or r['t3']) and r['babs_15']),
        # Any bull div
        ("T1+T3 + bull_any_15",                                 lambda r: (r['t1'] or r['t3']) and r['bany_15']),
        ("T1+T3 + bull_any_20",                                 lambda r: (r['t1'] or r['t3']) and r['bany_20']),
        # Combos
        ("T1+T3 + bull_reg_15 + bubble",                        lambda r: (r['t1'] or r['t3']) and r['breg_15'] and r['bs']),
        ("T1+T3 + bull_reg_15 + ob",                            lambda r: (r['t1'] or r['t3']) and r['breg_15'] and r['ob']),
        ("T1+T3 + bull_any_15 + bubble",                        lambda r: (r['t1'] or r['t3']) and r['bany_15'] and r['bs']),
        ("T1+T3 + bull_any_15 + ob",                            lambda r: (r['t1'] or r['t3']) and r['bany_15'] and r['ob']),
        # T1 only com bull div
        ("T1 only + bull_any_15",                               lambda r: r['t1'] and r['bany_15']),
        ("T1 only + bull_reg_15",                               lambda r: r['t1'] and r['breg_15']),
    ]

    print(f"{'variant':<55s} {'n':>4s} {'win%':>5s} {'avg_R':>7s} {'sum_R':>8s} {'wp/we':>6s} {'recall':>10s}")
    print("-"*120)
    for vname, fn in variants:
        kept = [r for r in rows if fn(r)]
        rs = [r['r'] for r in kept]
        s = stats_block(rs)
        if not s or s['n']<5:
            print(f"  {vname:<55s} {s['n'] if s else 0:>4d}  (n insuficiente)"); continue
        per = defaultdict(list)
        for r in kept: per[r['window']].append(r['r'])
        wp = sum(1 for w,rs_w in per.items() if len(rs_w)>=10 and stats_block(rs_w)['win%']>=WIN_GATE)
        we = sum(1 for w,rs_w in per.items() if len(rs_w)>=10)
        captured = set()
        for r in kept:
            for d_ts, tid in dream_ts:
                if abs(r['time']-d_ts)<=TOL: captured.add(tid)
        recall = 100*len(captured)/len(dream_ts)
        mk = "★" if s['win%']>=WIN_GATE and s['n']>=15 else " "
        print(f"{mk}{vname:<54s} {s['n']:>4d} {s['win%']:>5.1f} {s['avg_R']:>+7.2f} {s['sum_R']:>+8.2f} {wp:>2d}/{we:<2d} {recall:>4.0f}% ({len(captured)}/6)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
