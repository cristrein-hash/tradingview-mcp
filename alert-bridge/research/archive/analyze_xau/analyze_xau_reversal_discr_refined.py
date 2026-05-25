#!/usr/bin/env python3
"""
analyze_xau_reversal_discr_refined.py — Refinar T1 + T2 com filtros CVD/Bubble/OB.

Base setup: P1 (NAS LONG ≤5) + P2 (dist14d ≤-5%) + P3 (NAS_DIST ≤-1)

Opção B (T2 refinado): T2 + filtros pra reduzir fakeouts
Opção C (T1 refinado): T1 + CVDs/Bubble/OB pra ganhar precision

Variantes testadas (sobre base):
  T1 alone
  T1 + bubble_sell_4h (10c)
  T1 + ob_demand_bull
  T1 + TradingFinder +RD (recente)
  T1 + QuantAlgo Bullish Cross
  T1 + bubble + ob
  T1 + bubble + tradingfinder
  T1 + bubble + quantalgo
  T1 + ob + tradingfinder
  T1 + ob + quantalgo
  T1 + all 3

  T2 alone
  T2 + bubble_sell_4h
  T2 + ob_demand_bull
  T2 + bubble + ob

  T3 alone (já 100% win) — pra comparar
  T1+T3 (sem T2)
  T1_filtered + T2_filtered + T3 (versão final premium)
"""
from pathlib import Path
from datetime import datetime, timezone
from statistics import mean, median
import json, sys
from collections import defaultdict

BASE = Path(__file__).parent.parent
JSONL_DIR = BASE / "alert-bridge" / "logs" / "backtests"

