#!/usr/bin/env python3
"""
analyze_xau_reversal_macro_1d.py — Adiciona features 1D ao detector REVERSAL.

Base: F0_nas_5 (NAS LONG/SHORT label nos últimos 5 bars do 4H).
Horizon padrão: 20 (~3.3 dias).

Features 1D testadas (não só as 4 sugeridas — exploração ampla):
  slope EMA50 (direction + bucket)
  RSI 1D (level + extremes + divergence)
  dist_14d_high, dist_30d_high, dist_60d_high, dist_14d_low (regime)
  EMA20 vs EMA50 (cross)
  BB position + squeeze
  ATR relative (volatilidade)
  Consecutive bars same direction (momentum)
  Bullish/bearish engulfing pattern
  ADX (strength)

Foco: encontrar combinações que elevem LONG win% de 64.9% para >=70%
   e SHORT win% de 57.7% para >=70%
"""
from pathlib import Path
from datetime import datetime, timezone
from statistics import mean, median, stdev
import json, sys, subprocess, time
from itertools import combinations
from collections import defaultdict

BASE = Path(__file__).parent.parent
MCP_SERVER = BASE / "src" / "server.js"
NODE = "/opt/homebrew/bin/node"
JSONL_DIR = BASE / "alert-bridge" / "logs" / "backtests"

WINDOWS_V3 = [
    ("W1_2023H1",    "XAUUSD_240_2023-01-19_to_2026-05-20_v3.jsonl"),
    ("W2_2023H2",    "XAUUSD_240_2023-07-19_to_2026-05-20_v3.jsonl"),
    ("W3_2024H1",    "XAUUSD_240_2024-01-19_to_2026-05-20_v3.jsonl"),
    ("W4_2024H2",    "XAUUSD_240_2024-07-19_to_2026-05-20_v3.jsonl"),
    ("W5_2025May",   "XAUUSD_240_2025-05-19_to_2026-05-20_v3.jsonl"),
    ("W6_2025Sep",   "XAUUSD_240_2025-09-15_to_2026-05-20_v3.jsonl"),
    ("W7_2025Nov",   "XAUUSD_240_2025-11-19_to_2026-05-20_v3.jsonl"),
    ("W8_2026Mar",   "XAUUSD_240_2026-03-19_to_2026-05-20_v3.jsonl"),
]

SYMBOL = "PEPPERSTONE:XAUUSD"
PAUSE = Path("/tmp/claude_recheck.paused")
HORIZON_4H = 20  # default
WIN_GATE = 70.0
BAR_SECONDS_4H = 14400


