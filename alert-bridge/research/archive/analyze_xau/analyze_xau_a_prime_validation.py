#!/usr/bin/env python3
"""
analyze_xau_a_prime_validation.py — Validar A' (V0+V3+V4) em N janelas históricas.

A' = IN_OB_ZONE + NAS_1to2 + dist_14d>-7% + slope_EMA50_1D_5d >= 0.5%/wk

Janelas:
  X2: 2024-01-19 → 2024-07 (uptrend forte H1 2024)
  X1: 2024-07-19 → 2024-12 (uptrend forte H2 2024, Fed pivot Sep 2024)
  OOS antigo: 2025-05-19 → 2025-09 (regime fraco — controle negativo)
  IS: 2025-11-19 → 2026-03 (uptrend forte Q4 2025-Q1 2026)

Daily 1D count=1500 pra cobrir todo o período.
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
    ("X2_2024H1",          "XAUUSD_240_2024-01-19_to_2026-05-20.jsonl"),
    ("X1_2024H2",          "XAUUSD_240_2024-07-19_to_2026-05-20.jsonl"),
    ("OOS_2025_May-Sep",   "XAUUSD_240_2025-05-19_to_2026-05-20.jsonl"),
    ("IS_2025Nov-2026Mar", "XAUUSD_240_2025-11-19_to_2026-05-19.jsonl"),
]
JSONL_DIR = BASE / "alert-bridge" / "logs" / "backtests"

HORIZON_4H = 10
DIST_THRESHOLD = -7.0
SLOPE_THRESHOLD = 0.5
WIN_GATE = 70.0


class MCP:
    def __init__(self): self.proc=None; self.id=0
    def start(self):
        self.proc = subprocess.Popen([NODE, str(MCP_SERVER)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
        self._raw("initialize", {"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"ap","version":"1.0"}})
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


def get_atr14(bar):
    ohlcv = bar.get('ohlcv_last_40_bars') or []
    if len(ohlcv)<=1: return None
    closed = ohlcv[:-1][-14:]
    r = [b['high']-b['low'] for b in closed if b.get('high') and b.get('low') and b['high']>b['low']]
    return mean(r) if r else None


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


def synth_daily_from_jsonl(bars):
    """Constrói série daily a partir dos OHLCV 4H sequenciais do JSONL.
    Cada bar JSONL[i].ohlcv_last_40_bars[-1] é o candle 4H[i]. Agregamos por dia UTC.
    """
    series_4h = []
    for b in bars:
        ohlcv = b.get('ohlcv_last_40_bars') or []
        if not ohlcv: continue
        last = ohlcv[-1]
        if last.get('time') is None: continue
        series_4h.append({
            'time': last['time'],
            'open': last.get('open'),
            'high': last.get('high'),
            'low': last.get('low'),
            'close': last.get('close'),
        })
    # Dedup por timestamp
    seen = {}
    for c in series_4h:
        seen[c['time']] = c
    series_4h = sorted(seen.values(), key=lambda x: x['time'])

    # Agregar por dia UTC
    by_day = {}
    for c in series_4h:
        if c['close'] is None: continue
        dt = datetime.fromtimestamp(c['time'], tz=timezone.utc)
        # Day key = midnight UTC do mesmo dia
        day_key = int(datetime(dt.year, dt.month, dt.day, tzinfo=timezone.utc).timestamp())
        if day_key not in by_day:
            by_day[day_key] = {'time': day_key, 'open': c['open'], 'high': c['high'], 'low': c['low'], 'close': c['close']}
        else:
            d = by_day[day_key]
            if c['high'] is not None and (d['high'] is None or c['high'] > d['high']): d['high'] = c['high']
            if c['low'] is not None and (d['low'] is None or c['low'] < d['low']): d['low'] = c['low']
            # close mais recente (ordem por time)
            d['close'] = c['close']
    daily = sorted(by_day.values(), key=lambda x: x['time'])
    return daily


def main():
    if not PAUSE.exists():
        print("ERRO: pause flag ausente.", file=sys.stderr); return 1

    print("=== VALIDAÇÃO A' (V0+V3+V4) EM 4 JANELAS XAU 4H ===\n")

    # Tenta fetch daily REAL do TV (cobertura pode ser limitada por scroll do usuário)
    print("Tentando capturar daily REAL do TV (sem switch — confia no chart atual em XAU 1D)...")
    client = MCP(); client.start()
    daily_real = []
    try:
        st = client.call("chart_get_state")
        if st.get("symbol","").endswith("XAUUSD") and st.get("resolution") in ("1D","D"):
            resp = client.call("data_get_ohlcv", {"count": 1500, "summary": False})
            bars_d = resp.get("last_5_bars") or resp.get("bars") or []
            daily_real = sorted([b for b in bars_d if b.get("time")], key=lambda x: x["time"])
            if daily_real:
                print(f"  daily real: {len(daily_real)} bars ({datetime.fromtimestamp(daily_real[0]['time'],tz=timezone.utc):%Y-%m-%d} → {datetime.fromtimestamp(daily_real[-1]['time'],tz=timezone.utc):%Y-%m-%d})")
        else:
            print(f"  chart NÃO em XAU 1D ({st.get('symbol')} {st.get('resolution')}) — usando só sintetizado")
    finally:
        client.stop()

    real_first_ts = daily_real[0]['time'] if daily_real else None
    real_last_ts = daily_real[-1]['time'] if daily_real else None

    all_trades_by_window = {}
    all_trades_pool = []

    for label, fname in WINDOWS:
        path = JSONL_DIR / fname
        print(f"\n[{label}] {fname}")
        if not path.exists():
            print(f"  NÃO encontrado"); continue
        bars = load_bars(path)
        if not bars:
            print(f"  vazio"); continue
        first_t = (bars[0].get('ohlcv_last_40_bars') or [{}])[-1].get('time')
        last_t = (bars[-1].get('ohlcv_last_40_bars') or [{}])[-1].get('time')
        if first_t and last_t:
            print(f"  {len(bars)} bars 4H | range: {datetime.fromtimestamp(first_t,tz=timezone.utc):%Y-%m-%d} → {datetime.fromtimestamp(last_t,tz=timezone.utc):%Y-%m-%d}")

        # Decidir: usar daily REAL ou SINTETIZADO?
        # Daily real só vale se cobre o início da janela com folga de 60 dias (warmup EMA50)
        WARMUP_SECONDS = 60 * 86400
        if (daily_real and real_first_ts is not None and first_t is not None
            and real_first_ts <= first_t - WARMUP_SECONDS):
            daily = daily_real
            daily_source = f"REAL ({len(daily_real)} bars, cobre warmup)"
        else:
            daily = synth_daily_from_jsonl(bars)
            daily_source = f"SINTETIZADO local ({len(daily)} bars — warmup truncado)"
        if len(daily) < 55:
            print(f"  daily: {daily_source} — insuficiente para EMA50+slope")
            continue
        print(f"  daily: {daily_source}")

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

        def find_di(ts):
            for i in range(len(daily)-1, -1, -1):
                if daily[i]["time"] <= ts: return i
            return None

        trades_v0v3 = []
        trades_aprime = []
        cut_by_v4_only = []  # passou V0+V3 mas reprovado em V4
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
            slope = slope50[di] if di is not None and di < len(slope50) else None
            # V0 + V3
            if not (st['in_ob'] and st['nas_bucket']=='NAS_1to2'): continue
            if dist is None or dist <= DIST_THRESHOLD: continue
            t = {
                'window': label,
                'entry_time': st['entry_time'],
                'entry_dt': datetime.fromtimestamp(st['entry_time'],tz=timezone.utc).strftime('%Y-%m-%d %H:%M') if st['entry_time'] else '?',
                'R': round(close_R, 2),
                'dist_14d': dist,
                'slope50_5d': slope,
            }
            trades_v0v3.append(t)
            # V4
            if slope is not None and slope >= SLOPE_THRESHOLD:
                trades_aprime.append(t)
            else:
                cut_by_v4_only.append(t)

        rs_v0v3 = [t['R'] for t in trades_v0v3]
        rs_aprime = [t['R'] for t in trades_aprime]
        rs_cut = [t['R'] for t in cut_by_v4_only]
        s_v0v3 = stats_block(rs_v0v3)
        s_aprime = stats_block(rs_aprime)
        s_cut = stats_block(rs_cut)

        def show(name, s):
            if not s:
                print(f"    {name:<14s}: n=0")
                return
            valid = "VÁLIDA" if s['win%'] >= WIN_GATE else "FALHA gate"
            print(f"    {name:<14s}: n={s['n']:>3d}  win%={s['win%']:>5.1f}  avg_R={s['avg_R']:>+6.2f}  med_R={s['median_R']:>+6.2f}  sum_R={s['sum_R']:>+6.2f}  {valid}")
        show("V0+V3 (base)", s_v0v3)
        show("A' (+V4)", s_aprime)
        show("Cortados V4", s_cut)
        all_trades_by_window[label] = trades_aprime
        all_trades_pool.extend(trades_aprime)

    # Combined
    print("\n" + "="*120)
    print("COMBINED — A' através das 4 janelas")
    print("="*120)
    rs = [t['R'] for t in all_trades_pool]
    s = stats_block(rs)
    if s:
        print(f"  n={s['n']}  win%={s['win%']:.1f}  avg_R={s['avg_R']:+.2f}  median_R={s['median_R']:+.2f}  min={s['min_R']:+.2f}  max={s['max_R']:+.2f}  std={s['std_R']:.2f}  sum_R={s['sum_R']:+.2f}")
        if s['n'] >= 100:
            print("  → SÓLIDO (n>=100)")
        elif s['n'] >= 50:
            print("  → PRELIMINAR FORTE (n>=50)")
        elif s['n'] >= 30:
            print("  → PRELIMINAR (n>=30)")
        else:
            print("  → INTERIM (n<30)")
        valid = "VÁLIDA" if s['win%'] >= WIN_GATE else "FALHA gate"
        print(f"  → {valid} (gate {WIN_GATE}%)")

    # Por mês — combined
    if all_trades_pool:
        print("\nTrades A' por mês (combined):")
        from collections import defaultdict
        bm = defaultdict(list)
        for t in all_trades_pool:
            bm[t['entry_dt'][:7]].append(t)
        for ym in sorted(bm.keys()):
            ts = bm[ym]
            r = [x['R'] for x in ts]
            wins = sum(1 for x in r if x>0)
            print(f"  {ym}: n={len(ts):>2d}  win%={100*wins/len(ts):>5.1f}  sum_R={sum(r):>+6.2f}")

    # Lista completa por janela
    print("\nTodos os trades A' (por janela):")
    for label, _ in WINDOWS:
        ts = all_trades_by_window.get(label, [])
        if not ts: continue
        print(f"\n  [{label}] {len(ts)} trades:")
        for t in sorted(ts, key=lambda x: x['entry_time'] or 0):
            flag = "WIN " if t['R']>0 else "LOSS"
            slope_s = f"{t['slope50_5d']:+.2f}%" if t['slope50_5d'] is not None else "?"
            print(f"    {t['entry_dt']}  R={t['R']:+6.2f}  slope={slope_s}  dist={t['dist_14d']:+.1f}%  {flag}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
