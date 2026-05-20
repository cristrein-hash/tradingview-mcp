#!/usr/bin/env python3
"""
analyze_xau_jul2025_diagnostic.py — Investigar por que estratégia A falhou em julho 2025.

Os 4 losses em julho 2025 (a partir do out-of-sample):
  2025-07-02 18:00  R= -0.95  rsi= 61.1  dist= -2.7%
  2025-07-16 18:00  R= -0.13  rsi= 56.5  dist= -0.9%
  2025-07-23 22:00  R= -2.64  rsi= 51.2  dist= -2.0%
  2025-07-24 02:00  R= -3.05  rsi= 50.4  dist= -2.0%

Os 2 winners em julho 2025:
  2025-07-18 14:00  R= +1.70  rsi= 57.6  dist= -0.8%
  2025-07-21 02:00  R= +5.51  rsi= 57.3  dist= -0.1%

Hipóteses a testar:
  H1 — Regime macro: julho era correção/range, não uptrend
  H2 — Velocidade do pullback (dist evolution nos últimos N candles)
  H3 — Slope EMA50 1D
  H4 — Volatilidade alta (ATR daily)
  H5 — Bubble Sell em janela maior (lookback 10 vs 3)
  H6 — Comparar com dezembro 2025 (mês de ouro)
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

JSONL_OOS = BASE / "alert-bridge" / "logs" / "backtests" / "XAUUSD_240_2025-05-19_to_2026-05-20.jsonl"
JSONL_IS  = BASE / "alert-bridge" / "logs" / "backtests" / "XAUUSD_240_2025-11-19_to_2026-05-19.jsonl"

HORIZON_4H = 10
DIST_THRESHOLD = -7.0
SELL_PLOTS = {"plot_0", "plot_10"}
BAR_SECONDS_4H = 14400


class MCP:
    def __init__(self): self.proc=None; self.id=0
    def start(self):
        self.proc = subprocess.Popen([NODE, str(MCP_SERVER)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
        self._raw("initialize", {"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"diag","version":"1.0"}})
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
    return {'rsi':rsi,'nas':nas,'close':close,'entry_time':entry_time}


def get_atr14(bar):
    ohlcv = bar.get('ohlcv_last_40_bars') or []
    if len(ohlcv)<=1: return None
    closed = ohlcv[:-1][-14:]
    r = [b['high']-b['low'] for b in closed if b.get('high') and b.get('low') and b['high']>b['low']]
    return mean(r) if r else None


def bubble_sell_count(bar, entry_time, lookback_bars):
    if entry_time is None: return 0
    min_time = entry_time - (lookback_bars - 1) * BAR_SECONDS_4H
    plots_seen = set()
    for s in (bar.get('pine_shapes_bubbles') or []):
        if 'Bubbles' not in s.get('name',''): continue
        for act in s.get('activations', []):
            t = act.get('time')
            if t is None: continue
            if min_time <= t <= entry_time:
                for p in (act.get('shapes') or {}):
                    if p in SELL_PLOTS:
                        plots_seen.add((t, p))
    return len(plots_seen)


# Targets pra investigar
JUL_LOSSES = [
    ("2025-07-02 18:00", -0.95, "LOSS"),
    ("2025-07-16 18:00", -0.13, "LOSS"),
    ("2025-07-23 22:00", -2.64, "LOSS"),
    ("2025-07-24 02:00", -3.05, "LOSS"),
]
JUL_WINS = [
    ("2025-07-18 14:00", +1.70, "WIN"),
    ("2025-07-21 02:00", +5.51, "WIN"),
]
DEZ_WINS = [
    ("2025-12-19 11:00", +6.98, "WIN"),
    ("2025-12-19 15:00", +6.50, "WIN"),
    ("2025-12-10 23:00", +5.33, "WIN"),
    ("2025-12-21 23:00", +4.93, "WIN"),
]
DEZ_LOSS = [
    ("2025-12-29 11:00", -2.99, "LOSS"),  # único loser de A in-sample
]


def main():
    if not PAUSE.exists():
        print("ERRO: pause flag ausente.", file=sys.stderr); return 1

    # Captura daily
    print("Captura OHLCV daily (400 bars)...")
    client = MCP(); client.start()
    state = client.call("chart_get_state")
    orig_sym = state.get("symbol"); orig_tf = state.get("resolution")
    try:
        client.call("chart_set_symbol",{"symbol":SYMBOL}); time.sleep(1)
        client.call("chart_set_timeframe",{"timeframe":"D"}); time.sleep(2)
        resp = client.call("data_get_ohlcv",{"count":400,"summary":False})
        daily = sorted([b for b in (resp.get("last_5_bars") or resp.get("bars") or []) if b.get("time")], key=lambda x:x["time"])
        print(f"  {len(daily)} bars 1D ({datetime.fromtimestamp(daily[0]['time'],tz=timezone.utc):%Y-%m-%d} → {datetime.fromtimestamp(daily[-1]['time'],tz=timezone.utc):%Y-%m-%d})")
    finally:
        if orig_sym:
            client.call("chart_set_symbol",{"symbol":orig_sym})
            if orig_tf: client.call("chart_set_timeframe",{"timeframe":orig_tf})
        client.stop()

    # Compute daily features: EMA50, ATR14, dist_14d_high, slope EMA50 (5d)
    closes_d = [b["close"] for b in daily]
    highs_d = [b["high"] for b in daily]
    lows_d = [b["low"] for b in daily]
    ema50_d = ema(closes_d, 50)
    # ATR14 daily
    trs = []
    for i, b in enumerate(daily):
        if i == 0:
            trs.append(b["high"] - b["low"])
        else:
            tr = max(b["high"] - b["low"], abs(b["high"]-closes_d[i-1]), abs(b["low"]-closes_d[i-1]))
            trs.append(tr)
    atr14_d = [None]*len(daily)
    for i in range(14, len(daily)):
        atr14_d[i] = mean(trs[i-14:i])
    # dist_14d_high
    dist14_d = [None]*len(daily)
    for i in range(len(daily)):
        win_hi = max(highs_d[max(0,i-13):i+1])
        dist14_d[i] = (closes_d[i] - win_hi) / win_hi * 100
    # slope EMA50 (5-bar % change)
    slope50 = [None]*len(daily)
    for i in range(55, len(daily)):
        if ema50_d[i] is not None and ema50_d[i-5] is not None and ema50_d[i-5] > 0:
            slope50[i] = (ema50_d[i] - ema50_d[i-5]) / ema50_d[i-5] * 100

    def find_di(ts):
        for i in range(len(daily)-1, -1, -1):
            if daily[i]["time"] <= ts: return i
        return None

    # Load 4H bars (both jsonls)
    print("\nCarregando bars 4H (in-sample + out-of-sample)...")
    bars_is = load_bars(JSONL_IS)
    bars_oos = load_bars(JSONL_OOS)
    all_bars = bars_oos + bars_is  # ordem temporal: oos antes (2025-05) que is (2025-11)
    print(f"  {len(bars_is)} in-sample + {len(bars_oos)} out-of-sample = {len(all_bars)} bars 4H")

    # Index by entry_time
    bars_by_time = {}
    for b in all_bars:
        st = get_state_4h(b)
        if st['entry_time']:
            bars_by_time[st['entry_time']] = b

    def find_bar(target_dt_str):
        target_ts = int(datetime.strptime(target_dt_str+"+0000", "%Y-%m-%d %H:%M%z").timestamp())
        # Procurar bar mais próximo (igual ou imediatamente antes)
        best = None
        best_delta = None
        for ts, b in bars_by_time.items():
            if ts <= target_ts:
                delta = target_ts - ts
                if best_delta is None or delta < best_delta:
                    best_delta = delta
                    best = (ts, b)
        return best

    print("\n" + "="*100)
    print("DIAGNÓSTICO BAR-A-BAR (julho 2025 vs dezembro 2025)")
    print("="*100)

    def describe(label, dt_str, r, flag):
        found = find_bar(dt_str)
        if not found:
            print(f"\n  {label} {dt_str}  NÃO ENCONTRADO no dataset"); return
        ts, b = found
        st = get_state_4h(b)
        atr_4h = get_atr14(b)
        di = find_di(ts)
        # contextual features daily
        ema50 = ema50_d[di] if di is not None else None
        atr_d = atr14_d[di] if di is not None else None
        dist = dist14_d[di] if di is not None else None
        slp = slope50[di] if di is not None else None
        # close vs EMA50
        close = st['close']
        close_vs_ema = ((close - ema50) / ema50 * 100) if (ema50 and close) else None
        # ATR ratio: current 4H ATR / typical (8 bars = 1.3 day)
        # mais simples: atr_4h vs (atr_d / 6) (6 candles 4H ≈ 1 daily bar)
        atr_4h_vs_d = (atr_4h / (atr_d/6)) if (atr_4h and atr_d) else None
        # Bubble Sell counts em diferentes janelas
        bs_3 = bubble_sell_count(b, ts, 3)
        bs_5 = bubble_sell_count(b, ts, 5)
        bs_10 = bubble_sell_count(b, ts, 10)
        # dist change last 5 candles 4H — preciso dos closes anteriores
        ohlcv = b.get('ohlcv_last_40_bars') or []
        if len(ohlcv) >= 6:
            close_now = ohlcv[-1]['close']
            close_5_ago = ohlcv[-6]['close']
            change_5 = (close_now - close_5_ago) / close_5_ago * 100
        else:
            change_5 = None

        rsi_s = f"{st['rsi']:.1f}" if st['rsi'] is not None else "?"
        nas_s = f"{st['nas']:+.2f}" if st['nas'] is not None else "?"
        dist_s = f"{dist:+.1f}%" if dist is not None else "?"
        cve_s = f"{close_vs_ema:+.1f}%" if close_vs_ema is not None else "?"
        slp_s = f"{slp:+.2f}%" if slp is not None else "?"
        atrd_s = f"{atr_d:.1f}" if atr_d is not None else "?"
        atr4_s = f"{atr_4h:.2f}" if atr_4h is not None else "?"
        atrr_s = f"{atr_4h_vs_d:.2f}" if atr_4h_vs_d is not None else "?"
        chg_s = f"{change_5:+.2f}%" if change_5 is not None else "?"
        print(f"\n  [{label}] {dt_str}  R={r:+.2f}  {flag}")
        print(f"    RSI={rsi_s}  NAS_DIST={nas_s}")
        print(f"    daily: dist_14d_high={dist_s}  close_vs_EMA50={cve_s}  slope50_5d={slp_s}/wk  ATR14={atrd_s}")
        print(f"    4H:    ATR14_4h={atr4_s}  ATR ratio (4H/typical)={atrr_s}  Δprice_last_5_4h={chg_s}")
        print(f"    bubble sell counts: 3-bar={bs_3}  5-bar={bs_5}  10-bar={bs_10}")

    print("\n--- JULY 2025 LOSSES ---")
    for dt_s, r, flag in JUL_LOSSES:
        describe("JUL-L", dt_s, r, flag)

    print("\n--- JULY 2025 WINNERS ---")
    for dt_s, r, flag in JUL_WINS:
        describe("JUL-W", dt_s, r, flag)

    print("\n--- DECEMBER 2025 WINNERS (top 4) ---")
    for dt_s, r, flag in DEZ_WINS:
        describe("DEZ-W", dt_s, r, flag)

    print("\n--- DECEMBER 2025 LOSS (único A in-sample) ---")
    for dt_s, r, flag in DEZ_LOSS:
        describe("DEZ-L", dt_s, r, flag)

    # Summary numeric: agregados
    print("\n" + "="*100)
    print("AGREGADOS por grupo")
    print("="*100)

    groups = {
        'JUL_LOSSES': JUL_LOSSES,
        'JUL_WINS': JUL_WINS,
        'DEZ_WINS': DEZ_WINS,
        'DEZ_LOSS': DEZ_LOSS,
    }
    print(f"\n  {'group':<14s}  {'n':>2s}  {'avg_dist14d':>11s}  {'avg_slope50':>11s}  {'avg_atr_ratio':>13s}  {'avg_bs10':>9s}  {'avg_5bar_chg':>12s}")
    for gname, items in groups.items():
        rows = []
        for dt_s, r, flag in items:
            found = find_bar(dt_s)
            if not found: continue
            ts, b = found
            st = get_state_4h(b)
            atr_4h = get_atr14(b)
            di = find_di(ts)
            ema50 = ema50_d[di] if di is not None else None
            atr_d = atr14_d[di] if di is not None else None
            dist = dist14_d[di] if di is not None else None
            slp = slope50[di] if di is not None else None
            atr_4h_vs_d = (atr_4h / (atr_d/6)) if (atr_4h and atr_d) else None
            bs_10 = bubble_sell_count(b, ts, 10)
            ohlcv = b.get('ohlcv_last_40_bars') or []
            change_5 = None
            if len(ohlcv) >= 6:
                close_now = ohlcv[-1]['close']
                close_5_ago = ohlcv[-6]['close']
                change_5 = (close_now - close_5_ago) / close_5_ago * 100
            rows.append({
                'dist': dist, 'slope': slp, 'atr_ratio': atr_4h_vs_d, 'bs_10': bs_10, 'change_5': change_5
            })
        if not rows:
            print(f"  {gname:<14s}  empty"); continue
        def avg_or_none(key):
            vals = [r[key] for r in rows if r.get(key) is not None]
            return mean(vals) if vals else None
        avg_dist = avg_or_none('dist')
        avg_slp = avg_or_none('slope')
        avg_atr = avg_or_none('atr_ratio')
        avg_bs = avg_or_none('bs_10')
        avg_chg = avg_or_none('change_5')
        def f(v, w, p=2):
            if v is None: return "  ?".rjust(w)
            return f"{v:+.{p}f}".rjust(w)
        print(f"  {gname:<14s}  {len(rows):>2d}  {f(avg_dist,11,1)+'%':>11s}  {f(avg_slp,11,2)+'%':>11s}  {f(avg_atr,13,2):>13s}  {f(avg_bs,9,1):>9s}  {f(avg_chg,12,2)+'%':>12s}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
