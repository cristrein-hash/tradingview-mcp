#!/usr/bin/env python3
"""
analyze_xau_a_combined.py — Stats combinados da estratégia A em N janelas.

Strategy A = V0 + V3 + V1c
  V0  = IN_OB_ZONE + NAS_1to2
  V3  = dist_14d_high > -7%
  V1c = NOT Bubble Sell últimos 3 candles

Carrega múltiplos JSONLs, aplica A em cada, e produz stats por janela + combinado.

Uso:
  python3 analyze_xau_a_combined.py PATH1.jsonl LABEL1 [PATH2.jsonl LABEL2 ...]
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
        self._raw("initialize", {"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"a-comb","version":"1.0"}})
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
        'n': len(rs),
        'win%': round(100*wins/len(rs), 1),
        'avg_R': round(mean(rs), 2),
        'median_R': round(median(rs), 2),
        'min_R': round(min(rs), 2),
        'max_R': round(max(rs), 2),
        'std_R': round(stdev(rs), 2) if len(rs)>1 else 0,
        'sum_R': round(sum(rs), 2),
    }


def main():
    if not PAUSE.exists():
        print(f"ERRO: pause flag ausente.", file=sys.stderr); return 1
    if len(sys.argv) < 3 or len(sys.argv) % 2 != 1:
        print("Uso: analyze_xau_a_combined.py PATH1.jsonl LABEL1 [PATH2.jsonl LABEL2 ...]", file=sys.stderr); return 1

    pairs = []
    for i in range(1, len(sys.argv), 2):
        pairs.append((sys.argv[i], sys.argv[i+1]))

    print(f"=== Análise combinada — Strategy A (V0+V3+V1c) | gate >= {WIN_GATE}% ===\n")

    # Daily 1D — TF cobre todas janelas
    print("Captura daily 1D (400 bars, cobre todas as janelas)...")
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
    dist14 = [None]*len(daily)
    for i in range(len(daily)):
        win = highs_d[max(0,i-13):i+1]
        max_h = max(win)
        dist14[i] = (closes_d[i] - max_h) / max_h * 100

    def find_di(ts):
        for i in range(len(daily)-1, -1, -1):
            if daily[i]["time"] <= ts: return i
        return None

    all_trades_combined = []
    per_window = {}

    for path, label in pairs:
        bars = load_bars(path)
        if not bars:
            print(f"\n[{label}] vazio"); continue
        trades = []
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
            dist = dist14[di] if di is not None and di < len(dist14) else None
            bs_3 = bubble_sell_in_window(b, st['entry_time'], 3)
            # Apply A filters
            if not (st['in_ob'] and st['nas_bucket']=='NAS_1to2'): continue
            if dist is None or dist <= DIST_THRESHOLD: continue
            if bs_3: continue
            trades.append({
                'window': label,
                'entry_time': st['entry_time'],
                'entry_dt': datetime.fromtimestamp(st['entry_time'],tz=timezone.utc).strftime('%Y-%m-%d %H:%M') if st['entry_time'] else '?',
                'R': round(close_R, 2),
                'rsi': st['rsi'],
                'dist_14d': dist,
            })
        per_window[label] = trades
        all_trades_combined.extend(trades)

    # Per window
    print(f"\n{'janela':<35s}  {'n':>3s}  {'win%':>5s}  {'avg_R':>7s}  {'med_R':>6s}  {'min_R':>7s}  {'max_R':>7s}  {'std_R':>6s}  {'sum_R':>7s}  valid?")
    print("-"*120)
    for label, trades in per_window.items():
        rs = [t['R'] for t in trades]
        s = stats_block(rs)
        valid = "VÁLIDA" if s and s['win%'] >= WIN_GATE else "  -   "
        if s:
            print(f"{label:<35s}  {s['n']:>3d}  {s['win%']:>5.1f}  {s['avg_R']:>+7.2f}  {s['median_R']:>+6.2f}  {s['min_R']:>+7.2f}  {s['max_R']:>+7.2f}  {s['std_R']:>6.2f}  {s['sum_R']:>+7.2f}  {valid}")
        else:
            print(f"{label:<35s}  -")

    # Combined
    rs = [t['R'] for t in all_trades_combined]
    s = stats_block(rs)
    valid = "VÁLIDA" if s and s['win%'] >= WIN_GATE else "  -   "
    print("-"*120)
    if s:
        print(f"{'COMBINED (in + out)':<35s}  {s['n']:>3d}  {s['win%']:>5.1f}  {s['avg_R']:>+7.2f}  {s['median_R']:>+6.2f}  {s['min_R']:>+7.2f}  {s['max_R']:>+7.2f}  {s['std_R']:>6.2f}  {s['sum_R']:>+7.2f}  {valid}")

    # Sample gate status
    if s:
        print(f"\nSample gate ([[feedback_sample_gate_for_rules]]):")
        if s['n'] >= 100:
            print(f"  n={s['n']} → SÓLIDO (>=100)")
        elif s['n'] >= 50:
            print(f"  n={s['n']} → PRELIMINAR FORTE (>=50)")
        elif s['n'] >= 30:
            print(f"  n={s['n']} → PRELIMINAR (>=30)")
        else:
            print(f"  n={s['n']} → INTERIM (<30)")

    # Distribuição R
    if rs:
        print("\nDistribuição R (combinado):")
        buckets = [
            ('R <= -3', lambda r: r <= -3),
            ('-3 < R <= -2', lambda r: -3 < r <= -2),
            ('-2 < R <= -1', lambda r: -2 < r <= -1),
            ('-1 < R <= 0', lambda r: -1 < r <= 0),
            ('0 < R <= +1', lambda r: 0 < r <= 1),
            ('+1 < R <= +2', lambda r: 1 < r <= 2),
            ('+2 < R <= +3', lambda r: 2 < r <= 3),
            ('+3 < R <= +5', lambda r: 3 < r <= 5),
            ('R > +5', lambda r: r > 5),
        ]
        for name, pred in buckets:
            count = sum(1 for r in rs if pred(r))
            pct = count/len(rs)*100
            bar = "█" * int(pct/3)
            print(f"  {name:<14s}  {count:>3d} ({pct:>4.1f}%)  {bar}")

    # Trades por mês
    if all_trades_combined:
        print("\nTrades por mês:")
        from collections import defaultdict
        by_month = defaultdict(list)
        for t in all_trades_combined:
            ym = t['entry_dt'][:7]
            by_month[ym].append(t)
        for ym in sorted(by_month.keys()):
            ts = by_month[ym]
            rs = [x['R'] for x in ts]
            wins = sum(1 for r in rs if r>0)
            print(f"  {ym}  n={len(ts):>2d}  win%={100*wins/len(ts):>5.1f}  sum_R={sum(rs):+6.2f}")

    # All trades list
    print(f"\nLista completa dos {len(all_trades_combined)} trades A combinados (ordenado por data):")
    for t in sorted(all_trades_combined, key=lambda x: x['entry_time'] or 0):
        flag = "WIN " if t['R']>0 else "LOSS"
        print(f"  [{t['window']:<25s}] {t['entry_dt']}  R={t['R']:+6.2f}  rsi={t['rsi']:5.1f}  dist={t['dist_14d']:+5.1f}%  {flag}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
