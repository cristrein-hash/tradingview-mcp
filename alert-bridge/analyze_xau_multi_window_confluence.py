#!/usr/bin/env python3
"""
analyze_xau_multi_window_confluence.py — Confluência sistemática multi-janela.

Sobre baseline V0+V3 (zona OB + NAS_1to2 + dist_14d>-7%), em 6 janelas XAU 4H:
  - Single filters (1 feature adicional)
  - 2-way filters (2 features adicionais)
  - Identifica combos ROBUSTOS: passam gate 70% em >=5 de 6 janelas (com n>=10 cada)
"""
from pathlib import Path
from datetime import datetime, timezone
from statistics import mean, median, stdev
from itertools import combinations
from collections import defaultdict
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
DIST_THRESHOLD = -7.0
SELL_PLOTS = {"plot_0", "plot_10"}
BUY_PLOTS = {"plot_2", "plot_4", "plot_6", "plot_8"}
LARGE_BUY_PLOT = "plot_8"
LARGE_SELL_PLOT = "plot_0"
BAR_SECONDS_4H = 14400
WIN_GATE = 70.0
MIN_N_PER_WINDOW = 10
MIN_WINDOWS_PASSING = 5


class MCP:
    def __init__(self): self.proc=None; self.id=0
    def start(self):
        self.proc = subprocess.Popen([NODE, str(MCP_SERVER)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
        self._raw("initialize", {"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"mw","version":"1.0"}})
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


def get_atr14_4h(bar):
    ohlcv = bar.get('ohlcv_last_40_bars') or []
    if len(ohlcv)<=1: return None
    closed = ohlcv[:-1][-14:]
    r = [b['high']-b['low'] for b in closed if b.get('high') and b.get('low') and b['high']>b['low']]
    return mean(r) if r else None


def bubble_features(bar, entry_time):
    """Retorna features booleanas de bubbles."""
    feats = {
        'BB_now_yes': False, 'BB_now_no': False,
        'BS_now_yes': False, 'BS_now_no': False,
        'BS_3_yes': False, 'BS_3_no': False,
        'BS_5_yes': False, 'BS_5_no': False,
        'BS_10_yes': False, 'BS_10_no': False,
        'LB_now_yes': False, 'LB_now_no': False,
    }
    if entry_time is None:
        for k in feats: feats[k] = False
        return feats
    plots_now = set()
    plots_3, plots_5, plots_10 = set(), set(), set()
    t_now = entry_time
    t_3 = entry_time - 2*BAR_SECONDS_4H
    t_5 = entry_time - 4*BAR_SECONDS_4H
    t_10 = entry_time - 9*BAR_SECONDS_4H
    for s in (bar.get('pine_shapes_bubbles') or []):
        if 'Bubbles' not in s.get('name',''): continue
        for act in s.get('activations', []):
            t = act.get('time')
            if t is None: continue
            sh = act.get('shapes') or {}
            if t == t_now:
                plots_now.update(sh.keys())
            if t_3 <= t <= t_now:
                plots_3.update(sh.keys())
            if t_5 <= t <= t_now:
                plots_5.update(sh.keys())
            if t_10 <= t <= t_now:
                plots_10.update(sh.keys())
    feats['BB_now_yes'] = bool(plots_now & BUY_PLOTS)
    feats['BB_now_no'] = not feats['BB_now_yes']
    feats['BS_now_yes'] = bool(plots_now & SELL_PLOTS)
    feats['BS_now_no'] = not feats['BS_now_yes']
    feats['BS_3_yes'] = bool(plots_3 & SELL_PLOTS)
    feats['BS_3_no'] = not feats['BS_3_yes']
    feats['BS_5_yes'] = bool(plots_5 & SELL_PLOTS)
    feats['BS_5_no'] = not feats['BS_5_yes']
    feats['BS_10_yes'] = bool(plots_10 & SELL_PLOTS)
    feats['BS_10_no'] = not feats['BS_10_yes']
    feats['LB_now_yes'] = LARGE_BUY_PLOT in plots_now
    feats['LB_now_no'] = not feats['LB_now_yes']
    return feats


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


def bucket_value(value, edges, names):
    """Retorna nome do bucket."""
    if value is None: return None
    for i, e in enumerate(edges):
        if value < e: return names[i]
    return names[-1]


def main():
    if not PAUSE.exists():
        print("ERRO: pause flag ausente.", file=sys.stderr); return 1

    print(f"=== CONFLUÊNCIA SISTEMÁTICA MULTI-JANELA — XAU 4H (gate>={WIN_GATE}%, robust>={MIN_WINDOWS_PASSING}/6) ===\n")

    print("Capturando daily 1D (count=2000)...")
    client = MCP(); client.start()
    try:
        state = client.call("chart_get_state")
        orig_sym = state.get("symbol"); orig_tf = state.get("resolution")
        if state.get("symbol","").endswith("XAUUSD") and state.get("resolution") in ("1D","D"):
            resp = client.call("data_get_ohlcv", {"count": 2000, "summary": False})
        else:
            client.call("chart_set_symbol",{"symbol":SYMBOL}); time.sleep(1)
            client.call("chart_set_timeframe",{"timeframe":"D"}); time.sleep(2)
            resp = client.call("data_get_ohlcv", {"count": 2000, "summary": False})
            client.call("chart_set_symbol",{"symbol":orig_sym})
            if orig_tf: client.call("chart_set_timeframe",{"timeframe":orig_tf})
        bars_d = resp.get("last_5_bars") or resp.get("bars") or []
        daily = sorted([b for b in bars_d if b.get("time")], key=lambda x: x["time"])
        print(f"  {len(daily)} bars 1D ({datetime.fromtimestamp(daily[0]['time'],tz=timezone.utc):%Y-%m-%d} → {datetime.fromtimestamp(daily[-1]['time'],tz=timezone.utc):%Y-%m-%d})")
    finally:
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
    close_vs_ema50 = [None]*len(daily)
    for i in range(len(daily)):
        if ema50_d[i] is not None and ema50_d[i] > 0:
            close_vs_ema50[i] = (closes_d[i] - ema50_d[i]) / ema50_d[i] * 100

    def find_di(ts):
        for i in range(len(daily)-1, -1, -1):
            if daily[i]["time"] <= ts: return i
        return None

    # Carrega cada janela e computa features pra cada trade V0+V3
    per_window_trades = {}
    for label, fname in WINDOWS:
        path = JSONL_DIR / fname
        if not path.exists():
            print(f"  [{label}] NÃO encontrado")
            continue
        bars = load_bars(path)
        trades = []
        for i, b in enumerate(bars):
            st = get_state_4h(b)
            if st['close'] is None: continue
            atr_4h = get_atr14_4h(b)
            if not atr_4h or atr_4h <= 0: continue
            if i+HORIZON_4H >= len(bars): continue
            next_close = (bars[i+HORIZON_4H].get('ohlcv_last_40_bars') or [{}])[-1].get('close')
            if next_close is None: continue
            close_R = (next_close - st['close']) / atr_4h
            di = find_di(st['entry_time']) if st['entry_time'] else None
            dist_d = dist14_d[di] if di is not None and di < len(dist14_d) else None
            slope_d = slope50[di] if di is not None and di < len(slope50) else None
            cve = close_vs_ema50[di] if di is not None and di < len(close_vs_ema50) else None
            # baseline V0+V3
            if not (st['in_ob'] and st['nas_bucket']=='NAS_1to2'): continue
            if dist_d is None or dist_d <= DIST_THRESHOLD: continue
            # Features adicionais (categóricas)
            feats = bubble_features(b, st['entry_time'])
            feats['RSI_bucket'] = bucket_value(st['rsi'],
                edges=[50, 55, 60, 65, 70], names=['RSI<50','RSI_50-55','RSI_55-60','RSI_60-65','RSI_65-70','RSI>=70'])
            feats['slope_bucket'] = bucket_value(slope_d,
                edges=[0.3, 0.5, 0.8, 1.2, 1.5], names=['slope<0.3','slope_0.3-0.5','slope_0.5-0.8','slope_0.8-1.2','slope_1.2-1.5','slope>=1.5'])
            feats['cve_bucket'] = bucket_value(cve,
                edges=[2, 4, 6], names=['cve<2','cve_2-4','cve_4-6','cve>=6'])
            feats['dist_bucket'] = bucket_value(dist_d,
                edges=[-3, -1, 0], names=['dist<-3','dist_-3to-1','dist_-1to0','dist>=0'])
            trades.append({
                'window': label,
                'R': round(close_R, 2),
                'feats': feats,
            })
        per_window_trades[label] = trades
        wins = sum(1 for t in trades if t['R']>0)
        print(f"  [{label}] {len(trades)} V0+V3 baseline ({wins} winners, {100*wins/max(1,len(trades)):.1f}%)")

    # Lista de features candidatas
    feature_keys = ['BB_now_yes','BB_now_no',
                    'BS_now_yes','BS_now_no',
                    'BS_3_yes','BS_3_no',
                    'BS_5_yes','BS_5_no',
                    'BS_10_yes','BS_10_no',
                    'LB_now_yes','LB_now_no',
                    'RSI_bucket','slope_bucket','cve_bucket','dist_bucket']

    # Coletar valores possíveis de cada feature
    feature_values = {}
    for fk in feature_keys:
        vals = set()
        for trades in per_window_trades.values():
            for t in trades:
                v = t['feats'].get(fk)
                if v is not None:
                    if isinstance(v, bool):
                        vals.add(fk if v else None)
                    else:
                        vals.add(v)
        feature_values[fk] = sorted(v for v in vals if v is not None)

    # Predicates: lista de (predicate_label, fn(trade) -> bool)
    predicates = []
    # singles
    for fk in feature_keys:
        for v in feature_values[fk]:
            if fk.endswith('_yes') or fk.endswith('_no'):
                # boolean style
                want = (v == fk)
                def make_p(fkk=fk, ww=want):
                    return lambda t: t['feats'].get(fkk) == ww
                predicates.append((f"{fk}", make_p()))
            else:
                def make_p(fkk=fk, vv=v):
                    return lambda t: t['feats'].get(fkk) == vv
                predicates.append((f"{v}", make_p()))

    # Dedupe predicates by label
    seen = set()
    uniq_preds = []
    for lbl, fn in predicates:
        if lbl not in seen:
            seen.add(lbl); uniq_preds.append((lbl, fn))
    predicates = uniq_preds

    print(f"\nTotal predicates singles: {len(predicates)}")

    def eval_window(trades, pred):
        sub = [t for t in trades if pred(t)]
        rs = [t['R'] for t in sub]
        if not rs: return {'n':0, 'win%':None, 'avg_R':None}
        wins = sum(1 for r in rs if r>0)
        return {'n':len(rs), 'win%':100*wins/len(rs), 'avg_R':mean(rs)}

    def eval_combo(label, fn):
        """Roda em todas as janelas. Retorna lista de window stats e summary."""
        per_w = []
        windows_passing = 0
        windows_evaluated = 0
        total_trades = []
        for wlabel, trades in per_window_trades.items():
            sub = [t for t in trades if fn(t)]
            rs = [t['R'] for t in sub]
            if not rs:
                per_w.append((wlabel, None))
                continue
            wins = sum(1 for r in rs if r>0)
            stats = {'n':len(rs), 'win%':100*wins/len(rs), 'avg_R':mean(rs), 'sum_R':sum(rs)}
            per_w.append((wlabel, stats))
            if stats['n'] >= MIN_N_PER_WINDOW:
                windows_evaluated += 1
                if stats['win%'] >= WIN_GATE:
                    windows_passing += 1
            total_trades.extend(sub)
        # combined
        comb_rs = [t['R'] for t in total_trades]
        if comb_rs:
            comb = {'n': len(comb_rs), 'win%': 100*sum(1 for r in comb_rs if r>0)/len(comb_rs),
                    'avg_R': mean(comb_rs), 'sum_R': sum(comb_rs)}
        else:
            comb = None
        return {'per_w':per_w, 'wp':windows_passing, 'we':windows_evaluated, 'combined':comb, 'label':label}

    # === BASELINE ===
    print(f"\n{'='*120}")
    print("BASELINE V0+V3 (nenhum filtro adicional)")
    print(f"{'='*120}")
    result = eval_combo("BASELINE", lambda t: True)
    print_combo(result)

    # === SINGLES ===
    print(f"\n{'='*120}")
    print(f"SINGLES — Top robust (passa gate em >={MIN_WINDOWS_PASSING}/6 janelas com n>={MIN_N_PER_WINDOW})")
    print(f"{'='*120}")
    single_results = []
    for lbl, fn in predicates:
        r = eval_combo(lbl, fn)
        single_results.append(r)
    # Sort: wp desc, then combined win% desc, then combined n desc
    single_results.sort(key=lambda r: (-r['wp'], -(r['combined']['win%'] if r['combined'] else 0), -(r['combined']['n'] if r['combined'] else 0)))
    print(f"\n{'filter':<22s} {'wp/we':>6s} {'combined n':>10s} {'win%':>6s} {'avg_R':>7s} {'sum_R':>8s} | per janela (n/win%/avg)")
    for r in single_results[:30]:
        print_combo_summary(r)

    # === 2-WAY ===
    print(f"\n{'='*120}")
    print(f"2-WAY — Top robust (passa gate em >={MIN_WINDOWS_PASSING}/6 com n>={MIN_N_PER_WINDOW})")
    print(f"{'='*120}")
    two_way_results = []
    for (lbl1, fn1), (lbl2, fn2) in combinations(predicates, 2):
        # Skip pairs from same feature (mutuamente excludentes)
        if pred_feature_key(lbl1) == pred_feature_key(lbl2): continue
        combined_label = f"{lbl1} + {lbl2}"
        combined_fn = lambda t, f1=fn1, f2=fn2: f1(t) and f2(t)
        r = eval_combo(combined_label, combined_fn)
        # Only keep if has SOME data (combined n>0)
        if r['combined'] and r['combined']['n'] > 0:
            two_way_results.append(r)
    two_way_results.sort(key=lambda r: (-r['wp'], -(r['combined']['win%'] if r['combined'] else 0), -(r['combined']['n'] if r['combined'] else 0)))
    print(f"\n{'filter':<48s} {'wp/we':>6s} {'comb_n':>7s} {'win%':>6s} {'avg_R':>7s} {'sum_R':>8s} | per janela")
    for r in two_way_results[:40]:
        print_combo_summary(r, width=48)

    return 0


def pred_feature_key(label):
    """Extrai feature key do label pra evitar pares dentro da mesma feature."""
    if label.startswith('RSI'): return 'RSI'
    if label.startswith('slope'): return 'slope'
    if label.startswith('cve'): return 'cve'
    if label.startswith('dist_'): return 'dist'
    if label.startswith('BB_now'): return 'BB_now'
    if label.startswith('BS_now'): return 'BS_now'
    if label.startswith('BS_3'): return 'BS_3'
    if label.startswith('BS_5'): return 'BS_5'
    if label.startswith('BS_10'): return 'BS_10'
    if label.startswith('LB_now'): return 'LB_now'
    return label


def print_combo(result):
    label = result['label']
    print(f"\n  [{label}]")
    for wlabel, stats in result['per_w']:
        if stats is None or stats['n']==0:
            print(f"    {wlabel:<14s}: n=0")
        else:
            valid = "VÁLIDA" if stats['win%'] >= WIN_GATE else "  -   "
            print(f"    {wlabel:<14s}: n={stats['n']:>3d}  win%={stats['win%']:>5.1f}  avg_R={stats['avg_R']:>+6.2f}  sum_R={stats['sum_R']:>+6.2f}  {valid}")
    if result['combined']:
        c = result['combined']
        print(f"    COMBINED:       n={c['n']:>3d}  win%={c['win%']:>5.1f}  avg_R={c['avg_R']:>+6.2f}  sum_R={c['sum_R']:>+6.2f}")
        print(f"    janelas passando: {result['wp']}/{result['we']} (n>={MIN_N_PER_WINDOW})")


def print_combo_summary(result, width=22):
    label = result['label']
    c = result['combined']
    if not c: return
    # Per-window mini
    cells = []
    for wlabel, stats in result['per_w']:
        if stats is None or stats['n']==0:
            cells.append(f"{wlabel[:4]}:-")
        else:
            marker = "✓" if stats['win%'] >= WIN_GATE and stats['n']>=MIN_N_PER_WINDOW else "·"
            cells.append(f"{wlabel[:4]}:{stats['n']:>2d}/{stats['win%']:>3.0f}{marker}")
    per_w_str = "  ".join(cells)
    print(f"{label:<{width}s} {result['wp']:>2d}/{result['we']:<2d}   {c['n']:>5d} {c['win%']:>5.1f}  {c['avg_R']:>+6.2f}  {c['sum_R']:>+7.2f} | {per_w_str}")


if __name__ == "__main__":
    sys.exit(main())
