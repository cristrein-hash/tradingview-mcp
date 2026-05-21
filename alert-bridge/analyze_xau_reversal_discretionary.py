#!/usr/bin/env python3
"""
analyze_xau_reversal_discretionary.py — Hipótese REVERSAL_DISCRETIONARY LONG.

Sobre os 5 dream LONG válidos (sem #11 outlier):
  Padrão comum identificado:
    - NAS LONG label Δ=0 (no bar atual)
    - NAS_DIST ≤ -1
    - dist 14d high ≤ -7% (correção macro)

Testa esta combinação no sweep 8 janelas:
  - Recall: quantos dos 6 dream LONG válidos captura
  - Precision: win% no sweep total (8 janelas, H=20)
  - Comparar com REVERSAL_CAPITULATION (NAS+RSI<50+ATR_high)

Plus: testar variantes de threshold + filters adicionais (OB demand, Bubble Sell).
"""
from pathlib import Path
from datetime import datetime, timezone
from statistics import mean, median
import json, sys, subprocess, time
from itertools import combinations
from collections import defaultdict

BASE = Path(__file__).parent.parent
JSONL_DIR = BASE / "alert-bridge" / "logs" / "backtests"
MCP_SERVER = BASE / "src" / "server.js"
NODE = "/opt/homebrew/bin/node"
PAUSE = Path("/tmp/claude_recheck.paused")

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

# Dream LONG válidos (excluindo #11 outlier + #6 gap coleta)
DREAM_LONG_VALID = [
    ("#1",  "2026-05-04 15:00"),
    ("#5",  "2025-11-05 11:00"),
    ("#8",  "2026-03-20 14:00"),
    ("#10", "2026-03-24 10:00"),
    ("#13", "2026-02-03 03:00"),
]
DREAM_TOLERANCE_SEC = 7200
HORIZON_4H = 20
WIN_GATE = 70.0
COLOR_BULL = 2572201804
SELL_PLOTS = {"plot_0", "plot_10"}
BAR_SECONDS_4H = 14400


