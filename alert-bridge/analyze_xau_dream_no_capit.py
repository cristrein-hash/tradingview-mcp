#!/usr/bin/env python3
"""
analyze_xau_dream_no_capit.py — Investigar 5 dream LONG trades fora do CAPITULATION.

Os 5 dream trades NÃO capturados por REVERSAL_CAPITULATION (todos têm NAS LONG
mas falham em RSI<50 ou ATR_high):

  #1   2026-05-04 15:00  — ATR_rel=0.65 (baixa volat)
  #8   2026-03-20 14:00  — ATR_rel=0.87 (baixa volat)
  #10  2026-03-24 10:00  — ATR_rel=0.97 (baixa volat)
  #11  2026-01-29 19:00  — NAS_LONG false + RSI 85.6 (regime forte)
  #13  2026-02-03 03:00  — RSI 56.1 (regime acima média)

Investigar TODAS as features disponíveis pra esses 5 vs base do CAPITULATION
pra identificar padrão estrutural alternativo.
"""
from pathlib import Path
from datetime import datetime, timezone
from statistics import mean
import json, sys, subprocess, time

BASE = Path(__file__).parent.parent
JSONL_DIR = BASE / "alert-bridge" / "logs" / "backtests"
MCP_SERVER = BASE / "src" / "server.js"
NODE = "/opt/homebrew/bin/node"

WINDOWS_V3 = [
    "XAUUSD_240_2023-01-19_to_2026-05-20_v3.jsonl",
    "XAUUSD_240_2023-07-19_to_2026-05-20_v3.jsonl",
    "XAUUSD_240_2024-01-19_to_2026-05-20_v3.jsonl",
    "XAUUSD_240_2024-07-19_to_2026-05-20_v3.jsonl",
    "XAUUSD_240_2025-05-19_to_2026-05-20_v3.jsonl",
    "XAUUSD_240_2025-09-15_to_2026-05-20_v3.jsonl",
    "XAUUSD_240_2025-11-19_to_2026-05-20_v3.jsonl",
    "XAUUSD_240_2026-03-19_to_2026-05-20_v3.jsonl",
]

DREAM_NO_CAPIT = [
    ("#1",  "2026-05-04 15:00"),
    ("#8",  "2026-03-20 14:00"),
    ("#10", "2026-03-24 10:00"),
    ("#11", "2026-01-29 19:00"),
    ("#13", "2026-02-03 03:00"),
]
DREAM_CAPTURED = [
    ("#5",  "2025-11-05 11:00"),  # capturada pelo CAPITULATION — pra comparação
]
DREAM_TOLERANCE_SEC = 7200

COLOR_BULL = 2572201804
COLOR_BEAR = 2566953215
SELL_PLOTS = {"plot_0", "plot_10"}
BUY_PLOTS = {"plot_2", "plot_4", "plot_6", "plot_8"}
BAR_SECONDS_4H = 14400


