#!/usr/bin/env python3
"""
analyze_xau_h3_bubble_lookback.py — Testar V1c com lookbacks variados.

Setup A = IN_OB + NAS_1to2 + dist_14d > -7% + (variations of NOT Bubble Sell window)

Lookbacks testados: 3 (atual), 5, 7, 10, 15, 20

Pra cada lookback:
  - stats no dataset combinado (in + out-of-sample)
  - per-window stats (preserva detection de robustez OOS)
  - lista de trades descartados (winners e losers)
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
LOOKBACKS = [0, 3, 5, 7, 10, 15, 20]  # 0 = sem V1c (baseline V0+V3)


class MCP:
    def __init__(self): self.proc=None; self.id=0
    def start(self):
        self.proc = subprocess.Popen([NODE, str(MCP_SERVER)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
        self._raw("initialize", {"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"h3","version":"1.0"}})
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
    if lookback_bars <= 0: return False
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


def main():
    if not PAUSE.exists():
        print("ERRO: pause flag ausente.", file=sys.stderr); return 1

    # Daily fetch
    print("Captura OHLCV daily...")
    client = MCP(); client.start()
    state = client.call("chart_get_state")
    orig_sym = state.get("symbol"); orig_tf = state.get("resolution")
    try:
        client.call("chart_set_symbol",{"symbol":SYMBOL}); time.sleep(1)
        client.call("chart_set_timeframe",{"timeframe":"D"}); time.sleep(2)
        resp = client.call("data_get_ohlcv",{"count":400,"summary":False})
        daily = sorted([b for b in (resp.get("last_5_bars") or resp.get("bars") or []) if b.get("time")], key=lambda x:x["time"])
    finally:
        if orig_sym:
            client.call("chart_set_symbol",{"symbol":orig_sym})
            if orig_tf: client.call("chart_set_timeframe",{"timeframe":orig_tf})
        client.stop()

    closes_d = [b["close"] for b in daily]
    highs_d = [b["high"] for b in daily]
    dist14_d = [None]*len(daily)
    for i in range(len(daily)):
        win_hi = max(highs_d[max(0,i-13):i+1])
        dist14_d[i] = (closes_d[i] - win_hi) / win_hi * 100

    def find_di(ts):
        for i in range(len(daily)-1, -1, -1):
            if daily[i]["time"] <= ts: return i
        return None

    # Carrega 4H
    bars_oos = load_bars(JSONL_OOS)
    bars_is = load_bars(JSONL_IS)
    print(f"  4H: {len(bars_oos)} OOS + {len(bars_is)} IS = {len(bars_oos)+len(bars_is)}")

    def trades_for_window(bars):
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
            # Apply A base filters (V0 + V3)
            if not (st['in_ob'] and st['nas_bucket']=='NAS_1to2'): continue
            if dist is None or dist <= DIST_THRESHOLD: continue
            # bs_3, bs_5, bs_7, bs_10, bs_15, bs_20
            bs_flags = {lb: bubble_sell_in_window(b, st['entry_time'], lb) for lb in LOOKBACKS if lb > 0}
            out.append({
                'entry_time': st['entry_time'],
                'entry_dt': datetime.fromtimestamp(st['entry_time'],tz=timezone.utc).strftime('%Y-%m-%d %H:%M') if st['entry_time'] else '?',
                'R': round(close_R, 2),
                'rsi': st['rsi'],
                'dist_14d': dist,
                'bs_flags': bs_flags,
            })
        return out

    trades_oos = trades_for_window(bars_oos)
    trades_is = trades_for_window(bars_is)
    trades_combined = trades_oos + trades_is
    print(f"  trades A baseline (V0+V3): {len(trades_oos)} OOS + {len(trades_is)} IS = {len(trades_combined)} combined\n")

    def f(s):
        if not s or s['n']==0:
            return f"{0:>3d}  {'-':>5s}  {'-':>7s}  {'-':>9s}  {'-':>7s}  {'-':>7s}  {'-':>6s}  {'-':>7s}"
        valid = "VÁLIDA" if s['win%'] >= WIN_GATE else "  -   "
        return (f"{s['n']:>3d}  {s['win%']:>5.1f}  {s['avg_R']:>+7.2f}  {s['median_R']:>+9.2f}  "
                f"{s['min_R']:>+7.2f}  {s['max_R']:>+7.2f}  {s['std_R']:>6.2f}  {s['sum_R']:>+7.2f}  {valid}")

    print("="*135)
    print("COMPARATIVO LOOKBACKS — Strategy A com V1c em diferentes janelas")
    print("="*135)
    print(f"\n{'lookback':<10s}  {'janela':<22s}  {'n':>3s}  {'win%':>5s}  {'avg_R':>7s}  {'median_R':>9s}  {'min_R':>7s}  {'max_R':>7s}  {'std_R':>6s}  {'sum_R':>7s}  valid?")
    print("-"*135)

    best_combined = None

    for lb in LOOKBACKS:
        for label, trades in [('IN-SAMPLE', trades_is), ('OUT-OF-SAMPLE', trades_oos), ('COMBINED', trades_combined)]:
            if lb == 0:
                kept = trades
            else:
                kept = [t for t in trades if not t['bs_flags'].get(lb, False)]
            rs = [t['R'] for t in kept]
            s = stats_block(rs)
            lb_label = 'V0+V3 (no V1c)' if lb==0 else f'V1c bs_{lb}'
            print(f"{lb_label:<10s}  {label:<22s}  {f(s)}")
            if label == 'COMBINED' and s:
                if best_combined is None or (s['win%'] >= WIN_GATE and s['avg_R'] > best_combined[1]['avg_R']):
                    best_combined = (lb_label, s)
        print()

    print("\n" + "="*135)
    print("DETALHE: trades descartados quando lookback aumenta (V1c bs_3 → bs_10, combinado)")
    print("="*135)
    bs3_kept = [t for t in trades_combined if not t['bs_flags'].get(3, False)]
    bs10_kept = [t for t in trades_combined if not t['bs_flags'].get(10, False)]
    bs3_set = {t['entry_time'] for t in bs3_kept}
    bs10_set = {t['entry_time'] for t in bs10_kept}
    # diff: trades cortados ao mudar de 3 → 10
    cut_by_10 = [t for t in bs3_kept if t['entry_time'] not in bs10_set]
    print(f"\nTrades em V1c bs_3 mas cortados por V1c bs_10: n={len(cut_by_10)}")
    if cut_by_10:
        rs = [t['R'] for t in cut_by_10]
        wins = sum(1 for r in rs if r>0); losses = len(rs)-wins
        print(f"  destes: {wins} winners ({100*wins/len(rs):.1f}%) | {losses} losers | sum_R={sum(rs):+.2f}  avg_R={mean(rs):+.2f}")
        for t in sorted(cut_by_10, key=lambda x: x['entry_time'] or 0):
            flag = "WIN " if t['R']>0 else "LOSS"
            print(f"    {t['entry_dt']}  R={t['R']:+6.2f}  rsi={t['rsi']:5.1f}  {flag}")

    # Outros lookbacks: extras cortados além do bs_10
    print("\n" + "="*135)
    print("DETALHE: trades cortados em cada lookback (cumulativo)")
    print("="*135)
    base_set = {t['entry_time'] for t in trades_combined}  # V0+V3 todos
    for lb in [3, 5, 7, 10, 15, 20]:
        kept = [t for t in trades_combined if not t['bs_flags'].get(lb, False)]
        cut = [t for t in trades_combined if t['bs_flags'].get(lb, False)]
        cut_wins = sum(1 for t in cut if t['R']>0)
        cut_losses = len(cut)-cut_wins
        kept_wins = sum(1 for t in kept if t['R']>0)
        kept_losses = len(kept)-kept_wins
        sum_cut = sum(t['R'] for t in cut)
        print(f"  V1c bs_{lb:<2d}: cortados n={len(cut):>2d} ({cut_wins}W/{cut_losses}L sum_R={sum_cut:+.2f})  |  mantidos n={len(kept):>2d} ({kept_wins}W/{kept_losses}L)")

    print("\nBest combined (max avg_R com gate VÁLIDA):")
    if best_combined:
        lbl, s = best_combined
        print(f"  {lbl}: n={s['n']} win%={s['win%']:.1f} avg_R={s['avg_R']:+.2f}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