class MCP:
    def __init__(self): self.proc=None; self.id=0
    def start(self):
        self.proc = subprocess.Popen([NODE, str(MCP_SERVER)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
        self._raw("initialize",{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"d","version":"1.0"}})
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


def get_atr14(bar):
    ohlcv = bar.get('ohlcv_last_40_bars') or []
    if len(ohlcv)<=1: return None
    closed = ohlcv[:-1][-14:]
    r=[b['high']-b['low'] for b in closed if b.get('high') and b.get('low') and b['high']>b['low']]
    return mean(r) if r else None


def has_nas_label_delta_eq_0(bar):
    """NAS LONG label EXATAMENTE no bar atual (Δ=0)."""
    for s in (bar.get('pine_labels') or []):
        if 'NAS' not in s.get('name','').upper(): continue
        labels = s.get('labels') or []
        if not labels: continue
        xs = [l.get('x') for l in labels if l.get('x') is not None]
        if not xs: continue
        max_x = max(xs)
        for l in labels:
            lx = l.get('x'); txt = (l.get('text') or '').upper()
            if lx is None or txt!='LONG': continue
            if max_x - lx == 0: return True
    return False


def has_nas_label_recent(bar, max_delta=5):
    for s in (bar.get('pine_labels') or []):
        if 'NAS' not in s.get('name','').upper(): continue
        labels = s.get('labels') or []
        if not labels: continue
        xs = [l.get('x') for l in labels if l.get('x') is not None]
        if not xs: continue
        max_x = max(xs)
        for l in labels:
            lx = l.get('x'); txt = (l.get('text') or '').upper()
            if lx is None or txt!='LONG': continue
            if 0 <= max_x-lx <= max_delta: return True
    return False


def get_nas_dist(bar):
    for s in (bar.get('study_values') or []):
        if 'NAS' in s.get('name',''):
            try: return float(s.get('values',{}).get('NAS_DISTANCE_FROM_EMA_ATR','').replace('−','-'))
            except: return None
    return None


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


def stats_block(rs):
    if not rs: return None
    wins = sum(1 for r in rs if r>0)
    return {'n':len(rs),'win%':100*wins/len(rs),'avg_R':mean(rs),'median_R':median(rs),'sum_R':sum(rs)}


def main():
    if not PAUSE.exists():
        print("ERRO pause flag ausente.", file=sys.stderr); return 1

    print("=== REVERSAL_DISCRETIONARY hypothesis testing ===\n")

    # Daily
    client = MCP(); client.start()
    try:
        resp = client.call("data_get_ohlcv", {"count":2000,"summary":False})
        bars_d = resp.get("last_5_bars") or resp.get("bars") or []
        daily = sorted([b for b in bars_d if b.get("time")], key=lambda x: x["time"])
        print(f"Daily: {len(daily)} bars")
    finally:
        client.stop()

    closes_d = [b['close'] for b in daily]
    highs_d = [b['high'] for b in daily]
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
    for label, fname in WINDOWS_V3:
        p = JSONL_DIR / fname
        if not p.exists(): continue
        for b in load_bars(p):
            ohlcv = b.get('ohlcv_last_40_bars') or []
            if not ohlcv: continue
            t = ohlcv[-1].get('time')
            if t is None or t in master: continue
            master[t] = b; bar_to_window[t] = label
    times_sorted = sorted(master.keys())
    bars_sorted = [master[t] for t in times_sorted]
    print(f"Master: {len(times_sorted)} bars 4H\n")

    # Build bar features + outcomes pra todos bars
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
        nas_d0 = has_nas_label_delta_eq_0(b)
        nas_5 = has_nas_label_recent(b, 5)
        nas_dist = get_nas_dist(b)
        di = find_di(t)
        d14h = dist14h_d[di] if di is not None and di<len(dist14h_d) else None
        bub_sell = has_bubble_sell_4h(b, 10)
        ob_dem = has_ob_demand(b)
        bar_data.append({
            'time':t,'window':bar_to_window[t],'r_long':round(r_long,2),
            'nas_d0':nas_d0,'nas_5':nas_5,'nas_dist':nas_dist,
            'd14h':d14h,'bub_sell':bub_sell,'ob_dem':ob_dem,
        })
    print(f"Bar data: {len(bar_data)}")

    # Test variants
    variants = [
        # Hypothesis core
        ("NAS_5 + dist14h≤-7%",             lambda b: b['nas_5'] and b['d14h'] is not None and b['d14h']<=-7),
        ("NAS_5 + NAS_DIST≤-1 + dist14h≤-7%", lambda b: b['nas_5'] and b['nas_dist'] is not None and b['nas_dist']<=-1 and b['d14h'] is not None and b['d14h']<=-7),
        ("NAS_d0 + dist14h≤-7%",            lambda b: b['nas_d0'] and b['d14h'] is not None and b['d14h']<=-7),
        ("NAS_d0 + NAS_DIST≤-1 + dist14h≤-7%", lambda b: b['nas_d0'] and b['nas_dist'] is not None and b['nas_dist']<=-1 and b['d14h'] is not None and b['d14h']<=-7),
        # Variantes
        ("NAS_d0 + NAS_DIST≤-2 + dist14h≤-7%", lambda b: b['nas_d0'] and b['nas_dist'] is not None and b['nas_dist']<=-2 and b['d14h'] is not None and b['d14h']<=-7),
        ("NAS_d0 + dist14h≤-5%",            lambda b: b['nas_d0'] and b['d14h'] is not None and b['d14h']<=-5),
        ("NAS_d0 + dist14h≤-10%",           lambda b: b['nas_d0'] and b['d14h'] is not None and b['d14h']<=-10),
        ("NAS_5 + dist14h≤-7% + bub_sell",  lambda b: b['nas_5'] and b['d14h'] is not None and b['d14h']<=-7 and b['bub_sell']),
        ("NAS_5 + dist14h≤-7% + ob_dem",    lambda b: b['nas_5'] and b['d14h'] is not None and b['d14h']<=-7 and b['ob_dem']),
        ("NAS_d0 + NAS_DIST≤-1 + dist14h≤-7% + bub_sell", lambda b: b['nas_d0'] and b['nas_dist'] is not None and b['nas_dist']<=-1 and b['d14h'] is not None and b['d14h']<=-7 and b['bub_sell']),
    ]

    # Dream timestamps
    dream_ts = []
    for tid, dt_str in DREAM_LONG_VALID:
        ts = int(datetime.strptime(dt_str+"+0000","%Y-%m-%d %H:%M%z").timestamp())
        dream_ts.append((ts, tid))

    def is_dream(bar_t):
        for d_ts, tid in dream_ts:
            if abs(bar_t-d_ts) <= DREAM_TOLERANCE_SEC: return tid
        return None

    print(f"\n{'variant':<55s} {'n':>5s} {'win%':>5s} {'avg_R':>7s} {'sum_R':>8s} {'wp/we':>6s} {'recall':>7s} {'dreams':>8s}")
    print("-"*120)
    for vname, fn in variants:
        kept = [b for b in bar_data if fn(b)]
        rs = [b['r_long'] for b in kept]
        s = stats_block(rs)
        if not s: continue
        per_w = defaultdict(list)
        for b in kept: per_w[b['window']].append(b['r_long'])
        wp = sum(1 for w,rs in per_w.items() if len(rs)>=10 and stats_block(rs)['win%']>=WIN_GATE)
        we = sum(1 for w,rs in per_w.items() if len(rs)>=10)
        dreams_hit = set()
        for b in kept:
            tid = is_dream(b['time'])
            if tid: dreams_hit.add(tid)
        recall = 100*len(dreams_hit)/len(DREAM_LONG_VALID)
        mk = "★" if s['win%']>=70 and len(dreams_hit)>=4 else " "
        print(f"{mk}{vname:<54s} {s['n']:>5d} {s['win%']:>5.1f} {s['avg_R']:>+7.2f} {s['sum_R']:>+8.2f} {wp:>2d}/{we:<2d} {recall:>6.0f}% {len(dreams_hit)}/{len(DREAM_LONG_VALID)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
