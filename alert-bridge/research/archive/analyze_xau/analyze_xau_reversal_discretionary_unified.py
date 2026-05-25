#!/usr/bin/env python3
"""
analyze_xau_reversal_discretionary_unified.py — Validar REVERSAL_DISCRETIONARY unificado.

Setup unificado:
  PRE-REQUISITOS (TODOS):
    P1. NAS LONG label nos últimos 5 bars
    P2. dist 14d high ≤ -5% (região de fundo macro)
    P3. NAS_DIST ≤ -1 (preço esticado abaixo média 4H)

  TRIGGER ESTRUTURAL (QUALQUER UM):
    T1. LuxAlgo BOS_BEAR ou CHoCH_BEAR no bar atual (Δ ≤ 2) — exhaustion
    T2. LuxAlgo Strong Low_BULL ou CHoCH_BULL recente (Δ ≤ 5) — reversal confirmado
    T3. LuxAlgo BOS_BULL recente (Δ ≤ 5) — continuação após fundo

Horizon padrão: H=20 close-only.
Dataset: v5 (8 janelas com LuxAlgo + CVDs capturados).
"""
from pathlib import Path
from datetime import datetime, timezone
from statistics import mean, median
import json, sys, subprocess, time
from collections import defaultdict

BASE = Path(__file__).parent.parent
JSONL_DIR = BASE / "alert-bridge" / "logs" / "backtests"
MCP_SERVER = BASE / "src" / "server.js"
NODE = "/opt/homebrew/bin/node"
PAUSE = Path("/tmp/claude_recheck.paused")

WINDOWS_V5 = [
    ("W1_2023H1",    "XAUUSD_240_2023-01-19_to_2026-05-21_v5.jsonl"),
    ("W2_2023H2",    "XAUUSD_240_2023-07-19_to_2026-05-21_v5.jsonl"),
    ("W3_2024H1",    "XAUUSD_240_2024-01-19_to_2026-05-21_v5.jsonl"),
    ("W4_2024H2",    "XAUUSD_240_2024-07-19_to_2026-05-21_v5.jsonl"),
    ("W5_2025May",   "XAUUSD_240_2025-05-19_to_2026-05-21_v5.jsonl"),
    ("W6_2025Sep",   "XAUUSD_240_2025-09-15_to_2026-05-21_v5.jsonl"),
    ("W7_2025Nov",   "XAUUSD_240_2025-11-19_to_2026-05-21_v5.jsonl"),
    ("W8_2026Mar",   "XAUUSD_240_2026-03-19_to_2026-05-21_v5.jsonl"),
]

DREAM_LONG_DISCR = [
    ("#1",  "2026-05-04 15:00"),
    ("#6",  "2026-03-12 10:00"),
    ("#8",  "2026-03-20 14:00"),
    ("#10", "2026-03-24 10:00"),
    ("#11", "2026-01-29 19:00"),
    ("#13", "2026-02-03 03:00"),
]

LUX_BULL_COLOR = 4286683400
LUX_BEAR_COLOR = 4282726130
HORIZON_4H = 20
WIN_GATE = 70.0
TOLERANCE_SEC = 7200
BAR_SECONDS_4H = 14400


