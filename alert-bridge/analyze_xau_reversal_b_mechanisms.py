#!/usr/bin/env python3
"""
analyze_xau_reversal_b_mechanisms.py — Caminho B: 4 mecanismos novos sobre BASE T1+T3.

Mecanismos testados:
  1. Liquidity Sweep (EQL nível recente + close acima dele OU Strong Low recente)
  2. Wick Reversal (hammer/long lower wick em últimos 1-3 candles)
  3. Volume Spike (volume atual >= K * média 20 candles)
  4. RSI 1D oversold cross (RSI 1D <30 em algum dos últimos 5 dias + atual >=30)

Base: T1 OR T3 já validados.
Objetivo: encontrar variante que mantém recall (4/6+) E sobe win% >=70%.
"""
from pathlib import Path
from datetime import datetime, timezone
from statistics import mean
import json, sys
from collections import defaultdict

BASE = Path(__file__).parent.parent
JSONL_DIR = BASE / "alert-bridge" / "logs" / "backtests"
WINDOWS_V6 = [
    ("W1_2023H1","XAUUSD_240_2023-01-19_to_2026-05-21_v6.jsonl"),
    ("W2_2023H2","XAUUSD_240_2023-07-19_to_2026-05-21_v6.jsonl"),
    ("W3_2024H1","XAUUSD_240_2024-01-19_to_2026-05-21_v6.jsonl"),
    ("W4_2024H2","XAUUSD_240_2024-07-19_to_2026-05-21_v6.jsonl"),
    ("W5_2025May","XAUUSD_240_2025-05-19_to_2026-05-21_v6.jsonl"),
    ("W6_2025Sep","XAUUSD_240_2025-09-15_to_2026-05-21_v6.jsonl"),
    ("W7_2025Nov","XAUUSD_240_2025-11-19_to_2026-05-21_v6.jsonl"),
    ("W8_2026Mar","XAUUSD_240_2026-03-19_to_2026-05-21_v6.jsonl"),
]
DREAM_LONG = [
    ("#1","2026-05-04 15:00"),("#6","2026-03-12 10:00"),("#8","2026-03-20 14:00"),
    ("#10","2026-03-24 10:00"),("#11","2026-01-29 19:00"),("#13","2026-02-03 03:00"),
]
LUX_BULL = 4286683400
LUX_BEAR = 4282726130
HORIZON = 20
WIN_GATE = 70.0
TOL = 7200


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
    series=[]
    for b in bars:
        oh=b.get('ohlcv_last_40_bars') or []
        if oh and oh[-1].get('time'): series.append(oh[-1])
    seen={c['time']:c for c in series}
    series=sorted(seen.values(), key=lambda x:x['time'])
    bd={}
    for c in series:
        if c.get('close') is None: continue
        dt=datetime.fromtimestamp(c['time'],tz=timezone.utc)
        dk=int(datetime(dt.year,dt.month,dt.day,tzinfo=timezone.utc).timestamp())
        if dk not in bd:
            bd[dk]={'time':dk,'open':c.get('open'),'high':c['high'],'low':c['low'],'close':c['close']}
        else:
            d=bd[dk]
            if c['high'] and (d['high'] is None or c['high']>d['high']): d['high']=c['high']
            if c['low'] and (d['low'] is None or c['low']<d['low']): d['low']=c['low']
            d['close']=c['close']
    return sorted(bd.values(), key=lambda x:x['time'])


def rsi_series(closes, period=14):
    """Wilder RSI."""
    n = len(closes)
    out = [None]*n
    if n < period+1: return out
    gains=[]; losses=[]
    for i in range(1, period+1):
        diff = closes[i]-closes[i-1]
        gains.append(max(diff,0)); losses.append(max(-diff,0))
    avg_gain = sum(gains)/period
    avg_loss = sum(losses)/period
    rs = avg_gain/avg_loss if avg_loss>0 else float('inf')
    out[period] = 100 - 100/(1+rs) if avg_loss>0 else 100
    for i in range(period+1, n):
        diff = closes[i]-closes[i-1]
        g = max(diff,0); l = max(-diff,0)
        avg_gain = (avg_gain*(period-1)+g)/period
        avg_loss = (avg_loss*(period-1)+l)/period
        rs = avg_gain/avg_loss if avg_loss>0 else float('inf')
        out[i] = 100 - 100/(1+rs) if avg_loss>0 else 100
    return out


