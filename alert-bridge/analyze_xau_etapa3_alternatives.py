#!/usr/bin/env python3
"""
analyze_xau_etapa3_alternatives.py — Etapa 3.

Testa estratégias alternativas com V3 (regime macro) e V3+V1c (anti-Bubble Sell):
  A) IN_OB + NAS_1to2 (V0 já validado — baseline)
  B) IN_OB + RSI_50-60
  C) NAS_1to2 + RSI_50-60
  D) IN_OB + NAS_1to2 + RSI_50-60 (3-way)

Gate de validade: win% >= 70%.
Output: tabela comparativa raw → +V3 → +V3+V1c.
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
WIN_GATE = 70.0


class MCP:
    def __init__(self): self.proc=None; self.id=0
    def start(self):
        self.proc = subprocess.Popen([NODE, str(MCP_SERVER)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
        self._raw("initialize", {"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"v3","version":"1.0"}})
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
    }


def fmt(s):
    if s["n"]==0: return f"  {0:>3d}  {'-':>5s}  {'-':>7s}  {'-':>9s}  {'-':>9s}"
    valid = " VÁLIDA" if s["win%"] >= WIN_GATE else " "*7
    return f"  {s['n']:>3d}  {s['win%']:>5.1f}  {s['avg_R']:>+7.2f}  {s['median_R']:>+9.2f}{valid}"


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
    return {'rsi':rsi, 'rsi_bucket':rsi_b, 'nas_bucket':nas_b, 'in_ob':in_ob, 'close':close, 'entry_time':entry_time}


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

    print(f"=== ETAPA 3: alternativas com V3+V1c | gate win% >= {WIN_GATE}% | n>=30 ===\n")

    # Captura daily pra V3
    client = MCP(); client.start()
    state = client.call("chart_get_state")
    orig_sym = state.get("symbol"); orig_tf = state.get("resolution")
    try:
        print("Captura OHLCV diário (300 bars)...")
        client.call("chart_set_symbol",{"symbol":SYMBOL}); time.sleep(1)
        client.call("chart_set_timeframe",{"timeframe":"D"}); time.sleep(2)
        resp = client.call("data_get_ohlcv",{"count":300,"summary":False})
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

    def find_daily_idx(ts):
        for i in range(len(daily)-1, -1, -1):
            if daily[i]["time"] <= ts: return i
        return None

    # Carrega backtest
    print("\nCarregando backtest...")
    bars_4h = []
    with JSONL.open() as f:
        for line in f:
            try: bars_4h.append(json.loads(line))
            except: pass
    for i,b in enumerate(bars_4h):
        if not (b.get('ohlcv_last_40_bars') or []):
            bars_4h = bars_4h[:i]; break

    # Build full sample list (todos os bars com features)
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
            'R': round(close_R, 2),
            'rsi_bucket': st['rsi_bucket'],
            'nas_bucket': st['nas_bucket'],
            'in_ob': st['in_ob'],
            'dist_14d': dist,
            'bs_3': bs_3,
        })
    print(f"  {len(all_trades)} samples válidos\n")

    # Filtros por estratégia
    strategies = {
        'A: IN_OB + NAS_1to2 (V0)': lambda t: t['in_ob'] and t['nas_bucket']=='NAS_1to2',
        'B: IN_OB + RSI_50-60': lambda t: t['in_ob'] and t['rsi_bucket']=='RSI_50-60',
        'C: NAS_1to2 + RSI_50-60': lambda t: t['nas_bucket']=='NAS_1to2' and t['rsi_bucket']=='RSI_50-60',
        'D: IN_OB + NAS_1to2 + RSI_50-60': lambda t: t['in_ob'] and t['nas_bucket']=='NAS_1to2' and t['rsi_bucket']=='RSI_50-60',
    }

    print(f"{'estratégia':<40s} {'camada':<14s}    {'n':>3s}  {'win%':>5s}  {'avg_R':>7s}  {'median_R':>9s}")
    print("-"*100)
    for name, pred in strategies.items():
        # Raw
        base = [t for t in all_trades if pred(t)]
        # + V3
        v3 = [t for t in base if t['dist_14d'] is not None and t['dist_14d'] > DIST_THRESHOLD]
        # + V3 + V1c (anti-Bubble Sell 3 candles)
        v3_v1c = [t for t in v3 if not t['bs_3']]

        for layer_name, layer in [('raw', base), ('+V3', v3), ('+V3+V1c', v3_v1c)]:
            s = stats(layer)
            print(f"{name:<40s} {layer_name:<14s}{fmt(s)}")
        print()

    print(f"\nLegenda: VÁLIDA = win% >= {WIN_GATE}%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
