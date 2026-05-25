#!/usr/bin/env python3
"""
analyze_xau_reversal_stoptarget.py — Outcome com Stop/Target REAL (não close-only).

Pra cada setup REVERSAL LONG, simula:
  - Entry no close do bar de trigger
  - Stop = entry - stop_atr × ATR (default 1.5)
  - Target = entry + target_atr × ATR (default 3.0)
  - Look-forward até max_bars (default 40 = ~6.7 dias)
  - Outcome: WIN se target hit primeiro, LOSS se stop hit, TIMEOUT se nenhum
  - R = target_atr se WIN, -stop_atr se LOSS, (last_close-entry)/ATR se TIMEOUT

Compara setups:
  S1. REVERSAL_CAPITULATION: NAS_5 + RSI_1D<50 + ATR_high (validado close-only 83.7%)
  S2. REVERSAL_DISCRETIONARY candidate: NAS_d0 + NAS_DIST<=-1 + dist14h<=-7%
  S3. Outras variantes

Dataset: v4 (com text="DEMAND"/"SUPPLY" capturado).
"""
from pathlib import Path
from datetime import datetime, timezone
from statistics import mean, median
import json, sys, subprocess, time
from collections import defaultdict

BASE = Path(__file__).parent.parent
JSONL_DIR = BASE / "alert-bridge" / "logs" / "backtests"
MCP_SERVER = BASE / "src" / "server.js"
NODE = "/opt/homebrew/bin/node"
PAUSE = Path("/tmp/claude_recheck.paused")

WINDOWS_V4 = [
    ("W1_2023H1",    "XAUUSD_240_2023-01-19_to_2026-05-21_v4.jsonl"),
    ("W2_2023H2",    "XAUUSD_240_2023-07-19_to_2026-05-21_v4.jsonl"),
    ("W3_2024H1",    "XAUUSD_240_2024-01-19_to_2026-05-21_v4.jsonl"),
    ("W4_2024H2",    "XAUUSD_240_2024-07-19_to_2026-05-21_v4.jsonl"),
    ("W5_2025May",   "XAUUSD_240_2025-05-19_to_2026-05-21_v4.jsonl"),
    ("W6_2025Sep",   "XAUUSD_240_2025-09-15_to_2026-05-21_v4.jsonl"),
    ("W7_2025Nov",   "XAUUSD_240_2025-11-19_to_2026-05-21_v4.jsonl"),
    ("W8_2026Mar",   "XAUUSD_240_2026-03-19_to_2026-05-21_v4.jsonl"),
]

# Parâmetros stop/target
STOP_ATR = 1.5  # stop a 1.5 × ATR abaixo do entry
TARGET_ATR = 3.0  # target a 3.0 × ATR acima
MAX_BARS = 40  # look-forward máximo (timeout)
BAR_SECONDS_4H = 14400
WIN_GATE = 70.0
SELL_PLOTS = {"plot_0", "plot_10"}