def get_atr14(bar):
    oh=bar.get('ohlcv_last_40_bars') or []
    if len(oh)<=1: return None
    closed=oh[:-1][-14:]
    r=[b['high']-b['low'] for b in closed if b.get('high') and b.get('low')]
    return mean(r) if r else None


def has_nas_label(bar, want_text, max_delta=5):
    for s in (bar.get('pine_labels') or []):
        if 'NAS' not in s.get('name','').upper(): continue
        labels=s.get('labels') or []
        xs=[l.get('x') for l in labels if l.get('x') is not None]
        if not xs: continue
        max_x=max(xs)
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
        labels=s.get('labels') or []
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
                p=l.get('price')
                out.append((delta,txt,d,p))
        return out
    return out


def check_T1(lux):
    for d,txt,dirn,_ in lux:
        if d<=2 and dirn=='BEAR' and txt in ('BOS','CHoCH'): return True
    return False


def check_T3(lux):
    for d,txt,dirn,_ in lux:
        if d<=5 and dirn=='BULL' and txt=='BOS': return True
    return False


# --- Mecanismos novos ---

def has_strong_low_recent(lux, max_lookback=10):
    """Strong Low marcado dentro dos últimos max_lookback candles."""
    for d,txt,_,_ in lux:
        if d<=max_lookback and txt=='Strong Low': return True
    return False


def has_eql_sweep(bar, lux, close, low, lookback_eql=20):
    """EQL nível existe próximo do preço + low atual perfurou OU está dentro de 0.3% do EQL."""
    if close is None or low is None: return False
    for d,txt,_,price in lux:
        if d > lookback_eql or txt != 'EQL': continue
        if price is None: continue
        # Sweep: low atual ficou ABAIXO do EQL E close VOLTOU pra cima
        if low <= price and close > price: return True
        # Próximo o suficiente (toque)
        if abs(low - price)/price <= 0.003 and close > price: return True
    return False


def has_wick_reversal(bar, lookback=3, min_wick_ratio=1.5):
    """Em algum dos últimos 'lookback' candles, lower wick >= min_wick_ratio * body."""
    oh = bar.get('ohlcv_last_40_bars') or []
    if not oh: return False
    candles = oh[-lookback:]
    for c in candles:
        o=c.get('open'); h=c.get('high'); l=c.get('low'); cl=c.get('close')
        if None in (o,h,l,cl): continue
        body = abs(cl-o)
        lower_wick = min(o,cl) - l
        upper_wick = h - max(o,cl)
        rng = h - l
        if rng<=0 or body<=0: continue
        if lower_wick >= min_wick_ratio * body and lower_wick > upper_wick:
            # Close na metade superior do candle (sinal de rejeição)
            if cl >= l + 0.5*rng: return True
    return False


def has_volume_spike(bar, multiplier=2.0):
    """Volume do candle atual >= multiplier * media dos 20 candles anteriores."""
    oh = bar.get('ohlcv_last_40_bars') or []
    if len(oh) < 21: return False
    current_vol = oh[-1].get('volume', 0) or 0
    prior = oh[-21:-1]
    vols = [c.get('volume',0) or 0 for c in prior]
    avg = mean(vols) if vols else 0
    if avg <= 0: return False
    return current_vol >= multiplier * avg


def has_volume_spike_lookback(bar, multiplier=2.0, lookback=10):
    """Volume spike >= multiplier * media (20 antes do spike) em algum dos últimos 'lookback' candles."""
    oh = bar.get('ohlcv_last_40_bars') or []
    if len(oh) < 25: return False
    # check último 'lookback' bars (excluindo bar atual? incluindo)
    for k in range(0, lookback):
        # candle alvo: oh[-1-k]
        idx_target = len(oh) - 1 - k
        if idx_target < 20: continue
        tgt_vol = oh[idx_target].get('volume',0) or 0
        prior = oh[idx_target-20:idx_target]
        vols = [c.get('volume',0) or 0 for c in prior]
        avg = mean(vols) if vols else 0
        if avg <= 0: continue
        if tgt_vol >= multiplier * avg: return True
    return False


def stats_block(rs):
    if not rs: return None
    wins=sum(1 for r in rs if r>0)
    return {'n':len(rs),'win%':100*wins/len(rs),'avg_R':mean(rs),'sum_R':sum(rs)}