WINDOWS_V5 = [
    ("W1_2023H1",    "XAUUSD_240_2023-01-19_to_2026-05-21_v5.jsonl"),
    ("W2_2023H2",    "XAUUSD_240_2023-07-19_to_2026-05-21_v5.jsonl"),
    ("W3_2024H1",    "XAUUSD_240_2024-01-19_to_2026-05-21_v5.jsonl"),
    ("W4_2024H2",    "XAUUSD_240_2024-07-19_to_2026-05-21_v5.jsonl"),
    ("W5_2025May",   "XAUUSD_240_2025-05-19_to_2026-05-21_v5.jsonl"),
    ("W6_2025Sep",   "XAUUSD_240_2025-09-15_to_2026-05-21_v5.jsonl"),
    ("W7_2025Nov",   "XAUUSD_240_2025-11-19_to_2026-05-21_v5.jsonl"),
    ("W8_2026Mar",   "XAUUSD_240_2026-03-19_to_2026-05-21_v5.jsonl"),
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
        if not oh: continue
        last = oh[-1]
        if last.get('time'): series.append(last)
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
        if not labels: continue
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
        if not labels: continue
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


def check_T2(lux):
    for d,txt,dirn in lux:
        if d<=5 and dirn=='BULL' and (txt=='CHoCH' or txt=='Strong Low'): return True
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
            if t_lb <= t <= et:
                for p in (act.get('shapes') or {}):
                    if p in SELL_PLOTS: return True
    return False


def has_ob_demand(bar):
    """v11 text='DEMAND' bull OB proximity."""
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


def has_tradingfinder_rd_bull(bar, lookback=5):
    """TradingFinder '+RD' label recente Δ≤lookback."""
    for s in (bar.get('pine_labels') or []):
        if 'TRADINGFINDER' not in s.get('name','').upper(): continue
        labels = s.get('labels') or []
        if not labels: continue
        xs=[l.get('x') for l in labels if l.get('x') is not None]
        if not xs: continue
        max_x=max(xs)
        for l in labels:
            lx=l.get('x'); txt=l.get('text','')
            if lx is None or txt!='+RD': continue
            if 0<=max_x-lx<=lookback: return True
    return False


def get_quantalgo(bar):
    """Retorna (rolling_cvd, signal_line)."""
    for s in (bar.get('study_values') or []):
        if 'QUANTALGO' in s.get('name','').upper():
            v = s.get('values',{})
            try:
                rc = v.get('Rolling CVD','').replace(',','').replace('−','-')
                sl = v.get('Signal Line','').replace(',','').replace('−','-')
                return float(rc), float(sl)
            except: return None, None
    return None, None


def stats_block(rs):
    if not rs: return None
    wins=sum(1 for r in rs if r>0)
    return {'n':len(rs),'win%':100*wins/len(rs),'avg_R':mean(rs),'median_R':median(rs),'sum_R':sum(rs)}


def main():
    print(f"=== REVERSAL_DISCR REFINED — Opção B (T2 filtered) + Opção C (T1 filtered) ===\n")
    print("Carregando 8 janelas + daily sintetizado...")

    per_w = {}
    for label, fname in WINDOWS_V5:
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

    # Compute features pra cada bar elegível (passou pre-req)
    print("Computing features...")
    rows = []
    prev_quant = {}  # time -> (rc, sl) do bar anterior pra detectar cross
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
        # Pre-reqs
        if not has_nas_label(b, "LONG", 5): continue
        nd = get_nas_dist(b)
        if nd is None or nd > -1: continue
        d14 = bt_dist.get(t)
        if d14 is None or d14 > -5: continue
        # Triggers
        lux = get_lux_labels(b, 20)
        t1 = check_T1(lux); t2 = check_T2(lux); t3 = check_T3(lux)
        if not (t1 or t2 or t3): continue
        # Filters adicionais
        bs = has_bubble_sell(b, 10)
        ob = has_ob_demand(b)
        tf_rd = has_tradingfinder_rd_bull(b, 5)
        rc, sl = get_quantalgo(b)
        # Bullish cross do QuantAlgo: rc agora > sl, antes < sl (bar previous)
        bull_cross = False
        if i>0 and rc is not None and sl is not None:
            prev_rc, prev_sl = prev_quant.get(times[i-1], (None,None))
            if prev_rc is not None and prev_sl is not None:
                bull_cross = (rc > sl) and (prev_rc <= prev_sl)
        # Above signal (sem precisar cross — Rolling > Signal agora)
        above_signal = (rc is not None and sl is not None and rc > sl)
        prev_quant[t] = (rc, sl)
        rows.append({
            'time':t,'window':bt_window[t],'r':round(r,2),
            't1':t1,'t2':t2,'t3':t3,
            'bs':bs,'ob':ob,'tf_rd':tf_rd,
            'bull_cross':bull_cross,'above_signal':above_signal,
        })
    print(f"  {len(rows)} bars elegíveis\n")

    # Variantes
    variants = [
        # T1 isolado + filtros
        ("T1 alone",                    lambda r: r['t1']),
        ("T1 + bubble_sell",            lambda r: r['t1'] and r['bs']),
        ("T1 + ob_demand",              lambda r: r['t1'] and r['ob']),
        ("T1 + tradingfinder_+RD",      lambda r: r['t1'] and r['tf_rd']),
        ("T1 + quant_above_signal",     lambda r: r['t1'] and r['above_signal']),
        ("T1 + quant_bull_cross",       lambda r: r['t1'] and r['bull_cross']),
        ("T1 + bubble + ob",            lambda r: r['t1'] and r['bs'] and r['ob']),
        ("T1 + bubble + tf_rd",         lambda r: r['t1'] and r['bs'] and r['tf_rd']),
        ("T1 + ob + tf_rd",             lambda r: r['t1'] and r['ob'] and r['tf_rd']),
        ("T1 + bubble + quant_above",   lambda r: r['t1'] and r['bs'] and r['above_signal']),
        ("T1 + ob + quant_above",       lambda r: r['t1'] and r['ob'] and r['above_signal']),
        # T2 isolado + filtros
        ("T2 alone",                    lambda r: r['t2']),
        ("T2 + bubble_sell",            lambda r: r['t2'] and r['bs']),
        ("T2 + ob_demand",              lambda r: r['t2'] and r['ob']),
        ("T2 + bubble + ob",            lambda r: r['t2'] and r['bs'] and r['ob']),
        ("T2 + tradingfinder_+RD",      lambda r: r['t2'] and r['tf_rd']),
        ("T2 + quant_above_signal",     lambda r: r['t2'] and r['above_signal']),
        # T3 isolado (já validado)
        ("T3 alone",                    lambda r: r['t3']),
        # Combos completos
        ("T1+T2+T3 ALL (sem filtros)",  lambda r: r['t1'] or r['t2'] or r['t3']),
        ("T1+T3 (remove T2)",           lambda r: r['t1'] or r['t3']),
        ("(T1+ob) OR (T2+bub+ob) OR T3",lambda r: (r['t1'] and r['ob']) or (r['t2'] and r['bs'] and r['ob']) or r['t3']),
        ("(T1+bub) OR (T2+bub+ob) OR T3",lambda r: (r['t1'] and r['bs']) or (r['t2'] and r['bs'] and r['ob']) or r['t3']),
    ]

    dream_ts = [(int(datetime.strptime(dt+"+0000","%Y-%m-%d %H:%M%z").timestamp()), tid) for tid,dt in DREAM_LONG]

    print(f"{'variant':<55s} {'n':>4s} {'win%':>5s} {'avg_R':>7s} {'sum_R':>8s} {'wp/we':>6s} {'recall':>7s}")
    print("-"*115)
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
        # Recall
        captured = set()
        for r in kept:
            for d_ts, tid in dream_ts:
                if abs(r['time']-d_ts)<=TOL: captured.add(tid)
        recall = 100*len(captured)/len(dream_ts)
        mk = "★" if s['win%']>=WIN_GATE and s['n']>=15 else " "
        print(f"{mk}{vname:<54s} {s['n']:>4d} {s['win%']:>5.1f} {s['avg_R']:>+7.2f} {s['sum_R']:>+8.2f} {wp:>2d}/{we:<2d} {recall:>5.0f}% ({len(captured)}/{len(dream_ts)})")

    return 0


if __name__ == "__main__":
    sys.exit(main())
