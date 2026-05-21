#!/usr/bin/env python3
"""
analyze_xau_reversal_v2_deferred.py — REVERSAL_DISCRETIONARY V2.

Lógica (deferred entry no reteste DEMAND OB):
  1. REGIONAL_TRIGGER: NAS LONG <=5 + NAS_DIST<-1 + dist14h<-5 + (T1 OU T3)
  2. SEM LIMITE de tempo: varre bars futuros até encontrar reteste
  3. ENTRY no primeiro bar f > t onde:
     - existe DEMAND OB box com low[f] <= DEMAND.high E close[f] >= DEMAND.high
     - LuxAlgo BOS/CHoCH BULL apareceu entre t e f
     - Bubble Leviathan ativou nos últimos 10 candles antes de f
  4. Stop = DEMAND.low - 0.3*ATR
  5. 4 variantes target: 1.5R, 2R, 3R, close H=20

Comparação contra V1 BASE: 177 trades, 59.9% win, +0.72R avg, 4/6 recall.
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
STOP_ATR_BUFFERS = [0.3, 0.5, 1.0]  # testar 3 larguras
TOL = 7200
BSEC = 14400
H_CLOSE = 20
WIN_GATE = 70.0


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
            bd[dk]={'time':dk,'high':c['high'],'low':c['low'],'close':c['close']}
        else:
            d=bd[dk]
            if c['high'] and (d['high'] is None or c['high']>d['high']): d['high']=c['high']
            if c['low'] and (d['low'] is None or c['low']<d['low']): d['low']=c['low']
            d['close']=c['close']
    return sorted(bd.values(), key=lambda x:x['time'])


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


def get_lux_labels(bar, max_delta=30):
    """Retorna [(delta_bars_from_now, text, direction)] do LuxAlgo do bar atual."""
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


def has_lux_bull_since(bar, bars_back_limit):
    """LuxAlgo BOS/CHoCH BULL apareceu nos últimos 'bars_back_limit' candles."""
    lux = get_lux_labels(bar, bars_back_limit)
    for d,txt,dirn in lux:
        if dirn=='BULL' and txt in ('BOS','CHoCH'): return True
    return False


def get_demand_boxes(bar):
    """Retorna lista de DEMAND boxes ativas: [{'high':..,'low':..}]."""
    out=[]
    for s in (bar.get('pine_boxes') or []):
        if 'Custom OB' not in s.get('name',''): continue
        for box in (s.get('all_boxes') or []):
            hi,lo = box.get('high'), box.get('low')
            if hi is None or lo is None: continue
            if box.get('text') != 'DEMAND': continue
            out.append({'high':hi,'low':lo})
    return out


def has_bubble_activation_lookback(bar, lookback=10):
    """Qualquer ativação do indicator de bubbles nos últimos 'lookback' candles."""
    et = (bar.get('ohlcv_last_40_bars') or [{}])[-1].get('time')
    if et is None: return False
    t_lb = et - (lookback-1)*BSEC
    for s in (bar.get('pine_shapes_bubbles') or []):
        if 'Bubbles' not in s.get('name',''): continue
        for act in s.get('activations',[]):
            t = act.get('time')
            if t is None: continue
            if t_lb<=t<=et and (act.get('shapes') or {}): return True
    return False


def compute_outcome(entry_idx, entry_close, stop_price, target_R, times, master):
    """Retorna R do trade: +target_R se atinge target, -1 se atinge stop, ou close-based se nem atinge."""
    risk = entry_close - stop_price
    if risk <= 0: return None
    target_price = entry_close + target_R * risk
    # Varre bars futuros até alcançar stop ou target
    n = len(times)
    for j in range(entry_idx+1, n):
        b_next = master[times[j]]
        oh = b_next.get('ohlcv_last_40_bars') or []
        if not oh: continue
        h = oh[-1].get('high'); l = oh[-1].get('low')
        if h is None or l is None: continue
        # Verifica ordem intra-bar (assume worst case: stop primeiro se ambos batem)
        hit_stop = l <= stop_price
        hit_target = h >= target_price
        if hit_stop and hit_target: return -1.0  # conservador
        if hit_stop: return -1.0
        if hit_target: return target_R
    # Nem stop nem target em horizonte limitado — close at last bar
    last_b = master[times[-1]]
    last_close = (last_b.get('ohlcv_last_40_bars') or [{}])[-1].get('close')
    if last_close is None: return None
    return (last_close - entry_close) / risk


def compute_close_outcome(entry_idx, entry_close, stop_price, times, master, H=20):
    """R baseado em close[entry+H] / risk."""
    if entry_idx + H >= len(times): return None
    risk = entry_close - stop_price
    if risk <= 0: return None
    next_close = (master[times[entry_idx+H]].get('ohlcv_last_40_bars') or [{}])[-1].get('close')
    if next_close is None: return None
    return (next_close - entry_close) / risk


def stats_block(rs):
    if not rs: return None
    wins=sum(1 for r in rs if r>0)
    return {'n':len(rs),'win%':100*wins/len(rs),'avg_R':mean(rs),'sum_R':sum(rs)}


def main():
    print(f"=== REVERSAL_DISCRETIONARY V2 — Deferred Entry no Reteste DEMAND OB ===\n")

    per_w = {}
    for label, fname in WINDOWS_V6:
        p = JSONL_DIR / fname
        if not p.exists(): continue
        bars = load_bars(p)
        daily = synth_daily(bars)
        closes_d=[b['close'] for b in daily]; highs_d=[b['high'] for b in daily]
        dist14=[None]*len(daily)
        for i in range(len(daily)):
            w = highs_d[max(0,i-13):i+1]
            dist14[i]=(closes_d[i]-max(w))/max(w)*100
        per_w[label] = {'bars':bars,'daily':daily,'dist14':dist14}

    master={}; bt_window={}; bt_dist={}
    for label, data in per_w.items():
        for b in data['bars']:
            oh = b.get('ohlcv_last_40_bars') or []
            if not oh: continue
            t = oh[-1].get('time')
            if t is None or t in master: continue
            master[t]=b; bt_window[t]=label
            di=None
            for i in range(len(data['daily'])-1,-1,-1):
                if data['daily'][i]['time']<=t: di=i; break
            if di is not None and di<len(data['dist14']):
                bt_dist[t]=data['dist14'][di]
    times = sorted(master.keys())
    print(f"Master: {len(times)} bars\n")

    # Passo 1: Identifica REGIONAL_TRIGGERS (mesmo critério BASE V1)
    triggers = []  # (idx, time, window)
    for i,t in enumerate(times):
        b = master[t]
        oh = b.get('ohlcv_last_40_bars') or []
        if not oh: continue
        close = oh[-1].get('close')
        if close is None: continue
        atr = get_atr14(b)
        if not atr: continue
        if not has_nas_label(b, "LONG", 5): continue
        nd = get_nas_dist(b)
        if nd is None or nd > -1: continue
        d14 = bt_dist.get(t)
        if d14 is None or d14 > -5: continue
        lux = get_lux_labels(b, 20)
        if not (check_T1(lux) or check_T3(lux)): continue
        triggers.append((i, t, bt_window[t]))
    print(f"Regional triggers (V1 BASE base): {len(triggers)}\n")

    # Passo 2: Pra cada trigger, busca primeiro ENTRY válido (DEMAND touch SEM CHoCH filter)
    MAX_HORIZON = 50

    def build_trades(stop_buffer, require_bubble):
        trades_local = []
        used = set()
        for t_idx, t_time, t_window in triggers:
            max_f = min(t_idx + MAX_HORIZON, len(times))
            entry_found = None
            for f in range(t_idx+1, max_f):
                b_f = master[times[f]]
                oh_f = b_f.get('ohlcv_last_40_bars') or []
                if not oh_f: continue
                last = oh_f[-1]
                low_f = last.get('low'); close_f = last.get('close')
                if None in (low_f, close_f): continue
                atr_f = get_atr14(b_f)
                if not atr_f or atr_f<=0: continue

                demands = get_demand_boxes(b_f)
                best_demand = None
                for d in demands:
                    if low_f <= d['high']:
                        if best_demand is None or d['high'] > best_demand['high']:
                            best_demand = d
                if best_demand is None: continue

                entry_px = best_demand['high']
                stop_px = best_demand['low'] - stop_buffer * atr_f
                if stop_px >= entry_px: continue

                if require_bubble and not has_bubble_activation_lookback(b_f, 10): continue
                if f in used: continue

                entry_found = {
                    'entry_idx': f, 'entry_time': times[f], 'entry_close': entry_px,
                    'stop_price': stop_px, 'demand_high': best_demand['high'], 'demand_low': best_demand['low'],
                    'atr': atr_f, 'window': t_window, 'trigger_idx': t_idx, 'trigger_time': t_time,
                    'bars_to_entry': f - t_idx,
                }
                used.add(f)
                break
            if entry_found:
                trades_local.append(entry_found)
        return trades_local

    # 6 cenários: 3 buffers x (com/sem bubble)
    scenarios = []
    for sb in STOP_ATR_BUFFERS:
        for req_bub in (False, True):
            name = f"stop_{sb}xATR_{'BUB' if req_bub else 'NOBUB'}"
            scenarios.append((name, sb, req_bub))

    trade_sets = {}
    for name, sb, req_bub in scenarios:
        trades_local = build_trades(sb, req_bub)
        trade_sets[name] = trades_local
        if trades_local:
            b2e = [t['bars_to_entry'] for t in trades_local]
            print(f"  {name}: n={len(trades_local)}/{len(triggers)}, bars2entry median={sorted(b2e)[len(b2e)//2]}")
        else:
            print(f"  {name}: n=0")
    print()


    # Passo 3: Compute outcomes (4 variantes) — pra SIMPLE e FULL
    variants = [('Target 1.5R', 1.5, False), ('Target 2.0R', 2.0, False), ('Target 3.0R', 3.0, False), ('close H=20', None, True)]
    dream_ts = [(int(datetime.strptime(dt+"+0000","%Y-%m-%d %H:%M%z").timestamp()), tid) for tid,dt in DREAM_LONG]

    for trade_set_name, trades_set in trade_sets.items():
        print(f"=== {trade_set_name} — n_total={len(trades_set)} ===")
        print(f"  {'variant':<14s} {'n':>4s} {'win%':>5s} {'avg_R':>7s} {'sum_R':>8s} {'wp/we':>6s} {'recall':>12s}")
        print("  " + "-"*80)
        for vname, target_R, is_close in variants:
            results = []
            for tr in trades_set:
                if is_close:
                    r = compute_close_outcome(tr['entry_idx'], tr['entry_close'], tr['stop_price'], times, master, H=H_CLOSE)
                else:
                    r = compute_outcome(tr['entry_idx'], tr['entry_close'], tr['stop_price'], target_R, times, master)
                if r is None: continue
                results.append({'r':r, 'window':tr['window'], 'entry_time':tr['entry_time'], 'trigger_time':tr['trigger_time']})

            rs = [x['r'] for x in results]
            s = stats_block(rs)
            if not s or s['n']<3:
                print(f"  {vname:<14s} {s['n'] if s else 0:>4d}  (n insuficiente)"); continue
            per = defaultdict(list)
            for x in results: per[x['window']].append(x['r'])
            wp = sum(1 for w,rs_w in per.items() if len(rs_w)>=5 and stats_block(rs_w)['win%']>=WIN_GATE)
            we = sum(1 for w,rs_w in per.items() if len(rs_w)>=5)
            captured = set()
            for x in results:
                for d_ts, tid in dream_ts:
                    if abs(x['trigger_time']-d_ts)<=TOL or abs(x['entry_time']-d_ts)<=TOL:
                        captured.add(tid)
            recall = 100*len(captured)/len(dream_ts)
            mk = "★" if s['win%']>=WIN_GATE and s['n']>=10 else " "
            print(f"  {mk}{vname:<13s} {s['n']:>4d} {s['win%']:>5.1f} {s['avg_R']:>+7.2f} {s['sum_R']:>+8.2f} {wp:>2d}/{we:<2d} {recall:>4.0f}% ({len(captured)}/6)")
        print()

    # Comparação com V1 BASE
    print(f"--- Referência V1 BASE ---")
    print(f"  BASE T1+T3 (V1)        177  59.9   +0.72  +126.71  3/6     67% (4/6)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
