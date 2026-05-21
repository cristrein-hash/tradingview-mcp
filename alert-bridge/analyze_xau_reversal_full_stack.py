#!/usr/bin/env python3
"""
analyze_xau_reversal_full_stack.py — Empilha filtros adicionais sobre BASE.

BASE atual (validada): F0_nas_5 + rsi1d_<50 + atr_high → 83.7% win, 86 trades

Sobre essa base, testa adicionais:

  Categoria A (1D adicionais):
    F_A1 hammer_1d       — daily hammer (lower wick > 2×body + bull body)
    F_A2 bull_engulf_1d  — bullish engulfing 1D
    F_A3 ema20x50_recent — EMA20 cruzou acima EMA50 últimos 5 dias
    F_A4 dist_14d_low<3  — preço a no máximo +3% do low 14d (perto do fundo)
    F_A5 adx_1d>25       — ADX 1D > 25 (movimento forte/capitulação)
    F_A6 rsi_bull_div_1d — RSI divergence Bull 1D (lookback 50)

  Categoria B (4H adicionais):
    F_B1 bubble_sell_4h  — Bubble Sell exhaustion 4H (lookback 10)
    F_B2 ob_demand_prox  — OB demand proximity (IN ou ±50%)
    F_B3 sweep_low_4h    — low atual < min 5 bars + close > open
    F_B4 hammer_4h       — hammer 4H
    F_B5 bull_engulf_4h  — bullish engulfing 4H
    F_B6 vol_spike_4h    — volume > 1.5× média 10 bars

Encontrar combos que sobem win >=87% mantendo n>=30 e melhorando wp/we.
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
HORIZON_4H = 20
WIN_GATE = 70.0
BAR_SECONDS_4H = 14400
COLOR_BULL = 2572201804
COLOR_BEAR = 2566953215
SELL_PLOTS = {"plot_0", "plot_10"}


class MCP:
    def __init__(self): self.proc=None; self.id=0
    def start(self):
        self.proc = subprocess.Popen([NODE, str(MCP_SERVER)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
        self._raw("initialize",{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"fs","version":"1.0"}})
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
    avg_g = mean(gains[:period]); avg_l = mean(losses[:period])
    out = [None]*period
    if avg_l==0: out.append(100)
    else: out.append(100-(100/(1+avg_g/avg_l)))
    for i in range(period, len(closes)-1):
        avg_g = (avg_g*(period-1)+gains[i])/period
        avg_l = (avg_l*(period-1)+losses[i])/period
        if avg_l==0: out.append(100)
        else: out.append(100-(100/(1+avg_g/avg_l)))
    return out


def adx_series(highs, lows, closes, period=14):
    """ADX classical (Wilder)."""
    n = len(closes)
    if n<period+1: return [None]*n
    tr = []; pdm = []; mdm = []
    for i in range(1, n):
        tr.append(max(highs[i]-lows[i], abs(highs[i]-closes[i-1]), abs(lows[i]-closes[i-1])))
        up_move = highs[i]-highs[i-1]
        down_move = lows[i-1]-lows[i]
        pdm.append(up_move if up_move>down_move and up_move>0 else 0)
        mdm.append(down_move if down_move>up_move and down_move>0 else 0)
    # smoothed
    atr_s = [None]*period + [sum(tr[:period])]
    p_s = [None]*period + [sum(pdm[:period])]
    m_s = [None]*period + [sum(mdm[:period])]
    for i in range(period+1, n):
        atr_s.append(atr_s[-1] - atr_s[-1]/period + tr[i-1])
        p_s.append(p_s[-1] - p_s[-1]/period + pdm[i-1])
        m_s.append(m_s[-1] - m_s[-1]/period + mdm[i-1])
    pdi = [None]*n; mdi = [None]*n; dx = [None]*n
    for i in range(period, n):
        if atr_s[i] and atr_s[i]>0:
            pdi[i] = 100*p_s[i]/atr_s[i]
            mdi[i] = 100*m_s[i]/atr_s[i]
            denom = pdi[i]+mdi[i]
            if denom>0: dx[i] = 100*abs(pdi[i]-mdi[i])/denom
    adx = [None]*n
    # initial adx = mean of first 14 dx
    dx_vals = [d for d in dx if d is not None]
    if len(dx_vals)<period: return adx
    first_adx_idx = period*2
    if first_adx_idx >= n: return adx
    adx[first_adx_idx] = mean([d for d in dx[period:first_adx_idx+1] if d is not None][-period:])
    for i in range(first_adx_idx+1, n):
        if dx[i] is not None and adx[i-1] is not None:
            adx[i] = (adx[i-1]*(period-1) + dx[i])/period
    return adx


def find_pivots_lows(values, idx_end, lookback=50, window=3):
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


def detect_bull_div(closes, rsi, idx_end, lookback=50):
    lows = find_pivots_lows(closes, idx_end, lookback)
    if len(lows)<2: return False
    l1 = lows[-1]; l2 = lows[-2]
    if rsi[l1] is None or rsi[l2] is None: return False
    return closes[l1] < closes[l2] and rsi[l1] > rsi[l2]


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


def has_bubble_sell_4h(bar, lookback=10):
    entry_time = (bar.get('ohlcv_last_40_bars') or [{}])[-1].get('time')
    if entry_time is None: return False
    t_lb = entry_time - (lookback-1)*BAR_SECONDS_4H
    for s in (bar.get('pine_shapes_bubbles') or []):
        if 'Bubbles' not in s.get('name',''): continue
        for act in s.get('activations', []):
            t = act.get('time')
            if t is None: continue
            if t_lb <= t <= entry_time:
                for p in (act.get('shapes') or {}):
                    if p in SELL_PLOTS: return True
    return False


def has_ob_demand(bar):
    close = (bar.get('ohlcv_last_40_bars') or [{}])[-1].get('close')
    if close is None: return False
    for s in (bar.get('pine_boxes') or []):
        if 'Custom OB' not in s.get('name',''): continue
        for box in (s.get('all_boxes') or []):
            hi, lo = box.get('high'), box.get('low')
            bc = box.get('borderColor')
            if hi is None or lo is None or bc != COLOR_BULL: continue
            zone_size = hi - lo
            if zone_size <= 0: continue
            if lo <= close <= hi: return True
            dist = max((close-hi) if close>hi else 0, (lo-close) if close<lo else 0)
            if dist <= zone_size * 0.5: return True
    return False


def is_sweep_low_4h(bar, lookback=5):
    """Low atual < min últimos N bars + close > open (rejection)."""
    ohlcv = bar.get('ohlcv_last_40_bars') or []
    if len(ohlcv) < lookback+1: return False
    cur = ohlcv[-1]
    prev = ohlcv[-(lookback+1):-1]
    min_prev_low = min(b['low'] for b in prev if b.get('low'))
    return cur['low'] < min_prev_low and cur['close'] > cur['open']


def is_hammer(o, h, l, c):
    body = abs(c - o)
    if body == 0: return False
    range_total = h - l
    if range_total == 0: return False
    lower_wick = min(o, c) - l
    upper_wick = h - max(o, c)
    return lower_wick > 2*body and lower_wick > upper_wick


def is_bull_engulfing(prev, cur):
    prev_bearish = prev['close'] < prev['open']
    cur_bullish = cur['close'] > cur['open']
    if not (prev_bearish and cur_bullish): return False
    return cur['open'] <= prev['close'] and cur['close'] >= prev['open']


def is_volume_spike(bar, threshold=1.5, lookback=10):
    ohlcv = bar.get('ohlcv_last_40_bars') or []
    if len(ohlcv) < lookback+1: return False
    cur_vol = ohlcv[-1].get('volume')
    if cur_vol is None or cur_vol <= 0: return False
    prev_vols = [b['volume'] for b in ohlcv[-(lookback+1):-1] if b.get('volume')]
    if not prev_vols: return False
    avg_vol = mean(prev_vols)
    return cur_vol > threshold * avg_vol


def stats_block(rs):
    if not rs: return None
    wins = sum(1 for r in rs if r>0)
    return {'n':len(rs),'win%':100*wins/len(rs),'avg_R':mean(rs),'median_R':median(rs),'sum_R':sum(rs)}


def main():
    if not PAUSE.exists():
        print("ERRO: pause flag ausente.", file=sys.stderr); return 1

    print("=== FULL STACK — REVERSAL LONG: BASE + Cat A + Cat B ===\n")

    # Fetch daily
    print("Capturando daily 1D (count=2000)...")
    client = MCP(); client.start()
    try:
        resp = client.call("data_get_ohlcv",{"count":2000,"summary":False})
        bars_d = resp.get("last_5_bars") or resp.get("bars") or []
        daily = sorted([b for b in bars_d if b.get("time")], key=lambda x:x["time"])
        print(f"  {len(daily)} bars 1D ({datetime.fromtimestamp(daily[0]['time'],tz=timezone.utc):%Y-%m-%d} → {datetime.fromtimestamp(daily[-1]['time'],tz=timezone.utc):%Y-%m-%d})")
    finally:
        client.stop()

    closes_d = [b["close"] for b in daily]
    highs_d = [b["high"] for b in daily]
    lows_d = [b["low"] for b in daily]
    opens_d = [b["open"] for b in daily]

    # 1D indicators
    ema20_d = ema(closes_d, 20)
    ema50_d = ema(closes_d, 50)
    rsi_d = rsi_series(closes_d, 14)
    adx_d = adx_series(highs_d, lows_d, closes_d, 14)
    trs = [highs_d[0]-lows_d[0]]
    for i in range(1, len(daily)):
        trs.append(max(highs_d[i]-lows_d[i], abs(highs_d[i]-closes_d[i-1]), abs(lows_d[i]-closes_d[i-1])))
    atr14_d = [None]*len(daily)
    for i in range(14, len(daily)):
        atr14_d[i] = mean(trs[i-14:i])
    atr_avg30 = sma(atr14_d, 30)
    # dist 14d low
    dist14l_d = [None]*len(daily)
    for i in range(len(daily)):
        win = lows_d[max(0,i-13):i+1]
        dist14l_d[i] = (closes_d[i]-min(win))/min(win)*100
    # ema20 cross above ema50 dentro últimos 5 dias
    ema20x50_recent = [False]*len(daily)
    for i in range(5, len(daily)):
        above_now = (ema20_d[i] and ema50_d[i] and ema20_d[i] > ema50_d[i])
        below_5d_ago = (ema20_d[i-5] and ema50_d[i-5] and ema20_d[i-5] < ema50_d[i-5])
        ema20x50_recent[i] = above_now and below_5d_ago
    # hammer daily
    hammer_d = [False]*len(daily)
    for i in range(len(daily)):
        hammer_d[i] = is_hammer(opens_d[i], highs_d[i], lows_d[i], closes_d[i])
    # bull engulfing daily
    engulf_d = [False]*len(daily)
    for i in range(1, len(daily)):
        engulf_d[i] = is_bull_engulfing(daily[i-1], daily[i])
    # bull div extended (lookback 50)
    bull_div_ext = [False]*len(daily)
    for i in range(50, len(daily)):
        bull_div_ext[i] = detect_bull_div(closes_d, rsi_d, i, lookback=50)

    def find_di(ts):
        for i in range(len(daily)-1,-1,-1):
            if daily[i]['time']<=ts: return i
        return None

    # Load 4H master
    master = {}; bar_to_window = {}
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

    # Compute features per bar
    print("Computando features 4H + 1D...")
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
        nas_l = has_nas_label_recent(b, "LONG", 5)
        if not nas_l: continue  # já filtra direto na base
        di = find_di(t)
        if di is None or di<60: continue
        rsi_now = rsi_d[di] if di<len(rsi_d) else None
        if rsi_now is None: continue
        # BASE filters
        if rsi_now >= 50: continue  # rsi1d < 50
        atr_rel = (atr14_d[di]/atr_avg30[di]) if (atr14_d[di] and atr_avg30[di]) else None
        if atr_rel is None or atr_rel <= 1.3: continue  # atr_high
        # Categoria A features (1D)
        cur_4h = ohlcv[-1]
        prev_4h = ohlcv[-2] if len(ohlcv)>=2 else None
        feats = {
            'F_A1_hammer_1d':     hammer_d[di],
            'F_A2_engulf_1d':     engulf_d[di],
            'F_A3_ema20x50_5d':   ema20x50_recent[di],
            'F_A4_dist14l_<3':    (dist14l_d[di] is not None and dist14l_d[di] < 3),
            'F_A5_adx_>25':       (adx_d[di] is not None and adx_d[di] > 25),
            'F_A6_rsi_bull_div':  bull_div_ext[di],
            # Categoria B (4H)
            'F_B1_bub_sell_4h':   has_bubble_sell_4h(b, 10),
            'F_B2_ob_demand':     has_ob_demand(b),
            'F_B3_sweep_low_4h':  is_sweep_low_4h(b, 5),
            'F_B4_hammer_4h':     is_hammer(cur_4h['open'], cur_4h['high'], cur_4h['low'], cur_4h['close']),
            'F_B5_engulf_4h':     (prev_4h and is_bull_engulfing(prev_4h, cur_4h)),
            'F_B6_vol_spike_4h':  is_volume_spike(b, 1.5, 10),
        }
        bar_data.append({'time':t,'window':bar_to_window[t],'r_long':round(r_long,2),'feats':feats})

    n_base = len(bar_data)
    print(f"  {n_base} bars base (NAS+RSI<50+ATR_high)\n")
    base_rs = [b['r_long'] for b in bar_data]
    base_stats = stats_block(base_rs)
    print(f"BASE STATS: n={base_stats['n']} win%={base_stats['win%']:.1f} avg_R={base_stats['avg_R']:+.2f} sum_R={base_stats['sum_R']:+.2f}\n")

    # Test cada feature isolada + pares
    features = list(bar_data[0]['feats'].keys()) if bar_data else []
    results = []
    # singles
    for f in features:
        kept = [b for b in bar_data if b['feats'][f]]
        rs = [b['r_long'] for b in kept]
        s = stats_block(rs)
        if not s or s['n']<10: continue
        per_w = defaultdict(list)
        for b in kept: per_w[b['window']].append(b['r_long'])
        wp = sum(1 for w,rs in per_w.items() if len(rs)>=10 and stats_block(rs)['win%']>=WIN_GATE)
        we = sum(1 for w,rs in per_w.items() if len(rs)>=10)
        results.append({'name':f,'n':s['n'],'win%':s['win%'],'avg_R':s['avg_R'],'sum_R':s['sum_R'],'wp':wp,'we':we})
    # pairs
    for f1, f2 in combinations(features, 2):
        kept = [b for b in bar_data if b['feats'][f1] and b['feats'][f2]]
        rs = [b['r_long'] for b in kept]
        s = stats_block(rs)
        if not s or s['n']<15: continue
        per_w = defaultdict(list)
        for b in kept: per_w[b['window']].append(b['r_long'])
        wp = sum(1 for w,rs in per_w.items() if len(rs)>=10 and stats_block(rs)['win%']>=WIN_GATE)
        we = sum(1 for w,rs in per_w.items() if len(rs)>=10)
        results.append({'name':f1+'+'+f2,'n':s['n'],'win%':s['win%'],'avg_R':s['avg_R'],'sum_R':s['sum_R'],'wp':wp,'we':we})
    # triples
    for f1, f2, f3 in combinations(features, 3):
        kept = [b for b in bar_data if b['feats'][f1] and b['feats'][f2] and b['feats'][f3]]
        rs = [b['r_long'] for b in kept]
        s = stats_block(rs)
        if not s or s['n']<15: continue
        per_w = defaultdict(list)
        for b in kept: per_w[b['window']].append(b['r_long'])
        wp = sum(1 for w,rs in per_w.items() if len(rs)>=10 and stats_block(rs)['win%']>=WIN_GATE)
        we = sum(1 for w,rs in per_w.items() if len(rs)>=10)
        # short label name
        short = f1.replace('F_','')+'+'+f2.replace('F_','')+'+'+f3.replace('F_','')
        results.append({'name':short,'n':s['n'],'win%':s['win%'],'avg_R':s['avg_R'],'sum_R':s['sum_R'],'wp':wp,'we':we})

    # Sort por win% (priorizar melhoria vs base)
    results.sort(key=lambda r: (-r['win%'], -r['n']))
    print(f"=== TOP 60 ADDITIONALS (n>=10 single, >=15 pair/triple) ===")
    print(f"  base: win%={base_stats['win%']:.1f} n={base_stats['n']}")
    print(f"\n{'filter':<70s} {'n':>4s} {'win%':>5s} {'Δwin':>5s} {'avg_R':>7s} {'sum_R':>8s} {'wp/we':>6s}")
    print("-"*125)
    for r in results[:60]:
        marker = "★" if r['win%']>=87 and r['n']>=30 else (" ★" if r['win%']>=85 else "  ")
        delta = r['win%']-base_stats['win%']
        print(f"{marker}{r['name']:<53s} {r['n']:>4d} {r['win%']:>5.1f} {delta:>+5.1f} {r['avg_R']:>+7.2f} {r['sum_R']:>+8.2f} {r['wp']:>2d}/{r['we']:<2d}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
