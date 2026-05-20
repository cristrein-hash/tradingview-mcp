#!/usr/bin/env python3
"""
analyze_xau_v1_bubble_buy.py — Etapa 2 (V1)

Aplica em camadas sobre os 43 trades do V0 (IN_OB_ZONE + NAS:1to2):
  V0           — todos os 43 trades (baseline existente)
  V0 + V3      — V0 + dist_from_14d_high > -7% (filtro regime macro validado na Etapa 1)
  V0 + V3 + V1 — V0_filtered + Bubble Buy ativa no candle de entry

Bubble Buy ativa = alguma das plot_2 (Buy), plot_4 (Small Buy),
plot_6 (Medium Buy), plot_8 (Large Buy) ativa no MESMO bar (time match).

Output: tabela comparativa V0 → V0+V3 → V0+V3+V1
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
DIST_THRESHOLD = -7.0  # V3
SELL_PLOTS = {"plot_0", "plot_10"}  # New Sell / Small Sell — absorção institucional
BAR_SECONDS_4H = 14400  # 4h em segundos


class MCP:
    def __init__(self): self.proc=None; self.id=0
    def start(self):
        self.proc = subprocess.Popen([NODE, str(MCP_SERVER)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
        self._raw("initialize", {"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"v1","version":"1.0"}})
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


def stats(trades):
    if not trades: return {"n":0}
    rs = [t['close_R'] for t in trades]
    return {
        "n": len(trades),
        "win%": round(100*sum(1 for r in rs if r>0)/len(rs), 1),
        "avg_R": round(mean(rs), 2),
        "median_R": round(median(rs), 2),
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


def bubble_sell_in_window(bar, entry_time, lookback_bars):
    """True se alguma activation de plot_0 ou plot_10 (Sell bubbles) ocorre
    dentro de (entry_time - lookback_bars*4h, entry_time]."""
    if entry_time is None: return False, []
    min_time = entry_time - (lookback_bars - 1) * BAR_SECONDS_4H  # inclui entry_time + N-1 anteriores
    plots_hit = set()
    for s in (bar.get('pine_shapes_bubbles') or []):
        if 'Bubbles' not in s.get('name',''): continue
        for act in s.get('activations', []):
            t = act.get('time')
            if t is None: continue
            if min_time <= t <= entry_time:
                shapes = act.get('shapes', {}) or {}
                for p in shapes:
                    if p in SELL_PLOTS:
                        plots_hit.add(p)
    return (len(plots_hit) > 0), sorted(plots_hit)


def main():
    if not PAUSE.exists():
        print(f"ERRO: pause flag ausente.", file=sys.stderr); return 1

    print("=== ETAPA 2 (V1): filtro Bubble Buy + V3 baseline ===\n")

    # === Captura OHLCV diário pra reaplicar V3 ===
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

    # === Reconstrói os 43 trades V0 + enriquece ===
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
        if not atr or atr<=0 or st['close'] is None: continue
        if i+HORIZON_4H >= len(bars_4h): continue
        next_close = (bars_4h[i+HORIZON_4H].get('ohlcv_last_40_bars') or [{}])[-1].get('close')
        if next_close is None: continue
        close_R = (next_close - st['close']) / atr
        # V3 dist_from_14d_high
        di = find_daily_idx(st['entry_time']) if st['entry_time'] else None
        dist = dist14[di] if di is not None else None
        # V1a: Bubble Sell no MESMO candle (lookback=1)
        bs_now_active, bs_now_plots = bubble_sell_in_window(b, st['entry_time'], 1)
        # V1b: Bubble Sell nos ÚLTIMOS 3 candles (lookback=3)
        bs_3_active, bs_3_plots = bubble_sell_in_window(b, st['entry_time'], 3)
        trades.append({
            'bar_4h_index': i,
            'entry_time': st['entry_time'],
            'entry_dt': datetime.fromtimestamp(st['entry_time'],tz=timezone.utc).strftime('%Y-%m-%d %H:%M') if st['entry_time'] else '?',
            'close_R': round(close_R, 2),
            'rsi': st['rsi'],
            'dist_14d_high': round(dist, 2) if dist is not None else None,
            'bs_now_active': bs_now_active,
            'bs_now_plots': bs_now_plots,
            'bs_3_active': bs_3_active,
            'bs_3_plots': bs_3_plots,
        })

    print(f"  {len(trades)} trades V0 reconstruídos\n")

    # === Tabelas ===
    v0 = trades
    v3 = [t for t in trades if t['dist_14d_high'] is not None and t['dist_14d_high'] > DIST_THRESHOLD]
    v1a = [t for t in v3 if t['bs_now_active']]          # V0 + V3 + Bubble Sell no candle
    v1b = [t for t in v3 if t['bs_3_active']]            # V0 + V3 + Bubble Sell últimos 3 candles
    v1a_solo = [t for t in trades if t['bs_now_active']] # V1a sem V3 (controle)
    v1b_solo = [t for t in trades if t['bs_3_active']]   # V1b sem V3 (controle)
    v1c = [t for t in v3 if not t['bs_3_active']]        # ANTI-filter: V0+V3 SEM Bubble Sell em 3 candles

    print("=== COMPARATIVO ===\n")
    print(f"{'Versão':<48s}  {'n':>3s}  {'win%':>5s}  {'avg_R':>7s}  {'median_R':>9s}")
    for label, group in [
        ("V0 (todos)", v0),
        ("V0 + V3 (dist > -7%)", v3),
        ("V1a (Bubble Sell mesmo candle, sem V3)", v1a_solo),
        ("V1b (Bubble Sell últimos 3 candles, sem V3)", v1b_solo),
        ("V0 + V3 + V1a (mesmo candle)", v1a),
        ("V0 + V3 + V1b (últimos 3 candles)", v1b),
        ("V0 + V3 + V1c (ANTI: SEM Bubble Sell 3c)", v1c),
    ]:
        s = stats(group)
        if s["n"]==0:
            print(f"  {label:<46s}  {s['n']:>3d}  {'-':>5s}  {'-':>7s}  {'-':>9s}")
        else:
            print(f"  {label:<46s}  {s['n']:>3d}  {s['win%']:>5.1f}  {s['avg_R']:>+7.2f}  {s['median_R']:>+9.2f}")

    # === Detalhe: V1b descarta o quê do V3? ===
    print(f"\n=== Trades V3 descartados pelo V1b (sem Bubble Sell em 3 candles) ===")
    v3_minus_v1b = [t for t in v3 if not t['bs_3_active']]
    for t in sorted(v3_minus_v1b, key=lambda x: x['entry_dt']):
        print(f"  {t['entry_dt']} | R={t['close_R']:+.2f} | dist={t['dist_14d_high']:+.1f}% | rsi={t['rsi']:.1f}")
    s = stats(v3_minus_v1b)
    print(f"  Total descartados: {s['n']}  win%={s.get('win%','-')}  avg_R={s.get('avg_R','-')}  median_R={s.get('median_R','-')}")

    # === Detalhe: V1b mantém o quê? ===
    print(f"\n=== Trades V0+V3+V1b (mantidos) ===")
    for t in sorted(v1b, key=lambda x: x['entry_dt']):
        plots_str = ",".join(t['bs_3_plots'])
        print(f"  {t['entry_dt']} | R={t['close_R']:+.2f} | dist={t['dist_14d_high']:+.1f}% | rsi={t['rsi']:.1f} | sell_bubbles={plots_str}")

    # === Distribuição de tipos de Sell Bubble ===
    print(f"\n=== Bubble Sell types — frequência entre V1b ===")
    from collections import Counter
    plot_count = Counter()
    for t in v1b:
        for p in t['bs_3_plots']: plot_count[p] += 1
    plot_names = {"plot_0":"Sell (Market/Large)","plot_10":"Small Sell"}
    for p, n in plot_count.most_common():
        print(f"  {p} ({plot_names.get(p,'?')}): {n} ocorrências")

    return 0


if __name__ == "__main__":
    sys.exit(main())
