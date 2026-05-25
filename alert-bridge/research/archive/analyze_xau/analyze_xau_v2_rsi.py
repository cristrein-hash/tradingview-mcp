#!/usr/bin/env python3
"""
analyze_xau_v2_rsi.py — Etapa 2 (V2): RSI como filtro adicional sobre V0+V3.

Análise exploratória:
  1. Distribuição de RSI nos 38 trades V0+V3
  2. Winners vs losers — separação por RSI?
  3. Buckets candidatos (RSI<50, 50-55, 55-60, 60-65, 65+)
  4. Critério proposto: maximizar avg_R mantendo n>=20

Reutiliza a captura OHLCV + Daily do V1.
"""
from pathlib import Path
from datetime import datetime, timezone
from statistics import mean, median, stdev
import json, subprocess, sys, time

BASE = Path(__file__).parent.parent
MCP_SERVER = BASE / "src" / "server.js"
NODE = "/opt/homebrew/bin/node"
JSONL = BASE / "alert-bridge" / "logs" / "backtests" / "XAUUSD_240_2025-11-19_to_2026-05-19.jsonl"
PAUSE = Path("/tmp/claude_recheck.paused")

SYMBOL = "PEPPERSTONE:XAUUSD"
HORIZON_4H = 10
DIST_THRESHOLD = -7.0