class MCP:
    def __init__(self): self.proc=None; self.id=0
    def start(self):
        self.proc = subprocess.Popen([NODE, str(MCP_SERVER)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
        self._raw("initialize",{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"st","version":"1.0"}})
        self.proc.stdin.write(json.dumps({"jsonrpc":"2.0","method":"notifications/initialized","params":{}})+"\n"); self.proc.stdin.flush()
    def stop(self):
        if self.proc:
            try: self.proc.stdin.close()
            except: pass
            try: self.proc.terminate(); self.proc.wait(timeout=5)
            except: self.proc.kill()
    def _raw(self, m, p, t=60):
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
        return None
    def call(self, n, a=None, t=60):
        r=self._raw("tools/call",{"name":n,"arguments":a or {}},t)
        if "error" in r: return {}
        c=r.get("result",{}).get("content",[])
        if c and c[0].get("type")=="text":
            try: return json.loads(c[0]["text"])
            except: return {}
        return {}


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


def rsi_series(closes, period=14):
    if len(closes)<period+1: return [None]*len(closes)
    g,l=[],[]
    for i in range(1,len(closes)):
        d=closes[i]-closes[i-1]; g.append(max(d,0)); l.append(max(-d,0))
    ag=mean(g[:period]); al=mean(l[:period])
    out=[None]*period
    out.append(100 if al==0 else 100-(100/(1+ag/al)))
    for i in range(period, len(closes)-1):
        ag = (ag*(period-1)+g[i])/period
        al = (al*(period-1)+l[i])/period
        out.append(100 if al==0 else 100-(100/(1+ag/al)))
    return out


def sma(values, period):
    out=[None]*(period-1)
    for i in range(period-1, len(values)):
        vals = [v for v in values[i-period+1:i+1] if v is not None]
        out.append(mean(vals) if len(vals)>=period//2 else None)
    return out


def get_atr14(bar):
    ohlcv = bar.get('ohlcv_last_40_bars') or []
    if len(ohlcv)<=1: return None
    closed = ohlcv[:-1][-14:]
    r=[b['high']-b['low'] for b in closed if b.get('high') and b.get('low') and b['high']>b['low']]
    return mean(r) if r else None


def has_nas_label(bar, want_text, max_delta=5, exact_zero=False):
    for s in (bar.get('pine_labels') or []):
        if 'NAS' not in s.get('name','').upper(): continue
        labels = s.get('labels') or []
        if not labels: continue
        xs = [l.get('x') for l in labels if l.get('x') is not None]
        if not xs: continue
        max_x = max(xs)
        for l in labels:
            lx = l.get('x'); txt = (l.get('text') or '').upper()
            if lx is None or txt != want_text: continue
            delta = max_x - lx
            if exact_zero and delta == 0: return True
            if not exact_zero and 0 <= delta <= max_delta: return True
    return False


def get_nas_dist(bar):
    for s in (bar.get('study_values') or []):
        if 'NAS' in s.get('name',''):
            try: return float(s.get('values',{}).get('NAS_DISTANCE_FROM_EMA_ATR','').replace('−','-'))
            except: return None
    return None


def has_ob_demand_text(bar):
    """Usa text='DEMAND' do v4 ao invés de borderColor."""
    close = (bar.get('ohlcv_last_40_bars') or [{}])[-1].get('close')
    if close is None: return False
    for s in (bar.get('pine_boxes') or []):
        if 'Custom OB' not in s.get('name',''): continue
        for box in (s.get('all_boxes') or []):
            hi, lo = box.get('high'), box.get('low')
            text = box.get('text')
            if hi is None or lo is None or text != 'DEMAND': continue
            zone_size = hi - lo
            if zone_size <= 0: continue
            if lo <= close <= hi: return True
            dist = max((close-hi) if close>hi else 0, (lo-close) if close<lo else 0)
            if dist <= zone_size * 0.5: return True
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


def simulate_stop_target_long(bars_sorted, entry_idx, atr, stop_atr=STOP_ATR, target_atr=TARGET_ATR, max_bars=MAX_BARS):
    """Simula trade LONG com stop/target. Retorna (outcome_R, hit_bar, hit_type)."""
    entry_bar = bars_sorted[entry_idx]
    ohlcv_e = entry_bar.get('ohlcv_last_40_bars') or []
    entry_close = ohlcv_e[-1].get('close') if ohlcv_e else None
    if entry_close is None: return None
    stop_price = entry_close - stop_atr * atr
    target_price = entry_close + target_atr * atr
    # Iterate forward through next bars
    for offset in range(1, max_bars+1):
        if entry_idx + offset >= len(bars_sorted): break
        next_bar = bars_sorted[entry_idx + offset]
        ohlcv_n = next_bar.get('ohlcv_last_40_bars') or []
        if not ohlcv_n: continue
        b = ohlcv_n[-1]
        b_high = b.get('high'); b_low = b.get('low'); b_close = b.get('close')
        if b_high is None or b_low is None: continue
        # Check stop hit first (conservador — assume worst case se ambos no mesmo candle)
        if b_low <= stop_price:
            # stop hit
            return (-stop_atr, offset, 'STOP')
        if b_high >= target_price:
            # target hit
            return (target_atr, offset, 'TARGET')
    # Timeout: use last available close
    last_idx = min(entry_idx + max_bars, len(bars_sorted)-1)
    last_close = (bars_sorted[last_idx].get('ohlcv_last_40_bars') or [{}])[-1].get('close')
    if last_close is None: return None
    timeout_r = (last_close - entry_close) / atr
    return (timeout_r, max_bars, 'TIMEOUT')


def stats_block(rs, outcomes=None):
    if not rs: return None
    wins = sum(1 for r in rs if r>0)
    out = {'n':len(rs),'win%':100*wins/len(rs),'avg_R':mean(rs),'median_R':median(rs),'sum_R':sum(rs)}
    if outcomes:
        out['target_hits'] = sum(1 for o in outcomes if o=='TARGET')
        out['stop_hits'] = sum(1 for o in outcomes if o=='STOP')
        out['timeouts'] = sum(1 for o in outcomes if o=='TIMEOUT')
    return out


def main():
    if not PAUSE.exists():
        print("ERRO: pause flag ausente.", file=sys.stderr); return 1

    print(f"=== STOP/TARGET ANALYSIS — REVERSAL LONG ===")
    print(f"Stop: ATR × {STOP_ATR}  Target: ATR × {TARGET_ATR}  Max bars: {MAX_BARS}\n")

    # Daily
    client = MCP(); client.start()
    try:
        resp = client.call("data_get_ohlcv",{"count":2000,"summary":False})
        bars_d = resp.get("last_5_bars") or resp.get("bars") or []
        daily = sorted([b for b in bars_d if b.get("time")], key=lambda x: x["time"])
        print(f"Daily: {len(daily)} bars")
    finally:
        client.stop()

    closes_d = [b['close'] for b in daily]
    highs_d = [b['high'] for b in daily]
    lows_d = [b['low'] for b in daily]
    rsi_d = rsi_series(closes_d, 14)
    trs = [highs_d[0]-lows_d[0]]
    for i in range(1, len(daily)):
        trs.append(max(highs_d[i]-lows_d[i], abs(highs_d[i]-closes_d[i-1]), abs(lows_d[i]-closes_d[i-1])))
    atr14_d = [None]*len(daily)
    for i in range(14, len(daily)):
        atr14_d[i] = mean(trs[i-14:i])
    atr_avg30 = sma(atr14_d, 30)
    dist14h_d = [None]*len(daily)
    for i in range(len(daily)):
        win = highs_d[max(0,i-13):i+1]
        dist14h_d[i] = (closes_d[i]-max(win))/max(win)*100

    def find_di(ts):
        for i in range(len(daily)-1,-1,-1):
            if daily[i]['time']<=ts: return i
        return None

    # Master 4H
    master = {}; bar_to_window = {}
    for label, fname in WINDOWS_V4:
        p = JSONL_DIR / fname
        if not p.exists():
            print(f"WARN: {fname} missing"); continue
        for b in load_bars(p):
            ohlcv = b.get('ohlcv_last_40_bars') or []
            if not ohlcv: continue
            t = ohlcv[-1].get('time')
            if t is None or t in master: continue
            master[t] = b; bar_to_window[t] = label
    times_sorted = sorted(master.keys())
    bars_sorted = [master[t] for t in times_sorted]
    print(f"Master: {len(times_sorted)} bars 4H\n")

    # Pre-compute features per bar
    print("Computing features + outcomes (stop/target sim)...")
    bar_data = []
    for i, t in enumerate(times_sorted):
        b = bars_sorted[i]
        ohlcv = b.get('ohlcv_last_40_bars') or []
        close = ohlcv[-1].get('close') if ohlcv else None
        if close is None: continue
        atr = get_atr14(b)
        if not atr or atr<=0: continue
        di = find_di(t)
        if di is None or di < 60: continue
        # Features
        nas_l_5 = has_nas_label(b, "LONG", max_delta=5)
        nas_l_d0 = has_nas_label(b, "LONG", exact_zero=True)
        if not (nas_l_5 or nas_l_d0): continue
        nas_dist = get_nas_dist(b)
        rsi1d = rsi_d[di]
        if rsi1d is None: continue
        d14h = dist14h_d[di]
        atr_rel = (atr14_d[di]/atr_avg30[di]) if (atr14_d[di] and atr_avg30[di]) else None
        ob_dem = has_ob_demand_text(b)
        bub_sell = has_bubble_sell_4h(b, 10)
        # Compute stop/target outcome
        outcome = simulate_stop_target_long(bars_sorted, i, atr)
        if outcome is None: continue
        bar_data.append({
            'time':t,'window':bar_to_window[t],
            'r':outcome[0],'hit_bar':outcome[1],'hit_type':outcome[2],
            'nas_l_5':nas_l_5,'nas_l_d0':nas_l_d0,'nas_dist':nas_dist,
            'rsi1d':rsi1d,'d14h':d14h,'atr_rel':atr_rel,
            'ob_dem':ob_dem,'bub_sell':bub_sell,
        })
    print(f"  {len(bar_data)} bars com features (NAS LONG trigger)\n")

    # Test setups
    setups = [
        ("S0_NAS_5 only",
         lambda b: b['nas_l_5']),
        ("S1_CAPITULATION (NAS_5+RSI<50+ATR>1.3)",
         lambda b: b['nas_l_5'] and b['rsi1d']<50 and b['atr_rel'] is not None and b['atr_rel']>1.3),
        ("S2_DISCRETIONARY (NAS_d0+NAS_DIST<-1+dist14h<-7)",
         lambda b: b['nas_l_d0'] and b['nas_dist'] is not None and b['nas_dist']<=-1 and b['d14h'] is not None and b['d14h']<=-7),
        ("S2b_DISCR_relaxed (NAS_5+NAS_DIST<-1+dist14h<-7)",
         lambda b: b['nas_l_5'] and b['nas_dist'] is not None and b['nas_dist']<=-1 and b['d14h'] is not None and b['d14h']<=-7),
        ("S2c_DISCR_wider (NAS_5+dist14h<-5)",
         lambda b: b['nas_l_5'] and b['d14h'] is not None and b['d14h']<=-5),
        ("S3_DISCR+OB_demand (S2 + OB DEMAND proximity)",
         lambda b: b['nas_l_d0'] and b['nas_dist'] is not None and b['nas_dist']<=-1 and b['d14h'] is not None and b['d14h']<=-7 and b['ob_dem']),
        ("S4_DISCR+Bub_sell (S2 + Bubble Sell 4H)",
         lambda b: b['nas_l_d0'] and b['nas_dist'] is not None and b['nas_dist']<=-1 and b['d14h'] is not None and b['d14h']<=-7 and b['bub_sell']),
        ("S5_CAPIT+OB_demand",
         lambda b: b['nas_l_5'] and b['rsi1d']<50 and b['atr_rel'] is not None and b['atr_rel']>1.3 and b['ob_dem']),
        ("S6_CAPIT+Bub_sell",
         lambda b: b['nas_l_5'] and b['rsi1d']<50 and b['atr_rel'] is not None and b['atr_rel']>1.3 and b['bub_sell']),
    ]

    print(f"{'setup':<55s} {'n':>4s} {'win%':>5s} {'avg_R':>7s} {'med_R':>6s} {'sum_R':>8s} {'tgt':>4s} {'stop':>4s} {'tmo':>4s} {'wp/we':>6s}")
    print("-"*125)
    for sname, pred in setups:
        kept = [b for b in bar_data if pred(b)]
        rs = [b['r'] for b in kept]
        outcomes = [b['hit_type'] for b in kept]
        s = stats_block(rs, outcomes)
        if not s or s['n']<5: continue
        per_w = defaultdict(list)
        for b in kept: per_w[b['window']].append(b['r'])
        wp = sum(1 for w,rs in per_w.items() if len(rs)>=10 and stats_block(rs)['win%']>=WIN_GATE)
        we = sum(1 for w,rs in per_w.items() if len(rs)>=10)
        mk = "★" if s['win%']>=WIN_GATE and s['n']>=30 else " "
        print(f"{mk}{sname:<54s} {s['n']:>4d} {s['win%']:>5.1f} {s['avg_R']:>+7.2f} {s['median_R']:>+6.2f} {s['sum_R']:>+8.2f} {s['target_hits']:>4d} {s['stop_hits']:>4d} {s['timeouts']:>4d} {wp:>2d}/{we:<2d}")

    # Por janela: S1 (CAPITULATION) e S2 (DISCRETIONARY)
    print(f"\n{'='*100}")
    print(f"DETALHE PER WINDOW — S1 (CAPITULATION) e S2 (DISCRETIONARY)")
    print(f"{'='*100}")
    for sname, pred in [setups[1], setups[2]]:
        kept = [b for b in bar_data if pred(b)]
        per_w = defaultdict(list)
        for b in kept: per_w[b['window']].append(b['r'])
        print(f"\n  [{sname}]")
        print(f"    {'window':<14s} {'n':>3s} {'win%':>5s} {'avg_R':>7s} {'sum_R':>8s}")
        for wlabel, _ in WINDOWS_V4:
            rs_w = per_w.get(wlabel, [])
            s = stats_block(rs_w)
            if s:
                v = "✓" if s['n']>=10 and s['win%']>=WIN_GATE else " "
                print(f"    {wlabel:<14s} {s['n']:>3d} {s['win%']:>5.1f} {s['avg_R']:>+7.2f} {s['sum_R']:>+8.2f}  {v}")
            else:
                print(f"    {wlabel:<14s} {0:>3d}  -")

    return 0


if __name__ == "__main__":
    sys.exit(main())