class MCP:
    def __init__(self): self.proc=None; self.id=0
    def start(self):
        self.proc = subprocess.Popen([NODE, str(MCP_SERVER)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
        self._raw("initialize",{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"dn","version":"1.0"}})
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
        deadline=time.monotonic()+t
        while time.monotonic()<deadline:
            line=self.proc.stdout.readline()
            if not line: raise RuntimeError("closed")
            try:
                r=json.loads(line)
                if r.get("id")==self.id: return r
            except: continue
        return None
    def call(self, n, a=None, t=60):
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


def rsi_series(closes, period=14):
    if len(closes)<period+1: return [None]*len(closes)
    g,l=[],[]
    for i in range(1,len(closes)):
        d=closes[i]-closes[i-1]; g.append(max(d,0)); l.append(max(-d,0))
    ag=mean(g[:period]); al=mean(l[:period])
    out=[None]*period
    out.append(100 if al==0 else 100-(100/(1+ag/al)))
    for i in range(period, len(closes)-1):
        ag = (ag*(period-1)+g[i])/period
        al = (al*(period-1)+l[i])/period
        out.append(100 if al==0 else 100-(100/(1+ag/al)))
    return out


def main():
    print("=== DEEP DIVE — 5 dream LONG sem capitulação ===\n")

    # Fetch daily
    print("Fetching daily 2000 bars...")
    client = MCP(); client.start()
    try:
        resp = client.call("data_get_ohlcv", {"count":2000,"summary":False})
        bars_d = resp.get("last_5_bars") or resp.get("bars") or []
        daily = sorted([b for b in bars_d if b.get("time")], key=lambda x: x["time"])
        print(f"  {len(daily)} bars 1D")
    finally:
        client.stop()

    closes_d = [b['close'] for b in daily]
    highs_d = [b['high'] for b in daily]
    lows_d = [b['low'] for b in daily]
    rsi_d = rsi_series(closes_d, 14)
    # ATR 14
    trs = [highs_d[0]-lows_d[0]]
    for i in range(1, len(daily)):
        trs.append(max(highs_d[i]-lows_d[i], abs(highs_d[i]-closes_d[i-1]), abs(lows_d[i]-closes_d[i-1])))
    atr14 = [None]*len(daily)
    for i in range(14, len(daily)):
        atr14[i] = mean(trs[i-14:i])
    # dist 14d low
    dist14l = [None]*len(daily)
    for i in range(len(daily)):
        win = lows_d[max(0,i-13):i+1]
        dist14l[i] = (closes_d[i]-min(win))/min(win)*100
    dist14h = [None]*len(daily)
    for i in range(len(daily)):
        win = highs_d[max(0,i-13):i+1]
        dist14h[i] = (closes_d[i]-max(win))/max(win)*100
    dist30h = [None]*len(daily)
    for i in range(len(daily)):
        win = highs_d[max(0,i-29):i+1]
        dist30h[i] = (closes_d[i]-max(win))/max(win)*100

    def find_di(ts):
        for i in range(len(daily)-1,-1,-1):
            if daily[i]['time']<=ts: return i
        return None

    # Load 4H
    master = {}
    for fname in WINDOWS_V3:
        path = JSONL_DIR / fname
        if not path.exists(): continue
        for b in load_bars(path):
            ohlcv = b.get('ohlcv_last_40_bars') or []
            if not ohlcv: continue
            t = ohlcv[-1].get('time')
            if t is None or t in master: continue
            master[t] = b

    print(f"Master 4H: {len(master)} bars\n")

    def find_bar(target_ts):
        best_t = None; best_d = None
        for t in master.keys():
            d = abs(t-target_ts)
            if d <= DREAM_TOLERANCE_SEC and (best_d is None or d<best_d):
                best_d = d; best_t = t
        return best_t

    def analyze(tid, dt_str, group):
        target_ts = int(datetime.strptime(dt_str+"+0000","%Y-%m-%d %H:%M%z").timestamp())
        bar_t = find_bar(target_ts)
        if bar_t is None:
            print(f"\n[{group}] {tid} {dt_str} BAR NOT FOUND"); return
        b = master[bar_t]
        ohlcv = b.get('ohlcv_last_40_bars') or []
        close = ohlcv[-1].get('close')
        # 1D
        di = find_di(bar_t)
        rsi_now = rsi_d[di] if di and di<len(rsi_d) else None
        d14l = dist14l[di] if di else None
        d14h = dist14h[di] if di else None
        d30h = dist30h[di] if di else None
        # NAS labels recentes
        nas_label_status = []
        nas_dist = None
        for s in (b.get('pine_labels') or []):
            if 'NAS' not in s.get('name','').upper(): continue
            labels = s.get('labels') or []
            xs = [l.get('x') for l in labels if l.get('x') is not None]
            if not xs: break
            max_x = max(xs)
            for l in labels:
                lx = l.get('x'); txt = l.get('text','')
                if lx is None: continue
                delta = max_x - lx
                if 0 <= delta <= 10:
                    nas_label_status.append((delta, txt))
            break
        nas_label_status.sort()
        # NAS_DIST atual
        for s in (b.get('study_values') or []):
            if 'NAS' in s.get('name',''):
                try: nas_dist = float(s.get('values',{}).get('NAS_DISTANCE_FROM_EMA_ATR','').replace('−','-'))
                except: pass
                break
        # OB demand
        ob_info = []
        for s in (b.get('pine_boxes') or []):
            if 'Custom OB' not in s.get('name',''): continue
            for box in (s.get('all_boxes') or []):
                hi, lo = box.get('high'), box.get('low')
                bc = box.get('borderColor')
                if hi is None or lo is None or close is None: continue
                bull = bc == COLOR_BULL
                size = hi - lo
                if size <= 0: continue
                if lo <= close <= hi:
                    ob_info.append(f"IN_{'bull' if bull else 'bear'}[{lo:.0f}-{hi:.0f}]")
                else:
                    dist = max((close-hi) if close>hi else 0, (lo-close) if close<lo else 0)
                    if dist <= size:  # within zone-width
                        pct = dist/size*100
                        ob_info.append(f"near{int(pct)}%_{'bull' if bull else 'bear'}[{lo:.0f}-{hi:.0f}]")
        # Bubbles janela 20 (mais largo)
        bub_sells = []
        bub_buys = []
        if bar_t:
            t_lb = bar_t - 19*BAR_SECONDS_4H
            for s in (b.get('pine_shapes_bubbles') or []):
                if 'Bubbles' not in s.get('name',''): continue
                for act in s.get('activations', []):
                    t = act.get('time')
                    if t is None: continue
                    if t_lb <= t <= bar_t:
                        for p in (act.get('shapes') or {}):
                            delta = (bar_t-t)//BAR_SECONDS_4H
                            if p in SELL_PLOTS: bub_sells.append((delta, p))
                            elif p in BUY_PLOTS: bub_buys.append((delta, p))
        # Price action atual
        cur = ohlcv[-1]
        body_pct = abs(cur['close']-cur['open'])/(cur['high']-cur['low'])*100 if cur['high']>cur['low'] else 0
        # Sweep low?
        if len(ohlcv)>=6:
            prev5 = ohlcv[-6:-1]
            min_prev5 = min(b['low'] for b in prev5)
            is_sweep = cur['low'] < min_prev5
        else:
            is_sweep = False

        # Output
        bar_dt = datetime.fromtimestamp(bar_t, tz=timezone.utc).strftime('%Y-%m-%d %H:%M')
        def f(v, fmt='+.1f'):
            return format(v, fmt) if v is not None else '?'
        print(f"\n══ [{group}] {tid} {dt_str} (bar {bar_dt}) ══")
        print(f"  1D: RSI={f(rsi_now,'.1f')}  dist14d_low={f(d14l)}%  dist14d_high={f(d14h)}%  dist30d_high={f(d30h)}%")
        print(f"  4H: NAS_DIST={f(nas_dist,'+.2f')}  body={body_pct:.0f}%  sweep_low={is_sweep}")
        print(f"  NAS labels últimos 10b: {nas_label_status}")
        print(f"  OB context: {ob_info[:4] if ob_info else 'NO OB'}")
        print(f"  Bub Sells 20b: {bub_sells[-10:]}")
        print(f"  Bub Buys 20b: {bub_buys[-10:]}")

    print("\n############ DREAM NÃO CAPITULATION ############")
    for tid, dt_str in DREAM_NO_CAPIT:
        analyze(tid, dt_str, "NO_CAPIT")

    print("\n\n############ DREAM CAPTURADA POR CAPITULATION (#5) ############")
    for tid, dt_str in DREAM_CAPTURED:
        analyze(tid, dt_str, "CAPIT")

    return 0


if __name__ == "__main__":
    sys.exit(main())
