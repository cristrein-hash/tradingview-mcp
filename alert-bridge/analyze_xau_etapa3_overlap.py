#!/usr/bin/env python3
"""
analyze_xau_etapa3_overlap.py — Overlap entre estratégias A/B/C/D na camada +V3+V1c.

Saber se cada estratégia captura trades distintos ou se sobrepõem fortemente.
"""
from pathlib import Path
from datetime import datetime, timezone
from statistics import mean, median
import json, subprocess, sys, time

BASE = Path(__file__).parent.parent
MCP_SERVER = BASE / "src" / "server.js"
NODE = "/opt/homebrew/bin/node"
JSONL = BASE / "alert-bridge" / "logs" / "backtests" / "XAUUSD_240_2025-11-19_to_2026-05-19.jsonl"
PAUSE = Path("/tmp/claude_recheck.paused")

SYMBOL = "PEPPERSTONE:XAUUSD"
HORIZON_4H = 10
DIST_THRESHOLD = -7.0
SELL_PLOTS = {"plot_0", "plot_10"}
BAR_SECONDS_4H = 14400


class MCP:
    def __init__(self): self.proc=None; self.id=0
    def start(self):
        self.proc = subprocess.Popen([NODE, str(MCP_SERVER)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
        self._raw("initialize", {"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"ov","version":"1.0"}})
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
        deadline = time.monotonic()+t
        while time.monotonic()<deadline:
            line = self.proc.stdout.readline()
            if not line: raise RuntimeError("closed")
            try:
                r = json.loads(line)
                if r.get("id")==self.id: return r
            except: continue
        raise TimeoutError(m)
    def call(self, n, a=None, t=60):
        r = self._raw("tools/call", {"name":n,"arguments":a or {}}, t)
        if "error" in r: return {"_error": r["error"]}
        c = r.get("result",{}).get("content",[])
        if c and c[0].get("type")=="text":
            try: return json.loads(c[0]["text"])
            except: return {"_raw": c[0]["text"]}
        return r.get("result",{})


def get_state_4h(bar):
    rsi=nas=None
    for s in (bar.get('study_values') or []):
        if 'Relative Strength' in s.get('name',''):
            try: rsi = float(s.get('values',{}).get('RSI','').replace('−','-'))
            except: pass
        if 'NAS' in s.get('name',''):
            try: nas = float(s.get('values',{}).get('NAS_DISTANCE_FROM_EMA_ATR','').replace('−','-'))
            except: pass
    nas_b=None
    if nas is not None:
        if nas < -2: nas_b='NAS<-2'
        elif nas < -1: nas_b='NAS_-2to-1'
        elif nas < 1: nas_b='NAS_-1to1'
        elif nas < 2: nas_b='NAS_1to2'
        else: nas_b='NAS>2'
    rsi_b=None
    if rsi is not None:
        if rsi < 30: rsi_b='RSI<30'
        elif rsi < 40: rsi_b='RSI_30-40'
        elif rsi < 50: rsi_b='RSI_40-50'
        elif rsi < 60: rsi_b='RSI_50-60'
        elif rsi < 70: rsi_b='RSI_60-70'
        else: rsi_b='RSI>70'
    ohlcv = bar.get('ohlcv_last_40_bars') or []
    close = ohlcv[-1].get('close') if ohlcv else None
    entry_time = ohlcv[-1].get('time') if ohlcv else None
    in_ob=False
    for s in (bar.get('pine_boxes') or []):
        if 'Custom OB' in s.get('name',''):
            for z in s.get('zones', []):
                hi,lo = z.get('high'), z.get('low')
                if hi is not None and lo is not None and close is not None and lo <= close <= hi:
                    in_ob=True; break
            break
    return {'rsi':rsi,'rsi_bucket':rsi_b,'nas_bucket':nas_b,'in_ob':in_ob,'close':close,'entry_time':entry_time}


def get_atr14(bar):
    ohlcv = bar.get('ohlcv_last_40_bars') or []
    if len(ohlcv)<=1: return None
    closed = ohlcv[:-1][-14:]
    r = [b['high']-b['low'] for b in closed if b.get('high') and b.get('low') and b['high']>b['low']]
    return mean(r) if r else None


def bubble_sell_in_window(bar, entry_time, lookback_bars):
    if entry_time is None: return False
    min_time = entry_time - (lookback_bars - 1) * BAR_SECONDS_4H
    for s in (bar.get('pine_shapes_bubbles') or []):
        if 'Bubbles' not in s.get('name',''): continue
        for act in s.get('activations', []):
            t = act.get('time')
            if t is None: continue
            if min_time <= t <= entry_time:
                for p in (act.get('shapes') or {}):
                    if p in SELL_PLOTS:
                        return True
    return False


def main():
    if not PAUSE.exists():
        print(f"ERRO: pause flag ausente.", file=sys.stderr); return 1

    # Daily pra V3
    client = MCP(); client.start()
    state = client.call("chart_get_state")
    orig_sym = state.get("symbol"); orig_tf = state.get("resolution")
    try:
        client.call("chart_set_symbol",{"symbol":SYMBOL}); time.sleep(1)
        client.call("chart_set_timeframe",{"timeframe":"D"}); time.sleep(2)
        resp = client.call("data_get_ohlcv",{"count":300,"summary":False})
        daily = sorted([b for b in (resp.get("last_5_bars") or resp.get("bars") or []) if b.get("time")], key=lambda x:x["time"])
    finally:
        if orig_sym:
            client.call("chart_set_symbol",{"symbol":orig_sym})
            if orig_tf: client.call("chart_set_timeframe",{"timeframe":orig_tf})
        client.stop()

    closes_d = [b["close"] for b in daily]
    highs_d = [b["high"] for b in daily]
    dist14 = [None]*len(daily)
    for i in range(len(daily)):
        win = highs_d[max(0,i-13):i+1]
        max_h = max(win)
        dist14[i] = (closes_d[i] - max_h) / max_h * 100

    def find_daily_idx(ts):
        for i in range(len(daily)-1, -1, -1):
            if daily[i]["time"] <= ts: return i
        return None

    # Load
    bars_4h = []
    with JSONL.open() as f:
        for line in f:
            try: bars_4h.append(json.loads(line))
            except: pass
    for i,b in enumerate(bars_4h):
        if not (b.get('ohlcv_last_40_bars') or []):
            bars_4h = bars_4h[:i]; break

    all_trades = []
    for i, b in enumerate(bars_4h):
        st = get_state_4h(b)
        if st['close'] is None: continue
        atr = get_atr14(b)
        if not atr or atr<=0: continue
        if i+HORIZON_4H >= len(bars_4h): continue
        next_close = (bars_4h[i+HORIZON_4H].get('ohlcv_last_40_bars') or [{}])[-1].get('close')
        if next_close is None: continue
        close_R = (next_close - st['close']) / atr
        di = find_daily_idx(st['entry_time']) if st['entry_time'] else None
        dist = dist14[di] if di is not None else None
        bs_3 = bubble_sell_in_window(b, st['entry_time'], 3)
        all_trades.append({
            'idx': i,
            'entry_time': st['entry_time'],
            'entry_dt': datetime.fromtimestamp(st['entry_time'],tz=timezone.utc).strftime('%Y-%m-%d %H:%M') if st['entry_time'] else '?',
            'R': round(close_R, 2),
            'rsi': st['rsi'],
            'rsi_bucket': st['rsi_bucket'],
            'nas_bucket': st['nas_bucket'],
            'in_ob': st['in_ob'],
            'dist_14d': dist,
            'bs_3': bs_3,
        })

    # Apply V3+V1c base filter
    def base_filter(t):
        return (t['dist_14d'] is not None and t['dist_14d'] > DIST_THRESHOLD and not t['bs_3'])

    strategies = {
        'A': lambda t: t['in_ob'] and t['nas_bucket']=='NAS_1to2',
        'B': lambda t: t['in_ob'] and t['rsi_bucket']=='RSI_50-60',
        'C': lambda t: t['nas_bucket']=='NAS_1to2' and t['rsi_bucket']=='RSI_50-60',
        'D': lambda t: t['in_ob'] and t['nas_bucket']=='NAS_1to2' and t['rsi_bucket']=='RSI_50-60',
    }

    sets = {}
    for k, pred in strategies.items():
        sets[k] = {t['idx'] for t in all_trades if base_filter(t) and pred(t)}
        print(f"  {k}: n={len(sets[k])}")
    print()

    print("=== Intersections (camada +V3+V1c) ===")
    pairs = [('A','B'),('A','C'),('A','D'),('B','C'),('B','D'),('C','D')]
    for a, b in pairs:
        inter = sets[a] & sets[b]
        union = sets[a] | sets[b]
        only_a = sets[a] - sets[b]
        only_b = sets[b] - sets[a]
        jaccard = len(inter) / len(union) if union else 0
        print(f"  {a} ∩ {b}: {len(inter):3d}  | {a}-only: {len(only_a):3d}  | {b}-only: {len(only_b):3d}  | jaccard: {jaccard:.2f}")

    print()
    print("=== Pairwise containment ===")
    for a in 'ABCD':
        for b in 'ABCD':
            if a==b: continue
            if not sets[a]: continue
            pct = len(sets[a] & sets[b]) / len(sets[a]) * 100
            print(f"  {pct:5.1f}% dos trades de {a} estão em {b}")

    print()
    print("=== União A+B+C+D (todos os trades únicos VÁLIDOS) ===")
    union_all = sets['A'] | sets['B'] | sets['C'] | sets['D']
    print(f"  n = {len(union_all)} trades únicos")
    union_trades = [t for t in all_trades if t['idx'] in union_all]
    rs = [t['R'] for t in union_trades]
    wins = sum(1 for r in rs if r>0)
    print(f"  win% = {100*wins/len(rs):.1f}  avg_R = {mean(rs):+.2f}  median_R = {median(rs):+.2f}")

    print()
    print("=== Trade-by-trade: presença em cada estratégia ===")
    print(f"  {'entry_dt':<17s} {'R':>6s} {'rsi':>5s} {'A':>2s} {'B':>2s} {'C':>2s} {'D':>2s}  pool")
    union_sorted = sorted(union_trades, key=lambda x: x['entry_time'] or 0)
    for t in union_sorted:
        flags = ''.join(k if t['idx'] in sets[k] else '.' for k in 'ABCD')
        membership = [k for k in 'ABCD' if t['idx'] in sets[k]]
        print(f"  {t['entry_dt']} {t['R']:+6.2f} {t['rsi']:5.1f}  {flags[0]:>2s} {flags[1]:>2s} {flags[2]:>2s} {flags[3]:>2s}  {','.join(membership)}")

    # Trades only in B (not A) — diversificação real
    only_b = sets['B'] - sets['A']
    if only_b:
        print()
        print(f"=== Trades EXCLUSIVOS de B (não-A): n={len(only_b)} ===")
        trades_only_b = [t for t in all_trades if t['idx'] in only_b]
        for t in sorted(trades_only_b, key=lambda x: x['entry_time'] or 0):
            print(f"  {t['entry_dt']} R={t['R']:+.2f} | rsi={t['rsi']:.1f} | nas={t['nas_bucket']} | dist={t['dist_14d']:+.1f}%")
        rs = [t['R'] for t in trades_only_b]
        wins = sum(1 for r in rs if r>0)
        print(f"  → n={len(rs)}  win%={100*wins/len(rs):.1f}  avg_R={mean(rs):+.2f}")

    # Trades only in C (not A, not B) — diversificação ainda mais profunda
    only_c = sets['C'] - sets['A'] - sets['B']
    if only_c:
        print()
        print(f"=== Trades EXCLUSIVOS de C (não-A, não-B): n={len(only_c)} ===")
        trades_only_c = [t for t in all_trades if t['idx'] in only_c]
        for t in sorted(trades_only_c, key=lambda x: x['entry_time'] or 0):
            print(f"  {t['entry_dt']} R={t['R']:+.2f} | rsi={t['rsi']:.1f} | nas={t['nas_bucket']} | dist={t['dist_14d']:+.1f}%")
        rs = [t['R'] for t in trades_only_c]
        wins = sum(1 for r in rs if r>0)
        print(f"  → n={len(rs)}  win%={100*wins/len(rs):.1f}  avg_R={mean(rs):+.2f}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
