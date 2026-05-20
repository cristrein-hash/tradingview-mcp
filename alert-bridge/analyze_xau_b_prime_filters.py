#!/usr/bin/env python3
"""
analyze_xau_b_prime_filters.py — Testar B' + filtros Bubble Sell.

Setup B' (nova base adotada):
  - IN_OB_ZONE (Custom OB demand)
  - NAS_1to2 (NAS_DIST 1..2 ATR acima EMA)
  - dist_14d_high entre -1% e 0% (PRÁTICAMENTE no topo dos últimos 14d)

Filtros adicionais a testar:
  - B' (sozinho)
  - B' + sem Bubble Sell em 3 candles
  - B' + sem Bubble Sell em 5 candles
  - B' + sem Bubble Sell em 10 candles

Output: stats por janela + combined.
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

WINDOWS = [
    ("W1_2023H1", "XAUUSD_240_2023-01-19_to_2026-05-20.jsonl"),
    ("W2_2023H2", "XAUUSD_240_2023-07-19_to_2026-05-20.jsonl"),
    ("W3_2024H1", "XAUUSD_240_2024-01-19_to_2026-05-20.jsonl"),
    ("W4_2024H2", "XAUUSD_240_2024-07-19_to_2026-05-20.jsonl"),
    ("W5_2025May", "XAUUSD_240_2025-05-19_to_2026-05-20.jsonl"),
    ("W6_2025Nov", "XAUUSD_240_2025-11-19_to_2026-05-19.jsonl"),
]
JSONL_DIR = BASE / "alert-bridge" / "logs" / "backtests"

HORIZON_4H = 10
DIST_LOW = -1.0   # B': dist_14d entre [DIST_LOW, DIST_HIGH]
DIST_HIGH = 0.0
SELL_PLOTS = {"plot_0", "plot_10"}
BAR_SECONDS_4H = 14400
WIN_GATE = 70.0
MIN_N_PER_WINDOW = 10


class MCP:
    def __init__(self): self.proc=None; self.id=0
    def start(self):
        self.proc = subprocess.Popen([NODE, str(MCP_SERVER)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
        self._raw("initialize", {"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"bp","version":"1.0"}})
        self.proc.stdin.write(json.dumps({"jsonrpc":"2.0","method":"notifications/initialized","params":{}})+"\n"); self.proc.stdin.flush()
    def stop(self):
        if self.proc:
            try: self.proc.stdin.close()
            except: pass
            try: self.proc.terminate(); self.proc.wait(timeout=5)
            except: self.proc.kill()
    def _raw(self, m, p, t=120):
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
    def call(self, n, a=None, t=120):
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
    nas=None
    for s in (bar.get('study_values') or []):
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
    return {'nas_bucket':nas_b,'in_ob':in_ob,'close':close,'entry_time':entry_time}


def get_atr14_4h(bar):
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
    return {'n':len(rs), 'win%':100*wins/len(rs),
            'avg_R':mean(rs), 'median_R':median(rs),
            'sum_R':sum(rs), 'min_R':min(rs), 'max_R':max(rs)}


def main():
    if not PAUSE.exists():
        print("ERRO: pause flag ausente.", file=sys.stderr); return 1

    print("=== B' + Bubble Sell filters | 6 janelas XAU 4H ===\n")
    print("B' = IN_OB + NAS_1to2 + dist_14d in [-1.0, 0.0]\n")

    print("Capturando daily 1D (count=2000)...")
    client = MCP(); client.start()
    try:
        resp = client.call("data_get_ohlcv", {"count": 2000, "summary": False})
        bars_d = resp.get("last_5_bars") or resp.get("bars") or []
        daily = sorted([b for b in bars_d if b.get("time")], key=lambda x: x["time"])
        print(f"  {len(daily)} bars 1D ({datetime.fromtimestamp(daily[0]['time'],tz=timezone.utc):%Y-%m-%d} → {datetime.fromtimestamp(daily[-1]['time'],tz=timezone.utc):%Y-%m-%d})")
    finally:
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

    per_window_trades = {}
    for label, fname in WINDOWS:
        path = JSONL_DIR / fname
        if not path.exists(): continue
        bars = load_bars(path)
        trades = []
        for i, b in enumerate(bars):
            st = get_state_4h(b)
            if st['close'] is None: continue
            atr = get_atr14_4h(b)
            if not atr or atr<=0: continue
            if i+HORIZON_4H >= len(bars): continue
            next_close = (bars[i+HORIZON_4H].get('ohlcv_last_40_bars') or [{}])[-1].get('close')
            if next_close is None: continue
            close_R = (next_close - st['close']) / atr
            di = find_di(st['entry_time']) if st['entry_time'] else None
            dist = dist14_d[di] if di is not None and di < len(dist14_d) else None
            # B' filter: V0 + dist in [-1, 0]
            if not (st['in_ob'] and st['nas_bucket']=='NAS_1to2'): continue
            if dist is None or dist < DIST_LOW or dist > DIST_HIGH: continue
            bs_3 = bubble_sell_in_window(b, st['entry_time'], 3)
            bs_5 = bubble_sell_in_window(b, st['entry_time'], 5)
            bs_10 = bubble_sell_in_window(b, st['entry_time'], 10)
            trades.append({
                'window': label,
                'entry_time': st['entry_time'],
                'entry_dt': datetime.fromtimestamp(st['entry_time'],tz=timezone.utc).strftime('%Y-%m-%d %H:%M') if st['entry_time'] else '?',
                'R': round(close_R, 2),
                'dist_14d': dist,
                'bs_3': bs_3,
                'bs_5': bs_5,
                'bs_10': bs_10,
            })
        per_window_trades[label] = trades

    variants = [
        ("B' sozinho",       lambda t: True),
        ("B' + NO BS 3",     lambda t: not t['bs_3']),
        ("B' + NO BS 5",     lambda t: not t['bs_5']),
        ("B' + NO BS 10",    lambda t: not t['bs_10']),
    ]

    print(f"\n{'variante':<22s}  {'janela':<12s}  {'n':>3s}  {'win%':>5s}  {'avg_R':>7s}  {'med_R':>6s}  {'sum_R':>7s}  valid?  pass_5_of_6?")
    print("-"*135)
    for vname, vfn in variants:
        per_w_passed = 0
        per_w_evaluated = 0
        combined_trades = []
        for wlabel in (w[0] for w in WINDOWS):
            trades = per_window_trades.get(wlabel, [])
            sub = [t for t in trades if vfn(t)]
            rs = [t['R'] for t in sub]
            s = stats_block(rs)
            combined_trades.extend(sub)
            if s and s['n'] >= MIN_N_PER_WINDOW:
                per_w_evaluated += 1
                if s['win%'] >= WIN_GATE:
                    per_w_passed += 1
                valid = "VÁLIDA" if s['win%'] >= WIN_GATE else "  -   "
                print(f"{vname:<22s}  {wlabel:<12s}  {s['n']:>3d}  {s['win%']:>5.1f}  {s['avg_R']:>+7.2f}  {s['median_R']:>+6.2f}  {s['sum_R']:>+7.2f}  {valid}  -")
            elif s:
                valid = "n<10"
                print(f"{vname:<22s}  {wlabel:<12s}  {s['n']:>3d}  {s['win%']:>5.1f}  {s['avg_R']:>+7.2f}  {s['median_R']:>+6.2f}  {s['sum_R']:>+7.2f}  {valid}  -")
            else:
                print(f"{vname:<22s}  {wlabel:<12s}  {0:>3d}  {'-':>5s}  {'-':>7s}  {'-':>6s}  {'-':>7s}  n=0   -")
        # combined
        rs = [t['R'] for t in combined_trades]
        sc = stats_block(rs)
        if sc:
            valid = "VÁLIDA" if sc['win%'] >= WIN_GATE else "  -   "
            robust = f"{per_w_passed}/{per_w_evaluated}"
            print(f"{vname:<22s}  {'COMBINED':<12s}  {sc['n']:>3d}  {sc['win%']:>5.1f}  {sc['avg_R']:>+7.2f}  {sc['median_R']:>+6.2f}  {sc['sum_R']:>+7.2f}  {valid}  {robust:>4s}")
        print()

    # Tabela detalhada dos trades por janela e variante (apenas variante final)
    print(f"\n{'='*135}")
    print("Trade list — B' (sozinho)")
    print(f"{'='*135}")
    total_trades = []
    for wlabel in (w[0] for w in WINDOWS):
        trades = per_window_trades.get(wlabel, [])
        if not trades: continue
        print(f"\n  [{wlabel}] {len(trades)} trades:")
        for t in sorted(trades, key=lambda x: x['entry_time'] or 0):
            flag = "WIN " if t['R']>0 else "LOSS"
            bs_marks = ""
            if t['bs_3']: bs_marks += "BS3"
            if t['bs_5'] and not t['bs_3']: bs_marks += " BS5"
            if t['bs_10'] and not t['bs_5']: bs_marks += " BS10"
            if not bs_marks: bs_marks = "clean"
            print(f"    {t['entry_dt']}  R={t['R']:+6.2f}  dist={t['dist_14d']:+5.2f}%  {bs_marks:<12s}  {flag}")
            total_trades.append(t)

    return 0


if __name__ == "__main__":
    sys.exit(main())