class MCP:
    def __init__(self): self.proc=None; self.id=0
    def start(self):
        self.proc = subprocess.Popen([NODE, str(MCP_SERVER)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
        self._raw("initialize", {"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"v2","version":"1.0"}})
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
    rs = [t['close_R'] for t in trades]
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
    return {'rsi':rsi, 'nas_bucket':nas_b, 'in_ob':in_ob, 'close':close, 'entry_time':entry_time}


def get_atr14(bar):
    ohlcv = bar.get('ohlcv_last_40_bars') or []
    if len(ohlcv)<=1: return None
    closed = ohlcv[:-1][-14:]
    r = [b['high']-b['low'] for b in closed if b.get('high') and b.get('low') and b['high']>b['low']]
    return mean(r) if r else None


def main():
    if not PAUSE.exists():
        print(f"ERRO: pause flag ausente.", file=sys.stderr); return 1

    print("=== ETAPA 2 (V2): RSI sobre V0+V3 ===\n")

    # === Captura OHLCV diário (V3 daily reference) ===
    client = MCP()
    client.start()
    state = client.call("chart_get_state")
    orig_sym = state.get("symbol"); orig_tf = state.get("resolution")
    print(f"  chart original: {orig_sym} {orig_tf}")
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

    # === Reconstrói trades V0+V3 ===
    print("\nCarregando backtest V0...")
    bars_4h = []
    with JSONL.open() as f:
        for line in f:
            try: bars_4h.append(json.loads(line))
            except: pass
    for i,b in enumerate(bars_4h):
        if not (b.get('ohlcv_last_40_bars') or []):
            bars_4h = bars_4h[:i]; break
    print(f"  {len(bars_4h)} bars 4H válidos")

    trades = []
    for i, b in enumerate(bars_4h):
        st = get_state_4h(b)
        if not (st['in_ob'] and st['nas_bucket']=='NAS_1to2'): continue
        atr = get_atr14(b)
        if not atr or atr<=0 or st['close'] is None or st['rsi'] is None: continue
        if i+HORIZON_4H >= len(bars_4h): continue
        next_close = (bars_4h[i+HORIZON_4H].get('ohlcv_last_40_bars') or [{}])[-1].get('close')
        if next_close is None: continue
        close_R = (next_close - st['close']) / atr
        di = find_daily_idx(st['entry_time']) if st['entry_time'] else None
        dist = dist14[di] if di is not None else None
        if dist is None or dist <= DIST_THRESHOLD: continue  # V3 filter
        trades.append({
            'bar_4h_index': i,
            'entry_time': st['entry_time'],
            'entry_dt': datetime.fromtimestamp(st['entry_time'],tz=timezone.utc).strftime('%Y-%m-%d %H:%M') if st['entry_time'] else '?',
            'close_R': round(close_R, 2),
            'rsi': round(st['rsi'], 1),
            'dist_14d_high': round(dist, 2),
        })

    print(f"  {len(trades)} trades V0+V3 reconstruídos\n")

    # === Estatística de RSI ===
    rsis = [t['rsi'] for t in trades]
    print("=== RSI distribution (V0+V3 todos os 38) ===")
    print(f"  min={min(rsis):.1f}  max={max(rsis):.1f}  mean={mean(rsis):.1f}  median={median(rsis):.1f}")

    # Winners vs losers
    winners = [t for t in trades if t['close_R'] > 0]
    losers = [t for t in trades if t['close_R'] <= 0]
    print(f"\n  winners (n={len(winners)}): rsi mean={mean(r['rsi'] for r in winners):.1f}  median={median(r['rsi'] for r in winners):.1f}")
    if losers:
        print(f"  losers  (n={len(losers)}):  rsi mean={mean(r['rsi'] for r in losers):.1f}  median={median(r['rsi'] for r in losers):.1f}")

    # === Buckets RSI ===
    print("\n=== Buckets RSI ===")
    buckets = [
        ('<45', lambda r: r < 45),
        ('45-50', lambda r: 45 <= r < 50),
        ('50-55', lambda r: 50 <= r < 55),
        ('55-60', lambda r: 55 <= r < 60),
        ('60-65', lambda r: 60 <= r < 65),
        ('65+', lambda r: r >= 65),
    ]
    print(f"  {'bucket':<10s} {'n':>3s} {'win%':>6s} {'avg_R':>7s} {'median_R':>9s} {'min_R':>7s} {'max_R':>7s}")
    for name, pred in buckets:
        group = [t for t in trades if pred(t['rsi'])]
        s = stats(group)
        if s['n']==0:
            print(f"  {name:<10s} {0:>3d}  {'-':>5s}  {'-':>6s}  {'-':>8s}  {'-':>6s}  {'-':>6s}")
        else:
            print(f"  {name:<10s} {s['n']:>3d} {s['win%']:>5.1f}% {s['avg_R']:>+7.2f} {s['median_R']:>+9.2f} {s['min_R']:>+7.2f} {s['max_R']:>+7.2f}")

    # === Cortes progressivos: RSI >= X ===
    print("\n=== Cortes RSI >= X (V0+V3 + filtro RSI mínimo) ===")
    print(f"  {'corte':<10s} {'n':>3s} {'win%':>6s} {'avg_R':>7s} {'median_R':>9s}")
    for x in [50, 52, 54, 55, 56, 58, 60]:
        group = [t for t in trades if t['rsi'] >= x]
        s = stats(group)
        if s['n']==0: continue
        print(f"  RSI>={x:<5d}  {s['n']:>3d} {s['win%']:>5.1f}% {s['avg_R']:>+7.2f} {s['median_R']:>+9.2f}")

    # === Cortes RSI <= X (filtra topos exagerados) ===
    print("\n=== Cortes RSI <= X (filtra overbought) ===")
    print(f"  {'corte':<10s} {'n':>3s} {'win%':>6s} {'avg_R':>7s} {'median_R':>9s}")
    for x in [70, 65, 62, 60, 58]:
        group = [t for t in trades if t['rsi'] <= x]
        s = stats(group)
        if s['n']==0: continue
        print(f"  RSI<={x:<5d}  {s['n']:>3d} {s['win%']:>5.1f}% {s['avg_R']:>+7.2f} {s['median_R']:>+9.2f}")

    # === Janelas (band) RSI ===
    print("\n=== Janelas RSI (corte duplo) ===")
    print(f"  {'janela':<10s} {'n':>3s} {'win%':>6s} {'avg_R':>7s} {'median_R':>9s}")
    for lo, hi in [(50,65),(52,62),(54,62),(55,60),(50,60),(50,58)]:
        group = [t for t in trades if lo <= t['rsi'] <= hi]
        s = stats(group)
        if s['n']==0: continue
        print(f"  {lo}..{hi:<5d}  {s['n']:>3d} {s['win%']:>5.1f}% {s['avg_R']:>+7.2f} {s['median_R']:>+9.2f}")

    # === Trades detalhados ordenados por RSI ===
    print("\n=== Trades V0+V3 ordenados por RSI ===")
    for t in sorted(trades, key=lambda x: x['rsi']):
        flag = "WIN" if t['close_R']>0 else "LOSS"
        print(f"  rsi={t['rsi']:5.1f} | R={t['close_R']:+6.2f} | {flag} | {t['entry_dt']} | dist={t['dist_14d_high']:+.1f}%")

    return 0


if __name__ == "__main__":
    sys.exit(main())
