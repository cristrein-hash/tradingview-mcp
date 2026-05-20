#!/usr/bin/env python3
"""
analyze_xau_cluster_aug2024.py — Diagnóstico do cluster 2024-08-29 (4 losers B').

Comparar features dos 4 LOSERS de 29/08 com WINNERS adjacentes em agosto/setembro 2024.

Hipótese WebSearch: 29/08 era 1 dia antes do PCE inflation data release (30/08) —
mercado em wait-and-see pré-evento.

Buscar feature quantitativa que diferencie esses 4 do resto.
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

JSONL = BASE / "alert-bridge" / "logs" / "backtests" / "XAUUSD_240_2024-07-19_to_2026-05-20.jsonl"

HORIZON_4H = 10
SELL_PLOTS = {"plot_0", "plot_10"}
BUY_PLOTS = {"plot_2", "plot_4", "plot_6", "plot_8"}
BAR_SECONDS_4H = 14400

# Trades B' em agosto-setembro 2024 (do output anterior)
TARGETS = [
    ("2024-08-12 06:00", +3.05, "WIN_clean"),
    ("2024-08-16 02:00", +3.37, "WIN_clean"),
    ("2024-08-16 10:00", +2.79, "WIN_clean"),
    ("2024-08-26 06:00", +1.35, "WIN_BS3"),
    ("2024-08-29 06:00", -1.45, "LOSS_BS3"),  # cluster
    ("2024-08-29 10:00", -2.29, "LOSS_BS3"),  # cluster
    ("2024-08-29 14:00", -1.70, "LOSS_BS3"),  # cluster
    ("2024-08-29 18:00", -2.25, "LOSS_BS3"),  # cluster
    ("2024-09-11 02:00", +3.85, "WIN_BS3"),
    ("2024-09-11 06:00", +4.07, "WIN_BS5"),
    ("2024-09-11 10:00", +4.27, "WIN_BS5"),
]


class MCP:
    def __init__(self): self.proc=None; self.id=0
    def start(self):
        self.proc = subprocess.Popen([NODE, str(MCP_SERVER)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
        self._raw("initialize", {"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"c","version":"1.0"}})
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
    return {'rsi':rsi,'nas':nas,'close':close,'entry_time':entry_time}


def get_atr_4h(bar):
    ohlcv = bar.get('ohlcv_last_40_bars') or []
    if len(ohlcv)<=1: return None
    closed = ohlcv[:-1][-14:]
    r = [b['high']-b['low'] for b in closed if b.get('high') and b.get('low') and b['high']>b['low']]
    return mean(r) if r else None


def get_range_compression(bar):
    """Volatilidade últimos 5 bars vs ATR14. Razão < 1 = compressão."""
    ohlcv = bar.get('ohlcv_last_40_bars') or []
    if len(ohlcv) < 6: return None
    last5 = ohlcv[-5:]
    rng5 = [b['high']-b['low'] for b in last5 if b.get('high') and b.get('low')]
    if not rng5: return None
    atr14 = get_atr_4h(bar)
    if not atr14 or atr14 <= 0: return None
    return mean(rng5) / atr14


def get_price_change(bar, lookback=5):
    """% change últimos N bars."""
    ohlcv = bar.get('ohlcv_last_40_bars') or []
    if len(ohlcv) < lookback+1: return None
    close_now = ohlcv[-1].get('close')
    close_ago = ohlcv[-(lookback+1)].get('close')
    if close_now is None or close_ago is None or close_ago <= 0: return None
    return (close_now - close_ago) / close_ago * 100


def bubble_features(bar, entry_time):
    feats = {'BS_3':False,'BS_5':False,'BS_10':False,'BB_now':False,'BS_now':False}
    if entry_time is None: return feats
    t_3 = entry_time - 2*BAR_SECONDS_4H
    t_5 = entry_time - 4*BAR_SECONDS_4H
    t_10 = entry_time - 9*BAR_SECONDS_4H
    for s in (bar.get('pine_shapes_bubbles') or []):
        if 'Bubbles' not in s.get('name',''): continue
        for act in s.get('activations', []):
            t = act.get('time')
            if t is None: continue
            sh = act.get('shapes') or {}
            if t == entry_time:
                if set(sh.keys()) & BUY_PLOTS: feats['BB_now'] = True
                if set(sh.keys()) & SELL_PLOTS: feats['BS_now'] = True
            if t_3 <= t <= entry_time and set(sh.keys()) & SELL_PLOTS:
                feats['BS_3'] = True
            if t_5 <= t <= entry_time and set(sh.keys()) & SELL_PLOTS:
                feats['BS_5'] = True
            if t_10 <= t <= entry_time and set(sh.keys()) & SELL_PLOTS:
                feats['BS_10'] = True
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


def main():
    if not PAUSE.exists():
        print("ERRO: pause flag ausente.", file=sys.stderr); return 1

    print("=== DIAGNÓSTICO CLUSTER 2024-08-29 (4 losers consecutivos) ===\n")
    print("Contexto WebSearch: 29/08 era 1 dia antes do PCE inflation data release (30/08)")
    print("Powell Jackson Hole (22/08): dovish — Gold ATH $2531 em 20/08, depois consolidação\n")

    print("Captura daily 1D (count=2000)...")
    client = MCP(); client.start()
    try:
        resp = client.call("data_get_ohlcv", {"count": 2000, "summary": False})
        bars_d = resp.get("last_5_bars") or resp.get("bars") or []
        daily = sorted([b for b in bars_d if b.get("time")], key=lambda x: x["time"])
    finally:
        client.stop()
    closes_d = [b["close"] for b in daily]
    highs_d = [b["high"] for b in daily]
    lows_d = [b["low"] for b in daily]
    ema50_d = ema(closes_d, 50)
    # ATR daily
    trs=[daily[0]['high']-daily[0]['low']]
    for i in range(1,len(daily)):
        trs.append(max(daily[i]['high']-daily[i]['low'], abs(daily[i]['high']-closes_d[i-1]), abs(daily[i]['low']-closes_d[i-1])))
    atr14_d=[None]*len(daily)
    for i in range(14,len(daily)):
        atr14_d[i] = mean(trs[i-14:i])
    dist14_d=[None]*len(daily)
    for i in range(len(daily)):
        win_hi = max(highs_d[max(0,i-13):i+1])
        dist14_d[i] = (closes_d[i]-win_hi)/win_hi*100
    slope50=[None]*len(daily)
    for i in range(55,len(daily)):
        if ema50_d[i] and ema50_d[i-5] and ema50_d[i-5]>0:
            slope50[i] = (ema50_d[i]-ema50_d[i-5])/ema50_d[i-5]*100
    cve=[None]*len(daily)
    for i in range(len(daily)):
        if ema50_d[i] and ema50_d[i]>0:
            cve[i] = (closes_d[i]-ema50_d[i])/ema50_d[i]*100

    def find_di(ts):
        for i in range(len(daily)-1,-1,-1):
            if daily[i]['time']<=ts: return i
        return None

    bars_4h = load_bars(JSONL)

    bars_by_time = {}
    for b in bars_4h:
        st = get_state_4h(b)
        if st['entry_time']:
            bars_by_time[st['entry_time']] = b

    def find_bar(target_dt_str):
        target_ts = int(datetime.strptime(target_dt_str+"+0000", "%Y-%m-%d %H:%M%z").timestamp())
        best=None; best_delta=None
        for ts, b in bars_by_time.items():
            if ts <= target_ts:
                delta = target_ts-ts
                if best_delta is None or delta < best_delta:
                    best_delta=delta; best=(ts,b)
        return best

    print(f"{'trade':<22s} {'R':>6s} {'tag':<14s} {'rsi':>5s} {'atr4h':>6s} {'range/atr':>10s} {'chg5':>7s} {'chg20':>7s} {'cve':>6s} {'slope':>6s} {'distd':>6s} {'BS3':>4s}")
    print("-"*130)
    rows = []
    for dt_s, r, tag in TARGETS:
        found = find_bar(dt_s)
        if not found:
            print(f"  {dt_s:<22s} NOT FOUND"); continue
        ts, b = found
        st = get_state_4h(b)
        atr4 = get_atr_4h(b)
        rng_ratio = get_range_compression(b)
        chg5 = get_price_change(b, lookback=5)
        chg20 = get_price_change(b, lookback=20)
        di = find_di(ts)
        cve_v = cve[di] if di is not None else None
        slp = slope50[di] if di is not None else None
        distd = dist14_d[di] if di is not None else None
        bf = bubble_features(b, ts)
        rows.append({'dt':dt_s,'R':r,'tag':tag,'rsi':st['rsi'],'atr4':atr4,'rng_ratio':rng_ratio,
                     'chg5':chg5,'chg20':chg20,'cve':cve_v,'slope':slp,'distd':distd,
                     'BS3':bf['BS_3']})
        def f(v,fmt="+.2f"):
            if v is None: return "?".rjust(6)
            return format(v, fmt)
        print(f"  {dt_s:<22s} {r:+6.2f} {tag:<14s} {f(st['rsi'],'5.1f'):>5s} {f(atr4,'6.2f'):>6s} {f(rng_ratio,'10.2f'):>10s} {f(chg5,'+7.2f')+'%':>7s} {f(chg20,'+7.2f')+'%':>7s} {f(cve_v,'+6.1f')+'%':>6s} {f(slp,'+6.2f')+'%':>6s} {f(distd,'+6.2f')+'%':>6s} {('YES' if bf['BS_3'] else 'no'):>4s}")

    # Compare: 4 losers vs 7 winners
    losers = [r for r in rows if r['R']<0]
    winners = [r for r in rows if r['R']>0]
    print(f"\n=== AGREGADOS ===")
    print(f"{'feature':<14s} {'losers (n=4)':>15s} {'winners (n=7)':>16s} {'diff':>8s}")
    for k in ['rsi','atr4','rng_ratio','chg5','chg20','cve','slope','distd']:
        lv = [r[k] for r in losers if r[k] is not None]
        wv = [r[k] for r in winners if r[k] is not None]
        if not lv or not wv: continue
        lm, wm = mean(lv), mean(wv)
        diff = lm-wm
        print(f"  {k:<12s} {lm:>+15.2f} {wm:>+16.2f} {diff:>+8.2f}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
