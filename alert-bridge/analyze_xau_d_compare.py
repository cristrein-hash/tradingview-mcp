#!/usr/bin/env python3
"""
analyze_xau_d_compare.py — Aplica estratégia D em N janelas e compara stats.

Strategy D = V0 + V3 + V1c + RSI_50-60
  V0  = IN_OB_ZONE + NAS_1to2
  V3  = dist_14d_high > -7%
  V1c = NOT Bubble Sell últimos 3 candles
  RSI = RSI_50-60

Uso:
  python3 analyze_xau_d_compare.py PATH1.jsonl LABEL1 [PATH2.jsonl LABEL2 ...]
"""
from pathlib import Path
from datetime import datetime, timezone
from statistics import mean, median
import json, subprocess, sys, time

BASE = Path(__file__).parent.parent
MCP_SERVER = BASE / "src" / "server.js"
NODE = "/opt/homebrew/bin/node"
PAUSE = Path("/tmp/claude_recheck.paused")

SYMBOL = "PEPPERSTONE:XAUUSD"
HORIZON_4H = 10
DIST_THRESHOLD = -7.0
SELL_PLOTS = {"plot_0", "plot_10"}
BAR_SECONDS_4H = 14400
WIN_GATE = 70.0


class MCP:
    def __init__(self): self.proc=None; self.id=0
    def start(self):
        self.proc = subprocess.Popen([NODE, str(MCP_SERVER)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
        self._raw("initialize", {"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"d-cmp","version":"1.0"}})
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


def stats(trades):
    if not trades: return {"n":0}
    rs = [t['R'] for t in trades]
    return {
        "n": len(trades),
        "win%": round(100*sum(1 for r in rs if r>0)/len(rs), 1),
        "avg_R": round(mean(rs), 2),
        "median_R": round(median(rs), 2),
        "min_R": round(min(rs), 2),
        "max_R": round(max(rs), 2),
    }


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


def load_bars(jsonl_path):
    bars = []
    with Path(jsonl_path).open() as f:
        for line in f:
            try: bars.append(json.loads(line))
            except: pass
    for i, b in enumerate(bars):
        if b.get('_error') or not (b.get('ohlcv_last_40_bars') or []):
            bars = bars[:i]; break
    return bars


def fetch_daily(client, symbol, count=400):
    state = client.call("chart_get_state")
    orig_sym = state.get("symbol"); orig_tf = state.get("resolution")
    try:
        client.call("chart_set_symbol", {"symbol": symbol}); time.sleep(1)
        client.call("chart_set_timeframe", {"timeframe": "D"}); time.sleep(2)
        resp = client.call("data_get_ohlcv", {"count": count, "summary": False})
        daily = sorted([b for b in (resp.get("last_5_bars") or resp.get("bars") or []) if b.get("time")], key=lambda x: x["time"])
        return daily, orig_sym, orig_tf
    except Exception:
        if orig_sym:
            client.call("chart_set_symbol", {"symbol": orig_sym})
            if orig_tf: client.call("chart_set_timeframe", {"timeframe": orig_tf})
        raise


def restore_chart(client, orig_sym, orig_tf):
    if orig_sym:
        client.call("chart_set_symbol", {"symbol": orig_sym})
        if orig_tf: client.call("chart_set_timeframe", {"timeframe": orig_tf})


def compute_dist14(daily):
    closes_d = [b["close"] for b in daily]
    highs_d = [b["high"] for b in daily]
    dist14 = [None]*len(daily)
    for i in range(len(daily)):
        win = highs_d[max(0,i-13):i+1]
        max_h = max(win)
        dist14[i] = (closes_d[i] - max_h) / max_h * 100
    return dist14


def trades_for_window(bars_4h, daily, dist14):
    def find_di(ts):
        for i in range(len(daily)-1, -1, -1):
            if daily[i]["time"] <= ts: return i
        return None
    trades = []
    for i, b in enumerate(bars_4h):
        st = get_state_4h(b)
        if st['close'] is None or st['rsi'] is None: continue
        atr = get_atr14(b)
        if not atr or atr<=0: continue
        if i+HORIZON_4H >= len(bars_4h): continue
        next_close = (bars_4h[i+HORIZON_4H].get('ohlcv_last_40_bars') or [{}])[-1].get('close')
        if next_close is None: continue
        close_R = (next_close - st['close']) / atr
        di = find_di(st['entry_time']) if st['entry_time'] else None
        dist = dist14[di] if di is not None and di < len(dist14) else None
        bs_3 = bubble_sell_in_window(b, st['entry_time'], 3)
        trades.append({
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
    return trades


def apply_strategies(trades):
    """Return dict of strategy_name -> list of matched trades."""
    v0 = [t for t in trades if t['in_ob'] and t['nas_bucket']=='NAS_1to2']
    v3 = [t for t in v0 if t['dist_14d'] is not None and t['dist_14d'] > DIST_THRESHOLD]
    v3_v1c = [t for t in v3 if not t['bs_3']]
    d = [t for t in v3_v1c if t['rsi_bucket']=='RSI_50-60']
    return {
        'V0 (raw)': v0,
        'V0+V3 (regime)': v3,
        'V0+V3+V1c (anti-BubSell)': v3_v1c,
        'D (V0+V3+V1c+RSI_50-60)': d,
    }


def main():
    if not PAUSE.exists():
        print(f"ERRO: pause flag ausente.", file=sys.stderr); return 1
    if len(sys.argv) < 3 or len(sys.argv) % 2 != 1:
        print("Uso: analyze_xau_d_compare.py PATH1.jsonl LABEL1 [PATH2.jsonl LABEL2 ...]", file=sys.stderr); return 1

    pairs = []
    for i in range(1, len(sys.argv), 2):
        pairs.append((sys.argv[i], sys.argv[i+1]))

    print(f"=== Comparativo de janelas — Strategy D | gate win% >= {WIN_GATE}% ===\n")

    # Compute daily ONCE — get max window covering all bars in all jsonls
    print("Captura daily 1D (cobre todas janelas)...")
    client = MCP(); client.start()
    daily, orig_sym, orig_tf = fetch_daily(client, SYMBOL, count=400)
    print(f"  {len(daily)} bars 1D ({datetime.fromtimestamp(daily[0]['time'],tz=timezone.utc):%Y-%m-%d} → {datetime.fromtimestamp(daily[-1]['time'],tz=timezone.utc):%Y-%m-%d})")
    try:
        dist14 = compute_dist14(daily)

        # Per window
        for path, label in pairs:
            p = Path(path)
            if not p.exists():
                print(f"\n[{label}] NÃO encontrado: {path}"); continue
            print(f"\n[{label}] {p.name}")
            bars = load_bars(p)
            if not bars:
                print(f"  vazio"); continue
            print(f"  {len(bars)} bars 4H válidos")
            first_t = (bars[0].get('ohlcv_last_40_bars') or [{}])[-1].get('time')
            last_t = (bars[-1].get('ohlcv_last_40_bars') or [{}])[-1].get('time')
            if first_t and last_t:
                print(f"  range: {datetime.fromtimestamp(first_t,tz=timezone.utc):%Y-%m-%d %H:%M} → {datetime.fromtimestamp(last_t,tz=timezone.utc):%Y-%m-%d %H:%M}")

            trades = trades_for_window(bars, daily, dist14)
            results = apply_strategies(trades)
            print(f"  total samples válidos: {len(trades)}\n")
            print(f"  {'estratégia':<32s}  {'n':>3s}  {'win%':>5s}  {'avg_R':>7s}  {'median_R':>9s}  {'min_R':>7s}  {'max_R':>7s}  valid?")
            for sname, st_trades in results.items():
                s = stats(st_trades)
                valid = "VÁLIDA" if s.get('win%', 0) >= WIN_GATE else "  -   "
                if s['n']==0:
                    print(f"  {sname:<32s}  {0:>3d}  {'-':>5s}  {'-':>7s}  {'-':>9s}  {'-':>7s}  {'-':>7s}  -")
                else:
                    print(f"  {sname:<32s}  {s['n']:>3d}  {s['win%']:>5.1f}  {s['avg_R']:>+7.2f}  {s['median_R']:>+9.2f}  {s['min_R']:>+7.2f}  {s['max_R']:>+7.2f}  {valid}")

            # Detalhe dos trades D
            d_trades = results['D (V0+V3+V1c+RSI_50-60)']
            if d_trades:
                print(f"\n  --- Trades D detalhados ---")
                for t in sorted(d_trades, key=lambda x: x['entry_time'] or 0):
                    flag = "WIN " if t['R']>0 else "LOSS"
                    print(f"    {t['entry_dt']}  R={t['R']:+6.2f}  rsi={t['rsi']:5.1f}  dist={t['dist_14d']:+5.1f}%  {flag}")
    finally:
        restore_chart(client, orig_sym, orig_tf)
        client.stop()

    return 0


if __name__ == "__main__":
    sys.exit(main())
