#!/usr/bin/env python3
"""
analyze_xau_proxy1_slope.py — Proxy 1: filtro slope EMA50 1D (autocontido).

Sobre V0+V3 baseline (65 trades combinados), testa:
  - slope EMA50 1D >= {0.0, 0.3, 0.5, 0.7, 1.0}%/wk
  - cross com bs_3, bs_5, bs_10 (combinações)

Objetivo: encontrar filtro macro que corte julho LOSSES sem cortar tantos
trades quanto bs_10 (que tira 18 trades).
"""
from pathlib import Path
from datetime import datetime, timezone
from statistics import mean, median, stdev
import json, subprocess, sys, time

BASE = Path(__file__).parent.parent
MCP_SERVER = BASE / "src" / "server.js"
NODE = "/opt/homebrew/bin/node"
PAUSE = Path("/tmp/claude_recheck.paused")
SYMBOL = "PEPPERSTONE:XAUUSD"

JSONL_IS = BASE / "alert-bridge" / "logs" / "backtests" / "XAUUSD_240_2025-11-19_to_2026-05-19.jsonl"
JSONL_OOS = BASE / "alert-bridge" / "logs" / "backtests" / "XAUUSD_240_2025-05-19_to_2026-05-20.jsonl"

HORIZON_4H = 10
DIST_THRESHOLD = -7.0
SELL_PLOTS = {"plot_0", "plot_10"}
BAR_SECONDS_4H = 14400
WIN_GATE = 70.0
SLOPE_THRESHOLDS = [0.0, 0.3, 0.5, 0.7, 1.0]
BS_LOOKBACKS = [3, 5, 10]