class MCP:
    def __init__(self): self.proc=None; self.id=0
    def start(self):
        self.proc = subprocess.Popen([NODE, str(MCP_SERVER)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
        self._raw("initialize",{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"d","version":"1.0"}})
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
        deadline=time.monotonic()+t
        while time.monotonic()<deadline:
            line=self.proc.stdout.readline()
            if not line: raise RuntimeError("closed")
            try:
                r=json.loads(line)
                if r.get("id")==self.id: return r
            except: continue
        return None
    def call(self, n, a=None, t=120):
        r=self._raw("tools/call",{"name":n,"arguments":a or {}},t)
        if "error" in r: return {}
        c=r.get("result",{}).get("content",[])
        if c and c[0].get("type")=="text":
            try: return json.loads(c[0]["text"])
            except: return {}
        return {}


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


def get_atr14(bar):
    ohlcv = bar.get('ohlcv_last_40_bars') or []
    if len(ohlcv)<=1: return None
    closed = ohlcv[:-1][-14:]
    r=[b['high']-b['low'] for b in closed if b.get('high') and b.get('low') and b['high']>b['low']]
    return mean(r) if r else None


def has_nas_label_recent(bar, want_text, max_delta=5):
    for s in (bar.get('pine_labels') or []):
        if 'NAS' not in s.get('name','').upper(): continue
        labels = s.get('labels') or []
        if not labels: continue
        xs = [l.get('x') for l in labels if l.get('x') is not None]
        if not xs: continue
        max_x = max(xs)
        for l in labels:
            lx = l.get('x'); txt = (l.get('text') or '').upper()
            if lx is None or txt != want_text: continue
            if 0 <= max_x-lx <= max_delta: return True
    return False


def get_nas_dist(bar):
    for s in (bar.get('study_values') or []):
        if 'NAS' in s.get('name',''):
            try: return float(s.get('values',{}).get('NAS_DISTANCE_FROM_EMA_ATR','').replace('−','-'))
            except: return None
    return None


def get_lux_labels(bar, max_delta=20):
    """Retorna [(delta, text, direction)]."""
    out = []
    for s in (bar.get('pine_labels') or []):
        if 'LUXALGO' not in s.get('name','').upper(): continue
        labels = s.get('labels') or []
        if not labels: continue
        xs = [l.get('x') for l in labels if l.get('x') is not None]
        if not xs: continue
        max_x = max(xs)
        for l in labels:
            lx = l.get('x'); txt = (l.get('text') or '')
            if lx is None: continue
            delta = max_x - lx
            if 0 <= delta <= max_delta:
                tc = l.get('textColor')
                direction = 'BULL' if tc == LUX_BULL_COLOR else 'BEAR' if tc == LUX_BEAR_COLOR else '?'
                out.append((delta, txt, direction))
        return out
    return out


def check_T1_exhaustion(lux_labels):
    """LuxAlgo BOS_BEAR ou CHoCH_BEAR no bar atual (Δ ≤ 2)."""
    for delta, txt, dirn in lux_labels:
        if delta <= 2 and dirn == 'BEAR' and txt in ('BOS', 'CHoCH'):
            return True
    return False


def check_T2_reversal(lux_labels):
    """LuxAlgo Strong Low BULL ou CHoCH_BULL recente (Δ ≤ 5)."""
    for delta, txt, dirn in lux_labels:
        if delta <= 5 and dirn == 'BULL' and (txt == 'CHoCH' or txt == 'Strong Low'):
            return True
    return False


def check_T3_continuation(lux_labels):
    """LuxAlgo BOS_BULL recente (Δ ≤ 5)."""
    for delta, txt, dirn in lux_labels:
        if delta <= 5 and dirn == 'BULL' and txt == 'BOS':
            return True
    return False


def stats_block(rs):
    if not rs: return None
    wins = sum(1 for r in rs if r>0)
    return {'n':len(rs),'win%':100*wins/len(rs),'avg_R':mean(rs),'median_R':median(rs),'sum_R':sum(rs)}


def main():
    if not PAUSE.exists():
        print("ERRO pause flag ausente.", file=sys.stderr); return 1

    print(f"=== REVERSAL_DISCRETIONARY UNIFIED — sweep v5 ===\n")

    # Pra cada janela JSONL, vou sintetizar daily local (mais robusto que fetch limitado)
    def synth_daily_from_bars(bars):
        """Agrega bars 4H em daily (UTC day boundary)."""
        series_4h = []
        for b in bars:
            ohlcv = b.get('ohlcv_last_40_bars') or []
            if not ohlcv: continue
            last = ohlcv[-1]
            if last.get('time') is None: continue
            series_4h.append(last)
        # Dedup
        seen={}
        for c in series_4h:
            seen[c['time']] = c
        series_4h = sorted(seen.values(), key=lambda x: x['time'])
        # Agrega por dia UTC
        by_day={}
        for c in series_4h:
            if c.get('close') is None: continue
            dt = datetime.fromtimestamp(c['time'], tz=timezone.utc)
            day_key = int(datetime(dt.year, dt.month, dt.day, tzinfo=timezone.utc).timestamp())
            if day_key not in by_day:
                by_day[day_key] = {'time':day_key,'open':c['open'],'high':c['high'],'low':c['low'],'close':c['close']}
            else:
                d = by_day[day_key]
                if c['high'] is not None and (d['high'] is None or c['high']>d['high']): d['high']=c['high']
                if c['low'] is not None and (d['low'] is None or c['low']<d['low']): d['low']=c['low']
                d['close']=c['close']
        daily = sorted(by_day.values(), key=lambda x: x['time'])
        return daily

    # Load 8 windows + sintetiza daily POR JANELA (mais robusto)
    print("Carregando 8 janelas v5 + sintetizando daily local...")
    per_window_data = {}  # label -> {bars: [], daily: [], dist14h: []}
    for label, fname in WINDOWS_V5:
        p = JSONL_DIR / fname
        if not p.exists():
            print(f"  WARN {fname} missing"); continue
        bars = load_bars(p)
        daily = synth_daily_from_bars(bars)
        closes_d = [b['close'] for b in daily]
        highs_d = [b['high'] for b in daily]
        dist14h_w = [None]*len(daily)
        for i in range(len(daily)):
            win = highs_d[max(0,i-13):i+1]
            dist14h_w[i] = (closes_d[i]-max(win))/max(win)*100
        per_window_data[label] = {'bars':bars, 'daily':daily, 'dist14h':dist14h_w}
        print(f"  {label}: {len(bars)} bars 4H, {len(daily)} bars 1D (sintetizado)")

    # Build master + per-bar window lookup
    master = {}; bar_to_window = {}; bar_to_dist14h = {}
    for label, data in per_window_data.items():
        bars = data['bars']
        daily = data['daily']
        d14 = data['dist14h']
        for b in bars:
            ohlcv = b.get('ohlcv_last_40_bars') or []
            if not ohlcv: continue
            t = ohlcv[-1].get('time')
            if t is None or t in master: continue
            master[t] = b; bar_to_window[t] = label
            # Find daily idx for this bar
            di = None
            for i in range(len(daily)-1,-1,-1):
                if daily[i]['time'] <= t:
                    di = i; break
            if di is not None and di < len(d14):
                bar_to_dist14h[t] = d14[di]
    times_sorted = sorted(master.keys())
    bars_sorted = [master[t] for t in times_sorted]
    print(f"Master: {len(times_sorted)} bars 4H, {sum(1 for v in bar_to_dist14h.values() if v is not None)} com dist14h\n")

    # Pre-compute features per bar
    print("Computing features + outcomes...")
    bar_data = []
    for i, t in enumerate(times_sorted):
        b = bars_sorted[i]
        ohlcv = b.get('ohlcv_last_40_bars') or []
        close = ohlcv[-1].get('close') if ohlcv else None
        if close is None: continue
        atr = get_atr14(b)
        if not atr or atr<=0: continue
        if i+HORIZON_4H >= len(bars_sorted): continue
        next_close = (bars_sorted[i+HORIZON_4H].get('ohlcv_last_40_bars') or [{}])[-1].get('close')
        if next_close is None: continue
        r_long = (next_close - close) / atr
        # Pre-requisitos
        nas_l = has_nas_label_recent(b, "LONG", 5)
        if not nas_l: continue  # P1
        nas_dist = get_nas_dist(b)
        if nas_dist is None or nas_dist > -1: continue  # P3
        d14h = bar_to_dist14h.get(t)
        if d14h is None or d14h > -5: continue  # P2 (em região de fundo)
        # Triggers estruturais
        lux = get_lux_labels(b, max_delta=20)
        t1 = check_T1_exhaustion(lux)
        t2 = check_T2_reversal(lux)
        t3 = check_T3_continuation(lux)
        if not (t1 or t2 or t3): continue  # Pelo menos 1 trigger
        bar_data.append({
            'time':t,'window':bar_to_window[t],'r_long':round(r_long,2),
            'd14h':d14h,'nas_dist':nas_dist,
            't1':t1,'t2':t2,'t3':t3,
        })

    n_total = len(bar_data)
    print(f"  {n_total} triggers totais (pre-req + qualquer T1/T2/T3)\n")

    # Stats overall
    rs = [b['r_long'] for b in bar_data]
    s = stats_block(rs)
    if not s:
        print("Zero trades — algo está bloqueando triggers."); return 0

    print(f"=== OVERALL ===")
    print(f"  n={s['n']}  win%={s['win%']:.1f}  avg_R={s['avg_R']:+.2f}  median_R={s['median_R']:+.2f}  sum_R={s['sum_R']:+.2f}")
    valid = "VÁLIDA" if s['win%']>=WIN_GATE else "FALHA gate"
    print(f"  → {valid}")

    # Per-trigger breakdown
    print(f"\n=== POR TRIGGER ===")
    for t_name, key in [("T1 Exhaustion BEAR (BOS/CHoCH BEAR Δ≤2)", 't1'),
                        ("T2 Reversal CONFIRMED (Strong Low / CHoCH BULL)", 't2'),
                        ("T3 Continuation BULL (BOS BULL Δ≤5)", 't3')]:
        kept = [b for b in bar_data if b[key]]
        rs_t = [b['r_long'] for b in kept]
        s_t = stats_block(rs_t)
        if s_t:
            v = "VÁLIDA" if s_t['win%']>=WIN_GATE else "  -   "
            print(f"  {t_name:<55s}  n={s_t['n']:>4d}  win%={s_t['win%']:>5.1f}  avg_R={s_t['avg_R']:>+6.2f}  {v}")

    # T1+T2 (sem T3)
    t12 = [b for b in bar_data if b['t1'] or b['t2']]
    rs_12 = [b['r_long'] for b in t12]
    s_12 = stats_block(rs_12)
    if s_12:
        print(f"  T1+T2 (exhaustion+reversal sem continuation):       n={s_12['n']:>4d}  win%={s_12['win%']:>5.1f}  avg_R={s_12['avg_R']:>+6.2f}")

    # Per-window
    print(f"\n=== PER WINDOW ===")
    per_w = defaultdict(list)
    for b in bar_data: per_w[b['window']].append(b['r_long'])
    print(f"  {'window':<14s} {'n':>3s} {'win%':>5s} {'avg_R':>7s} {'sum_R':>8s}")
    wp = we = 0
    for wlabel, _ in WINDOWS_V5:
        rs_w = per_w.get(wlabel, [])
        s_w = stats_block(rs_w)
        if s_w:
            v = "✓" if s_w['n']>=10 and s_w['win%']>=WIN_GATE else " "
            print(f"  {wlabel:<14s} {s_w['n']:>3d} {s_w['win%']:>5.1f} {s_w['avg_R']:>+7.2f} {s_w['sum_R']:>+8.2f}  {v}")
            if s_w['n']>=10:
                we += 1
                if s_w['win%']>=WIN_GATE: wp += 1
        else:
            print(f"  {wlabel:<14s} {0:>3d}  -")
    print(f"  → windows passing: {wp}/{we}")

    # Recall vs dream
    print(f"\n=== RECALL vs 6 DREAM TRADES ===")
    dream_ts = [(int(datetime.strptime(dt+"+0000","%Y-%m-%d %H:%M%z").timestamp()), tid) for tid, dt in DREAM_LONG_DISCR]
    captured = []
    for d_ts, tid in dream_ts:
        for b in bar_data:
            if abs(b['time']-d_ts) <= TOLERANCE_SEC:
                trigger_info = []
                if b['t1']: trigger_info.append('T1')
                if b['t2']: trigger_info.append('T2')
                if b['t3']: trigger_info.append('T3')
                captured.append((tid, b['r_long'], '+'.join(trigger_info)))
                break
    captured_ids = set(c[0] for c in captured)
    print(f"  Capturados: {len(captured_ids)}/{len(dream_ts)}")
    for tid, dt_str in DREAM_LONG_DISCR:
        found = next((c for c in captured if c[0]==tid), None)
        if found:
            print(f"    ✓ {tid:<4s} ({dt_str})  R={found[1]:+.2f}  triggers={found[2]}")
        else:
            print(f"    · {tid:<4s} ({dt_str})  NOT CAPTURED")

    return 0


if __name__ == "__main__":
    sys.exit(main())