def main():
    print(f"=== CAMINHO B — 4 mecanismos novos (Sweep / Wick / Volume / RSI 1D cross) ===\n")

    per_w = {}
    for label, fname in WINDOWS_V6:
        p = JSONL_DIR / fname
        if not p.exists(): continue
        bars = load_bars(p)
        daily = synth_daily(bars)
        closes_d = [b['close'] for b in daily]
        highs_d = [b['high'] for b in daily]
        # dist14 from daily highs
        dist14 = [None]*len(daily)
        for i in range(len(daily)):
            w = highs_d[max(0,i-13):i+1]
            dist14[i] = (closes_d[i]-max(w))/max(w)*100
        # RSI 1D
        rsi1d = rsi_series(closes_d, period=14)
        per_w[label] = {'bars':bars,'daily':daily,'dist14':dist14,'rsi1d':rsi1d}

    master={}; bt_window={}; bt_dist={}; bt_rsi1d={}; bt_rsi1d_oversold_recent={}; bt_rsi1d_above30={}
    for label, data in per_w.items():
        daily = data['daily']
        rsi1d = data['rsi1d']
        for b in data['bars']:
            oh = b.get('ohlcv_last_40_bars') or []
            if not oh: continue
            t = oh[-1].get('time')
            if t is None or t in master: continue
            master[t]=b; bt_window[t]=label
            di=None
            for i in range(len(daily)-1,-1,-1):
                if daily[i]['time']<=t: di=i; break
            if di is not None and di<len(data['dist14']):
                bt_dist[t]=data['dist14'][di]
                rsi_now = rsi1d[di]
                bt_rsi1d[t] = rsi_now
                window = rsi1d[max(0,di-5):di+1]
                oversold_recent = any(v is not None and v < 30 for v in window)
                bt_rsi1d_oversold_recent[t] = oversold_recent
                bt_rsi1d_above30[t] = (rsi_now is not None and rsi_now >= 30)

    times = sorted(master.keys())
    print(f"Master: {len(times)} bars\n")

    print("Computing features per eligible bar...")
    rows=[]
    for i, t in enumerate(times):
        b = master[t]
        oh = b.get('ohlcv_last_40_bars') or []
        close = oh[-1].get('close') if oh else None
        low = oh[-1].get('low') if oh else None
        if close is None: continue
        atr = get_atr14(b)
        if not atr or atr<=0: continue
        # outcome H=20
        idx_next = times.index(t) + HORIZON if False else None
        # rebuild via master index
        pos = i
        if pos+HORIZON >= len(times): continue
        nb = master[times[pos+HORIZON]]
        nc = (nb.get('ohlcv_last_40_bars') or [{}])[-1].get('close')
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

        rows.append({
            'time':t,'window':bt_window[t],'r':round(r,2),
            't1':t1,'t3':t3,
            # M1: Liquidity Sweep
            'strong_low_10':has_strong_low_recent(lux, 10),
            'strong_low_5':has_strong_low_recent(lux, 5),
            'eql_sweep':has_eql_sweep(b, lux, close, low, 20),
            'sweep_any':has_strong_low_recent(lux, 10) or has_eql_sweep(b, lux, close, low, 20),
            # M2: Wick Reversal
            'wick_1_15':has_wick_reversal(b, 1, 1.5),
            'wick_3_15':has_wick_reversal(b, 3, 1.5),
            'wick_3_20':has_wick_reversal(b, 3, 2.0),
            # M3: Volume Spike — usar LOOKBACK porque spike ocorre antes do sinal
            'vol_2x':has_volume_spike(b, 2.0),
            'vol_3x':has_volume_spike(b, 3.0),
            'vol_lb_2x_10':has_volume_spike_lookback(b, 2.0, 10),
            'vol_lb_2x_5':has_volume_spike_lookback(b, 2.0, 5),
            'vol_lb_15x_10':has_volume_spike_lookback(b, 1.5, 10),
            # M4: RSI 1D oversold cross
            'rsi1d_cross':bt_rsi1d_oversold_recent.get(t,False) and bt_rsi1d_above30.get(t,False),
            'rsi1d_oversold_only':bt_rsi1d_oversold_recent.get(t,False),
            'rsi1d_lt35': (bt_rsi1d.get(t) is not None and bt_rsi1d.get(t) < 35),
            'rsi1d_lt30': (bt_rsi1d.get(t) is not None and bt_rsi1d.get(t) < 30),
        })
    print(f"  {len(rows)} bars elegíveis (T1 ou T3)\n")

    dream_ts = [(int(datetime.strptime(dt+"+0000","%Y-%m-%d %H:%M%z").timestamp()), tid) for tid,dt in DREAM_LONG]

    variants = [
        ("BASE T1+T3",                                          lambda r: r['t1'] or r['t3']),
        # M1: Sweep variants
        ("BASE + strong_low_10",                                lambda r: (r['t1'] or r['t3']) and r['strong_low_10']),
        ("BASE + strong_low_5",                                 lambda r: (r['t1'] or r['t3']) and r['strong_low_5']),
        ("BASE + eql_sweep",                                    lambda r: (r['t1'] or r['t3']) and r['eql_sweep']),
        ("BASE + sweep_any",                                    lambda r: (r['t1'] or r['t3']) and r['sweep_any']),
        # M2: Wick variants
        ("BASE + wick_1bar_1.5x",                               lambda r: (r['t1'] or r['t3']) and r['wick_1_15']),
        ("BASE + wick_3bar_1.5x",                               lambda r: (r['t1'] or r['t3']) and r['wick_3_15']),
        ("BASE + wick_3bar_2.0x",                               lambda r: (r['t1'] or r['t3']) and r['wick_3_20']),
        # M3: Volume Spike (lookback)
        ("BASE + vol_spike_lb_2x_10",                           lambda r: (r['t1'] or r['t3']) and r['vol_lb_2x_10']),
        ("BASE + vol_spike_lb_2x_5",                            lambda r: (r['t1'] or r['t3']) and r['vol_lb_2x_5']),
        ("BASE + vol_spike_lb_15x_10",                          lambda r: (r['t1'] or r['t3']) and r['vol_lb_15x_10']),
        # M4: RSI 1D variants
        ("BASE + rsi1d_<30",                                    lambda r: (r['t1'] or r['t3']) and r['rsi1d_lt30']),
        ("BASE + rsi1d_<35",                                    lambda r: (r['t1'] or r['t3']) and r['rsi1d_lt35']),
        ("BASE + rsi1d_oversold_recent",                        lambda r: (r['t1'] or r['t3']) and r['rsi1d_oversold_only']),
        # Combos
        ("BASE + sweep_any + rsi1d_<35",                        lambda r: (r['t1'] or r['t3']) and r['sweep_any'] and r['rsi1d_lt35']),
        ("BASE + sweep_any + wick_3_15",                        lambda r: (r['t1'] or r['t3']) and r['sweep_any'] and r['wick_3_15']),
        ("BASE + sweep_any + vol_lb_2x_10",                     lambda r: (r['t1'] or r['t3']) and r['sweep_any'] and r['vol_lb_2x_10']),
        ("BASE + wick_3_15 + vol_lb_2x_10",                     lambda r: (r['t1'] or r['t3']) and r['wick_3_15'] and r['vol_lb_2x_10']),
        ("BASE + wick_3_15 + rsi1d_<35",                        lambda r: (r['t1'] or r['t3']) and r['wick_3_15'] and r['rsi1d_lt35']),
        ("BASE + vol_lb_2x_10 + rsi1d_<35",                     lambda r: (r['t1'] or r['t3']) and r['vol_lb_2x_10'] and r['rsi1d_lt35']),
        ("BASE + sweep_any + rsi1d_lt30",                       lambda r: (r['t1'] or r['t3']) and r['sweep_any'] and r['rsi1d_lt30']),
        # ANY de 4
        ("BASE + ANY_of_4",                                     lambda r: (r['t1'] or r['t3']) and (r['sweep_any'] or r['wick_3_15'] or r['vol_lb_2x_10'] or r['rsi1d_lt35'])),
        ("BASE + 2of4",                                         lambda r: (r['t1'] or r['t3']) and (sum([r['sweep_any'], r['wick_3_15'], r['vol_lb_2x_10'], r['rsi1d_lt35']]) >= 2)),
        ("BASE + 3of4",                                         lambda r: (r['t1'] or r['t3']) and (sum([r['sweep_any'], r['wick_3_15'], r['vol_lb_2x_10'], r['rsi1d_lt35']]) >= 3)),
    ]

    print(f"  {'variant':<48s} {'n':>4s} {'win%':>5s} {'avg_R':>7s} {'sum_R':>8s} {'wp/we':>6s} {'recall':>12s}")
    print("-"*120)
    for vname, fn in variants:
        kept = [r for r in rows if fn(r)]
        rs = [r['r'] for r in kept]
        s = stats_block(rs)
        if not s or s['n']<5:
            print(f"  {vname:<48s} {s['n'] if s else 0:>4d}  (n insuficiente)"); continue
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
        print(f"{mk} {vname:<47s} {s['n']:>4d} {s['win%']:>5.1f} {s['avg_R']:>+7.2f} {s['sum_R']:>+8.2f} {wp:>2d}/{we:<2d} {recall:>4.0f}% ({len(captured)}/6)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