class MCP:
    def __init__(self): self.proc=None; self.id=0
    def start(self):
        self.proc = subprocess.Popen([NODE, str(MCP_SERVER)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
        self._raw("initialize", {"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"p1","version":"1.0"}})
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


def ema(values, period):
    if len(values) < period: return [None]*len(values)
    k = 2/(period+1)
    out = [None]*(period-1)
    out.append(sum(values[:period])/period)
    for v in values[period:]:
        out.append(v*k + out[-1]*(1-k))
    return out


def get_state_4h(bar):
    rsi=nas=None
    for s in (bar.get('study_values') or []):
        if 'Relative Strength' in s.get('name',''):
            try: rsi = float(s.get('values',{}).get('RSI','').replace('−','-'))
            except: pass
        if 'NAS' in s.get('name',''):
            try: nas = float(s.get('values',{}).get('NAS_DISTANCE_FROM_EMA_ATR','').replace('−','-'))
            except: pass
    ohlcv = bar.get('ohlcv_last_40_bars') or []
    close = ohlcv[-1].get('close') if ohlcv else None
    entry_time = ohlcv[-1].get('time') if ohlcv else None
    nas_b=None
    if nas is not None:
        if nas < -2: nas_b='NAS<-2'
        elif nas < -1: nas_b='NAS_-2to-1'
        elif nas < 1: nas_b='NAS_-1to1'
        elif nas < 2: nas_b='NAS_1to2'
        else: nas_b='NAS>2'
    in_ob=False
    for s in (bar.get('pine_boxes') or []):
        if 'Custom OB' in s.get('name',''):
            for z in s.get('zones', []):
                hi,lo = z.get('high'), z.get('low')
                if hi is not None and lo is not None and close is not None and lo <= close <= hi:
                    in_ob=True; break
            break
    return {'rsi':rsi,'nas_bucket':nas_b,'in_ob':in_ob,'close':close,'entry_time':entry_time}


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


def stats_block(rs):
    if not rs: return None
    wins = sum(1 for r in rs if r>0)
    return {
        'n': len(rs), 'win%': 100*wins/len(rs),
        'avg_R': mean(rs), 'median_R': median(rs),
        'min_R': min(rs), 'max_R': max(rs),
        'std_R': stdev(rs) if len(rs)>1 else 0,
        'sum_R': sum(rs),
    }


def fmt(s):
    if not s or s['n']==0:
        return f"{0:>3d}  {'-':>5s}  {'-':>7s}  {'-':>9s}  {'-':>7s}  {'-':>6s}"
    valid = "✓" if s['win%'] >= WIN_GATE else " "
    return (f"{s['n']:>3d}  {s['win%']:>5.1f}  {s['avg_R']:>+7.2f}  {s['median_R']:>+9.2f}  "
            f"{s['sum_R']:>+7.2f}  {valid:>6s}")


def main():
    if not PAUSE.exists():
        print("ERRO: pause flag ausente.", file=sys.stderr); return 1

    # Captura daily 1D
    print("Captura OHLCV daily (400 bars)...")
    client = MCP(); client.start()
    state = client.call("chart_get_state")
    orig_sym = state.get("symbol"); orig_tf = state.get("resolution")
    try:
        client.call("chart_set_symbol",{"symbol":SYMBOL}); time.sleep(1)
        client.call("chart_set_timeframe",{"timeframe":"D"}); time.sleep(2)
        resp = client.call("data_get_ohlcv",{"count":400,"summary":False})
        daily = sorted([b for b in (resp.get("last_5_bars") or resp.get("bars") or []) if b.get("time")], key=lambda x:x["time"])
        print(f"  {len(daily)} bars 1D")
    finally:
        if orig_sym:
            client.call("chart_set_symbol",{"symbol":orig_sym})
            if orig_tf: client.call("chart_set_timeframe",{"timeframe":orig_tf})
        client.stop()

    closes_d = [b["close"] for b in daily]
    highs_d = [b["high"] for b in daily]
    ema50_d = ema(closes_d, 50)
    dist14_d = [None]*len(daily)
    for i in range(len(daily)):
        win_hi = max(highs_d[max(0,i-13):i+1])
        dist14_d[i] = (closes_d[i] - win_hi) / win_hi * 100
    slope50 = [None]*len(daily)
    for i in range(55, len(daily)):
        if ema50_d[i] is not None and ema50_d[i-5] is not None and ema50_d[i-5] > 0:
            slope50[i] = (ema50_d[i] - ema50_d[i-5]) / ema50_d[i-5] * 100

    def find_di(ts):
        for i in range(len(daily)-1, -1, -1):
            if daily[i]["time"] <= ts: return i
        return None

    bars_oos = load_bars(JSONL_OOS)
    bars_is = load_bars(JSONL_IS)
    print(f"  4H: {len(bars_oos)} OOS + {len(bars_is)} IS\n")

    def trades_for_window(bars, label):
        out = []
        for i, b in enumerate(bars):
            st = get_state_4h(b)
            if st['close'] is None: continue
            atr = get_atr14(b)
            if not atr or atr<=0: continue
            if i+HORIZON_4H >= len(bars): continue
            next_close = (bars[i+HORIZON_4H].get('ohlcv_last_40_bars') or [{}])[-1].get('close')
            if next_close is None: continue
            close_R = (next_close - st['close']) / atr
            di = find_di(st['entry_time']) if st['entry_time'] else None
            dist = dist14_d[di] if di is not None and di < len(dist14_d) else None
            slope = slope50[di] if di is not None and di < len(slope50) else None
            if not (st['in_ob'] and st['nas_bucket']=='NAS_1to2'): continue
            if dist is None or dist <= DIST_THRESHOLD: continue
            bs_flags = {lb: bubble_sell_in_window(b, st['entry_time'], lb) for lb in BS_LOOKBACKS}
            out.append({
                'window': label,
                'entry_time': st['entry_time'],
                'entry_dt': datetime.fromtimestamp(st['entry_time'],tz=timezone.utc).strftime('%Y-%m-%d %H:%M') if st['entry_time'] else '?',
                'R': round(close_R, 2),
                'rsi': st['rsi'],
                'dist_14d': dist,
                'slope50_5d': slope,
                'bs_flags': bs_flags,
            })
        return out

    trades_oos = trades_for_window(bars_oos, 'OOS')
    trades_is = trades_for_window(bars_is, 'IS')
    trades_combined = trades_oos + trades_is

    # Print slope distribution
    print("Distribuição slope EMA50 1D dos 65 trades V0+V3 baseline:")
    slopes = [t['slope50_5d'] for t in trades_combined if t['slope50_5d'] is not None]
    if slopes:
        print(f"  min={min(slopes):+.2f}%  max={max(slopes):+.2f}%  mean={mean(slopes):+.2f}%  median={median(slopes):+.2f}%")
    # winners vs losers
    winners = [t for t in trades_combined if t['R']>0]
    losers = [t for t in trades_combined if t['R']<=0]
    print(f"  winners (n={len(winners)}): slope mean={mean(t['slope50_5d'] for t in winners if t['slope50_5d'] is not None):+.2f}")
    print(f"  losers  (n={len(losers)}): slope mean={mean(t['slope50_5d'] for t in losers if t['slope50_5d'] is not None):+.2f}")
    # buckets de slope
    print("\nBuckets de slope (todos os 65):")
    bins = [
        ('<0', lambda s: s < 0),
        ('0..0.3', lambda s: 0 <= s < 0.3),
        ('0.3..0.5', lambda s: 0.3 <= s < 0.5),
        ('0.5..0.7', lambda s: 0.5 <= s < 0.7),
        ('0.7..1.0', lambda s: 0.7 <= s < 1.0),
        ('1.0..1.5', lambda s: 1.0 <= s < 1.5),
        ('>=1.5', lambda s: s >= 1.5),
    ]
    print(f"  {'bucket':<10s}  {'n':>3s}  {'win%':>5s}  {'avg_R':>7s}  {'sum_R':>7s}")
    for name, pred in bins:
        g = [t for t in trades_combined if t['slope50_5d'] is not None and pred(t['slope50_5d'])]
        if g:
            rs = [t['R'] for t in g]
            wins = sum(1 for r in rs if r>0)
            print(f"  {name:<10s}  {len(g):>3d}  {100*wins/len(g):>5.1f}  {mean(rs):>+7.2f}  {sum(rs):>+7.2f}")

    print("\n" + "="*135)
    print("FILTROS SLOPE-ONLY — sobre V0+V3 baseline")
    print("="*135)
    print(f"\n{'filtro':<28s}  {'janela':<14s}  {'n':>3s}  {'win%':>5s}  {'avg_R':>7s}  {'median_R':>9s}  {'sum_R':>7s}  valid?")
    print("-"*135)
    for thr in SLOPE_THRESHOLDS:
        for label, trades in [('IS', trades_is), ('OOS', trades_oos), ('COMBINED', trades_combined)]:
            kept = [t for t in trades if t['slope50_5d'] is not None and t['slope50_5d'] >= thr]
            rs = [t['R'] for t in kept]
            s = stats_block(rs)
            print(f"slope >= {thr:<5.2f}%/wk         {label:<14s}  {fmt(s)}")
        print()

    print("\n" + "="*135)
    print("FILTROS SLOPE + bs_X — combinações")
    print("="*135)
    print(f"\n{'filtro':<28s}  {'janela':<14s}  {'n':>3s}  {'win%':>5s}  {'avg_R':>7s}  {'median_R':>9s}  {'sum_R':>7s}  valid?")
    print("-"*135)
    for thr in SLOPE_THRESHOLDS:
        if thr == 0.0: continue  # já visto no acima
        for lb in BS_LOOKBACKS:
            for label, trades in [('IS', trades_is), ('OOS', trades_oos), ('COMBINED', trades_combined)]:
                kept = [t for t in trades
                        if t['slope50_5d'] is not None and t['slope50_5d'] >= thr
                        and not t['bs_flags'].get(lb, False)]
                rs = [t['R'] for t in kept]
                s = stats_block(rs)
                print(f"slope>={thr:.2f} + bs_{lb:<2d}       {label:<14s}  {fmt(s)}")
            print()

    # Top combinações: maior n com win% >= 70
    print("\n" + "="*135)
    print("RANKING combined (win% >= 70%, ordenado por n)")
    print("="*135)
    candidates = []
    # slope-only
    for thr in SLOPE_THRESHOLDS:
        kept = [t for t in trades_combined if t['slope50_5d'] is not None and t['slope50_5d'] >= thr]
        s = stats_block([t['R'] for t in kept])
        if s and s['win%'] >= WIN_GATE:
            candidates.append((f"slope>={thr:.2f}", s))
    # slope + bs
    for thr in SLOPE_THRESHOLDS:
        if thr == 0.0: continue
        for lb in BS_LOOKBACKS:
            kept = [t for t in trades_combined
                    if t['slope50_5d'] is not None and t['slope50_5d'] >= thr
                    and not t['bs_flags'].get(lb, False)]
            s = stats_block([t['R'] for t in kept])
            if s and s['win%'] >= WIN_GATE:
                candidates.append((f"slope>={thr:.2f} + bs_{lb}", s))
    # bs only (baseline ref)
    for lb in BS_LOOKBACKS:
        kept = [t for t in trades_combined if not t['bs_flags'].get(lb, False)]
        s = stats_block([t['R'] for t in kept])
        if s and s['win%'] >= WIN_GATE:
            candidates.append((f"bs_{lb} only (ref)", s))

    candidates.sort(key=lambda x: (-x[1]['n'], -x[1]['win%']))
    print(f"\n{'filtro':<28s}  {'n':>3s}  {'win%':>5s}  {'avg_R':>7s}  {'median_R':>9s}  {'sum_R':>7s}")
    for name, s in candidates[:20]:
        print(f"{name:<28s}  {s['n']:>3d}  {s['win%']:>5.1f}  {s['avg_R']:>+7.2f}  {s['median_R']:>+9.2f}  {s['sum_R']:>+7.2f}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