class MCP:
    def __init__(self): self.proc=None; self.id=0
    def start(self):
        self.proc = subprocess.Popen([NODE, str(MCP_SERVER)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
        self._raw("initialize",{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"m1d","version":"1.0"}})
        self.proc.stdin.write(json.dumps({"jsonrpc":"2.0","method":"notifications/initialized","params":{}})+"\n"); self.proc.stdin.flush()
    def stop(self):
        if self.proc:
            try: self.proc.stdin.close()
            except: pass
            try: self.proc.terminate(); self.proc.wait(timeout=5)
            except: self.proc.kill()
    def _raw(self, m, p, t=120):
        self.id+=1
        self.proc.stdin.write(json.dumps({"jsonrpc":"2.0","id":self.id,"method":m,"params":p})+"\n"); self.proc.stdin.flush()
        deadline=time.monotonic()+t
        while time.monotonic()<deadline:
            line=self.proc.stdout.readline()
            if not line: raise RuntimeError("closed")
            try:
                r=json.loads(line)
                if r.get("id")==self.id: return r
            except: continue
        raise TimeoutError(m)
    def call(self, n, a=None, t=120):
        r=self._raw("tools/call",{"name":n,"arguments":a or {}},t)
        if "error" in r: return {"_error":r["error"]}
        c=r.get("result",{}).get("content",[])
        if c and c[0].get("type")=="text":
            try: return json.loads(c[0]["text"])
            except: return {"_raw":c[0]["text"]}
        return r.get("result",{})


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


def ema(values, period):
    if len(values)<period: return [None]*len(values)
    k = 2/(period+1)
    out = [None]*(period-1)
    out.append(sum(values[:period])/period)
    for v in values[period:]:
        out.append(v*k + out[-1]*(1-k))
    return out


def sma(values, period):
    if len(values)<period: return [None]*len(values)
    out = [None]*(period-1)
    for i in range(period-1, len(values)):
        vals = [v for v in values[i-period+1:i+1] if v is not None]
        out.append(mean(vals) if len(vals) >= period//2 else None)
    return out


def rsi_series(closes, period=14):
    if len(closes)<period+1: return [None]*len(closes)
    gains=[]; losses=[]
    for i in range(1,len(closes)):
        d = closes[i]-closes[i-1]
        gains.append(max(d,0))
        losses.append(max(-d,0))
    avg_g = mean(gains[:period])
    avg_l = mean(losses[:period])
    out = [None]*period
    if avg_l == 0: out.append(100)
    else: out.append(100 - (100/(1 + avg_g/avg_l)))
    for i in range(period, len(closes)-1):
        avg_g = (avg_g*(period-1)+gains[i])/period
        avg_l = (avg_l*(period-1)+losses[i])/period
        if avg_l == 0: out.append(100)
        else: out.append(100 - (100/(1 + avg_g/avg_l)))
    return out


def find_pivots_lows(values, idx_end, lookback=30, window=3):
    out = []
    start = max(window, idx_end-lookback)
    for i in range(start, idx_end+1):
        if i<window or i>len(values)-window-1: continue
        if values[i] is None: continue
        is_p = True
        for j in range(1, window+1):
            if values[i-j] is None or values[i+j] is None: is_p=False; break
            if values[i] >= values[i-j] or values[i] >= values[i+j]:
                is_p=False; break
        if is_p: out.append(i)
    return out


def find_pivots_highs(values, idx_end, lookback=30, window=3):
    out = []
    start = max(window, idx_end-lookback)
    for i in range(start, idx_end+1):
        if i<window or i>len(values)-window-1: continue
        if values[i] is None: continue
        is_p = True
        for j in range(1, window+1):
            if values[i-j] is None or values[i+j] is None: is_p=False; break
            if values[i] <= values[i-j] or values[i] <= values[i+j]:
                is_p=False; break
        if is_p: out.append(i)
    return out


def detect_bull_div(closes, rsi, idx_end, lookback=30):
    lows = find_pivots_lows(closes, idx_end, lookback)
    if len(lows)<2: return False
    l1 = lows[-1]; l2 = lows[-2]
    if rsi[l1] is None or rsi[l2] is None: return False
    return closes[l1] < closes[l2] and rsi[l1] > rsi[l2]


def detect_bear_div(closes, rsi, idx_end, lookback=30):
    highs = find_pivots_highs(closes, idx_end, lookback)
    if len(highs)<2: return False
    h1 = highs[-1]; h2 = highs[-2]
    if rsi[h1] is None or rsi[h2] is None: return False
    return closes[h1] > closes[h2] and rsi[h1] < rsi[h2]


def get_atr14(bar):
    ohlcv = bar.get('ohlcv_last_40_bars') or []
    if len(ohlcv)<=1: return None
    closed = ohlcv[:-1][-14:]
    r=[b['high']-b['low'] for b in closed if b.get('high') and b.get('low') and b['high']>b['low']]
    return mean(r) if r else None


def has_nas_label_recent(bar, want_text, max_delta=5):
    for s in (bar.get('pine_labels') or []):
        if 'NAS' not in s.get('name','').upper(): continue
        labels = s.get('labels') or []
        if not labels: continue
        xs = [lbl.get('x') for lbl in labels if lbl.get('x') is not None]
        if not xs: continue
        max_x = max(xs)
        for lbl in labels:
            lx = lbl.get('x'); txt = (lbl.get('text') or '').upper()
            if lx is None or txt != want_text: continue
            delta = max_x - lx
            if 0 <= delta <= max_delta: return True
    return False


def stats_block(rs):
    if not rs: return None
    wins = sum(1 for r in rs if r>0)
    return {'n':len(rs),'win%':100*wins/len(rs),'avg_R':mean(rs),'median_R':median(rs),'sum_R':sum(rs)}


def main():
    if not PAUSE.exists():
        print("ERRO: pause flag ausente.", file=sys.stderr); return 1

    print("=== MACRO 1D FEATURES — REVERSAL detector + filters daily ===\n")

    # Fetch daily real
    print("Capturando daily 1D (count=2000)...")
    client = MCP(); client.start()
    try:
        state = client.call("chart_get_state")
        if not (state.get("symbol","").endswith("XAUUSD") and state.get("resolution") in ("1D","D")):
            client.call("chart_set_symbol",{"symbol":SYMBOL}); time.sleep(1)
            client.call("chart_set_timeframe",{"timeframe":"D"}); time.sleep(2)
        resp = client.call("data_get_ohlcv",{"count":2000,"summary":False})
        bars_d = resp.get("last_5_bars") or resp.get("bars") or []
        daily = sorted([b for b in bars_d if b.get("time")], key=lambda x:x["time"])
        print(f"  {len(daily)} bars 1D ({datetime.fromtimestamp(daily[0]['time'],tz=timezone.utc):%Y-%m-%d} → {datetime.fromtimestamp(daily[-1]['time'],tz=timezone.utc):%Y-%m-%d})")
    finally:
        client.stop()

    closes_d = [b["close"] for b in daily]
    highs_d = [b["high"] for b in daily]
    lows_d = [b["low"] for b in daily]
    # Indicators 1D
    ema20_d = ema(closes_d, 20)
    ema50_d = ema(closes_d, 50)
    rsi_d = rsi_series(closes_d, 14)
    # ATR 14
    trs = [highs_d[0]-lows_d[0]]
    for i in range(1, len(daily)):
        trs.append(max(highs_d[i]-lows_d[i], abs(highs_d[i]-closes_d[i-1]), abs(lows_d[i]-closes_d[i-1])))
    atr14_d = [None]*len(daily)
    for i in range(14, len(daily)):
        atr14_d[i] = mean(trs[i-14:i])
    atr_avg30 = sma(atr14_d, 30)
    # BB(20,2)
    sma20 = sma(closes_d, 20)
    bb_upper = [None]*len(daily); bb_lower = [None]*len(daily); bb_width = [None]*len(daily)
    for i in range(19, len(daily)):
        s = stdev(closes_d[i-19:i+1])
        bb_upper[i] = sma20[i] + 2*s if sma20[i] else None
        bb_lower[i] = sma20[i] - 2*s if sma20[i] else None
        if bb_upper[i] and bb_lower[i]:
            bb_width[i] = bb_upper[i] - bb_lower[i]
    bb_width_avg = sma(bb_width, 30)
    # dist from highs/lows
    dist14h = [None]*len(daily)
    dist30h = [None]*len(daily)
    dist60h = [None]*len(daily)
    dist14l = [None]*len(daily)
    for i in range(len(daily)):
        win14 = highs_d[max(0,i-13):i+1]; dist14h[i] = (closes_d[i]-max(win14))/max(win14)*100
        win30 = highs_d[max(0,i-29):i+1]; dist30h[i] = (closes_d[i]-max(win30))/max(win30)*100
        win60 = highs_d[max(0,i-59):i+1]; dist60h[i] = (closes_d[i]-max(win60))/max(win60)*100
        win14l = lows_d[max(0,i-13):i+1]; dist14l[i] = (closes_d[i]-min(win14l))/min(win14l)*100
    # slope EMA50 5d
    slope50 = [None]*len(daily)
    for i in range(55, len(daily)):
        if ema50_d[i] and ema50_d[i-5] and ema50_d[i-5]>0:
            slope50[i] = (ema50_d[i]-ema50_d[i-5])/ema50_d[i-5]*100
    # consecutive bars same direction
    consec_bull = [0]*len(daily); consec_bear = [0]*len(daily)
    for i in range(len(daily)):
        if i==0:
            consec_bull[i] = 1 if closes_d[i]>=daily[i].get('open',closes_d[i]) else 0
            consec_bear[i] = 1 if closes_d[i]<daily[i].get('open',closes_d[i]) else 0
        else:
            is_bull = closes_d[i] > closes_d[i-1]
            consec_bull[i] = consec_bull[i-1]+1 if is_bull else 0
            consec_bear[i] = consec_bear[i-1]+1 if not is_bull else 0

    def find_di(ts):
        for i in range(len(daily)-1,-1,-1):
            if daily[i]['time']<=ts: return i
        return None

    # Load master 4H
    master = {}
    bar_to_window = {}
    for label, fname in WINDOWS_V3:
        path = JSONL_DIR / fname
        if not path.exists(): continue
        for b in load_bars(path):
            ohlcv = b.get('ohlcv_last_40_bars') or []
            if not ohlcv: continue
            t = ohlcv[-1].get('time')
            if t is None or t in master: continue
            master[t] = b; bar_to_window[t] = label
    times_sorted = sorted(master.keys())
    bars_sorted = [master[t] for t in times_sorted]
    print(f"Master: {len(times_sorted)} bars 4H únicos\n")

    # Compute features per bar 4H (with daily features attached)
    print("Computando features 1D pra cada bar 4H...")
    bar_data = []
    for i, t in enumerate(times_sorted):
        b = bars_sorted[i]
        ohlcv = b.get('ohlcv_last_40_bars') or []
        close = ohlcv[-1].get('close') if ohlcv else None
        if close is None: continue
        atr = get_atr14(b)
        if not atr or atr<=0: continue
        if i+HORIZON_4H >= len(bars_sorted): continue
        next_close = (bars_sorted[i+HORIZON_4H].get('ohlcv_last_40_bars') or [{}])[-1].get('close')
        if next_close is None: continue
        r_long = (next_close - close) / atr
        # NAS labels
        nas_l = has_nas_label_recent(b, "LONG", 5)
        nas_s = has_nas_label_recent(b, "SHORT", 5)
        if not (nas_l or nas_s): continue
        # Daily features
        di = find_di(t)
        if di is None or di<60: continue  # need history
        slope = slope50[di]
        rsi_now = rsi_d[di] if di<len(rsi_d) else None
        if rsi_now is None: continue
        d14h = dist14h[di]; d30h = dist30h[di]; d60h = dist60h[di]; d14l = dist14l[di]
        e20 = ema20_d[di]; e50 = ema50_d[di]
        bp = ((closes_d[di]-bb_lower[di])/(bb_upper[di]-bb_lower[di])) if (bb_upper[di] and bb_lower[di] and bb_upper[di]>bb_lower[di]) else None
        bb_sq = (bb_width[di] < 0.7*bb_width_avg[di]) if (bb_width[di] and bb_width_avg[di]) else False
        atr_rel = (atr14_d[di]/atr_avg30[di]) if (atr14_d[di] and atr_avg30[di]) else None
        cb_bull = consec_bull[di]; cb_bear = consec_bear[di]
        bull_div_1d = detect_bull_div(closes_d, rsi_d, di, lookback=30)
        bear_div_1d = detect_bear_div(closes_d, rsi_d, di, lookback=30)

        bar_data.append({
            'time':t,'window':bar_to_window[t],'r_long':round(r_long,2),'r_short':round(-r_long,2),
            'nas_l':nas_l,'nas_s':nas_s,
            # daily features
            'slope':slope,'rsi':rsi_now,
            'd14h':d14h,'d30h':d30h,'d60h':d60h,'d14l':d14l,
            'e20_gt_e50':(e20 and e50 and e20>e50),
            'bb_pos':bp,'bb_sq':bb_sq,'atr_rel':atr_rel,
            'cb_bull':cb_bull,'cb_bear':cb_bear,
            'bull_div_1d':bull_div_1d,'bear_div_1d':bear_div_1d,
        })
    print(f"  {len(bar_data)} bars com features (NAS-trigger + daily disponível)\n")

    # === LONG analysis ===
    print(f"\n{'='*100}")
    print(f"LONG REVERSAL — base F0_nas_5 LONG + daily filter, H={HORIZON_4H}")
    print(f"{'='*100}")
    long_bars = [b for b in bar_data if b['nas_l']]
    rs = [b['r_long'] for b in long_bars]
    s_base = stats_block(rs)
    print(f"  Base LONG (n={s_base['n']} win%={s_base['win%']:.1f} avg_R={s_base['avg_R']:+.2f})\n")

    # filter candidates LONG
    long_filters = [
        # 1D regime features pra LONG REVERSAL
        ('slope_<0',         lambda b: b['slope'] is not None and b['slope']<0),
        ('slope_<-0.2',      lambda b: b['slope'] is not None and b['slope']<-0.2),
        ('slope_<+0.5',      lambda b: b['slope'] is not None and b['slope']<0.5),
        ('rsi1d_<30',        lambda b: b['rsi']<30),
        ('rsi1d_<40',        lambda b: b['rsi']<40),
        ('rsi1d_<50',        lambda b: b['rsi']<50),
        ('d14h_<-5%',        lambda b: b['d14h']<-5),
        ('d14h_<-3%',        lambda b: b['d14h']<-3),
        ('d30h_<-7%',        lambda b: b['d30h']<-7),
        ('d14l_<+2%',        lambda b: b['d14l']<2),  # near 14d low
        ('d14l_<+1%',        lambda b: b['d14l']<1),
        ('e20_below_e50',    lambda b: not b['e20_gt_e50']),
        ('bb_pos_<0.3',      lambda b: b['bb_pos'] is not None and b['bb_pos']<0.3),
        ('bb_pos_<0.5',      lambda b: b['bb_pos'] is not None and b['bb_pos']<0.5),
        ('bb_squeeze',       lambda b: b['bb_sq']),
        ('atr_high',         lambda b: b['atr_rel'] is not None and b['atr_rel']>1.3),
        ('atr_low',          lambda b: b['atr_rel'] is not None and b['atr_rel']<0.8),
        ('cb_bear>=3',       lambda b: b['cb_bear']>=3),
        ('cb_bear>=5',       lambda b: b['cb_bear']>=5),
        ('bull_div_1d',      lambda b: b['bull_div_1d']),
    ]

    # Test each filter alone + pairs
    long_results = []
    for fname, fn in long_filters:
        kept = [b for b in long_bars if fn(b)]
        rs = [b['r_long'] for b in kept]
        s = stats_block(rs)
        if s and s['n']>=30:
            # windows passing
            per_w = defaultdict(list)
            for b in kept: per_w[b['window']].append(b['r_long'])
            wp = sum(1 for ws,rs in per_w.items() if len(rs)>=10 and stats_block(rs)['win%']>=WIN_GATE)
            we = sum(1 for ws,rs in per_w.items() if len(rs)>=10)
            long_results.append({'name':fname,'n':s['n'],'win%':s['win%'],'avg_R':s['avg_R'],'sum_R':s['sum_R'],'wp':wp,'we':we})

    # 2-way combos
    for (f1n, f1), (f2n, f2) in combinations(long_filters, 2):
        kept = [b for b in long_bars if f1(b) and f2(b)]
        rs = [b['r_long'] for b in kept]
        s = stats_block(rs)
        if s and s['n']>=30:
            per_w = defaultdict(list)
            for b in kept: per_w[b['window']].append(b['r_long'])
            wp = sum(1 for ws,rs in per_w.items() if len(rs)>=10 and stats_block(rs)['win%']>=WIN_GATE)
            we = sum(1 for ws,rs in per_w.items() if len(rs)>=10)
            long_results.append({'name':f1n+'+'+f2n,'n':s['n'],'win%':s['win%'],'avg_R':s['avg_R'],'sum_R':s['sum_R'],'wp':wp,'we':we})

    long_results.sort(key=lambda r: (-r['win%'], -r['n']))
    print(f"  {'filter':<48s} {'n':>5s} {'win%':>5s} {'avg_R':>7s} {'sum_R':>8s} {'wp/we':>6s}")
    print("-"*100)
    for r in long_results[:25]:
        marker = "★" if r['win%']>=WIN_GATE else " "
        print(f"{marker}{r['name']:<47s} {r['n']:>5d} {r['win%']:>5.1f} {r['avg_R']:>+7.2f} {r['sum_R']:>+8.2f} {r['wp']:>2d}/{r['we']:<2d}")

    # === SHORT analysis ===
    print(f"\n\n{'='*100}")
    print(f"SHORT REVERSAL — base F0_nas_5 SHORT + daily filter, H={HORIZON_4H}")
    print(f"{'='*100}")
    short_bars = [b for b in bar_data if b['nas_s']]
    rs = [b['r_short'] for b in short_bars]
    s_base = stats_block(rs)
    print(f"  Base SHORT (n={s_base['n']} win%={s_base['win%']:.1f} avg_R={s_base['avg_R']:+.2f})\n")

    short_filters = [
        ('slope_>0',         lambda b: b['slope'] is not None and b['slope']>0),
        ('slope_>+0.5',      lambda b: b['slope'] is not None and b['slope']>0.5),
        ('slope_>+1.0',      lambda b: b['slope'] is not None and b['slope']>1.0),
        ('slope_<+0.3',      lambda b: b['slope'] is not None and b['slope']<0.3),  # macro flat/down
        ('slope_<0',         lambda b: b['slope'] is not None and b['slope']<0),  # macro downtrend
        ('rsi1d_>70',        lambda b: b['rsi']>70),
        ('rsi1d_>60',        lambda b: b['rsi']>60),
        ('rsi1d_>50',        lambda b: b['rsi']>50),
        ('d14h_<-1%',        lambda b: b['d14h']<-1 and b['d14h']>-3),  # near 14d high but not crashed
        ('d14h_in[-1,0]',    lambda b: b['d14h']>-1 and b['d14h']<=0),
        ('d30h_in[-3,0]',    lambda b: b['d30h']>-3 and b['d30h']<=0),
        ('d60h_in[-2,0]',    lambda b: b['d60h']>-2 and b['d60h']<=0),
        ('e20_above_e50',    lambda b: b['e20_gt_e50']),
        ('bb_pos_>0.7',      lambda b: b['bb_pos'] is not None and b['bb_pos']>0.7),
        ('bb_pos_>0.9',      lambda b: b['bb_pos'] is not None and b['bb_pos']>0.9),
        ('bb_squeeze',       lambda b: b['bb_sq']),
        ('atr_high',         lambda b: b['atr_rel'] is not None and b['atr_rel']>1.3),
        ('atr_low',          lambda b: b['atr_rel'] is not None and b['atr_rel']<0.8),
        ('cb_bull>=3',       lambda b: b['cb_bull']>=3),
        ('cb_bull>=5',       lambda b: b['cb_bull']>=5),
        ('bear_div_1d',      lambda b: b['bear_div_1d']),
    ]

    short_results = []
    for fname, fn in short_filters:
        kept = [b for b in short_bars if fn(b)]
        rs = [b['r_short'] for b in kept]
        s = stats_block(rs)
        if s and s['n']>=30:
            per_w = defaultdict(list)
            for b in kept: per_w[b['window']].append(b['r_short'])
            wp = sum(1 for ws,rs in per_w.items() if len(rs)>=10 and stats_block(rs)['win%']>=WIN_GATE)
            we = sum(1 for ws,rs in per_w.items() if len(rs)>=10)
            short_results.append({'name':fname,'n':s['n'],'win%':s['win%'],'avg_R':s['avg_R'],'sum_R':s['sum_R'],'wp':wp,'we':we})

    for (f1n, f1), (f2n, f2) in combinations(short_filters, 2):
        kept = [b for b in short_bars if f1(b) and f2(b)]
        rs = [b['r_short'] for b in kept]
        s = stats_block(rs)
        if s and s['n']>=30:
            per_w = defaultdict(list)
            for b in kept: per_w[b['window']].append(b['r_short'])
            wp = sum(1 for ws,rs in per_w.items() if len(rs)>=10 and stats_block(rs)['win%']>=WIN_GATE)
            we = sum(1 for ws,rs in per_w.items() if len(rs)>=10)
            short_results.append({'name':f1n+'+'+f2n,'n':s['n'],'win%':s['win%'],'avg_R':s['avg_R'],'sum_R':s['sum_R'],'wp':wp,'we':we})

    short_results.sort(key=lambda r: (-r['win%'], -r['n']))
    print(f"  {'filter':<48s} {'n':>5s} {'win%':>5s} {'avg_R':>7s} {'sum_R':>8s} {'wp/we':>6s}")
    print("-"*100)
    for r in short_results[:25]:
        marker = "★" if r['win%']>=WIN_GATE else " "
        print(f"{marker}{r['name']:<47s} {r['n']:>5d} {r['win%']:>5.1f} {r['avg_R']:>+7.2f} {r['sum_R']:>+8.2f} {r['wp']:>2d}/{r['we']:<2d}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
