#!/usr/bin/env python3
"""
analyze_xau_regime_macro.py — Etapa 1: descobrir critério de regime macro em TF Diário
que melhor separa winners de losers do backtest V0 (IN_OB_ZONE + NAS:1to2).

Passos:
1. Captura OHLCV diário XAU (~300 bars = ~12 meses) via MCP standalone
2. Carrega backtest V0 (43 trades) do JSONL existente
3. Pra cada trade 4H, mapeia para o bar diário do mesmo dia (ou anterior)
4. Calcula no diário:
   - EMA50
   - distance from 14d high (%)
   - slope EMA50 (subindo / lateral / descendo)
5. Bucketiza trades em regimes
6. Win rate / avg_R por bucket
7. Identifica critério mais discriminante

Pré-requisitos:
- touch /tmp/claude_recheck.paused
- daemons pausados

Uso:
    python3 analyze_xau_regime_macro.py
"""
from pathlib import Path
from datetime import datetime, timezone
from statistics import mean, median
import json, subprocess, sys, time

BASE_DIR = Path(__file__).parent.parent
MCP_SERVER = BASE_DIR / "src" / "server.js"
NODE = "/opt/homebrew/bin/node"
BACKTEST_JSONL = BASE_DIR / "alert-bridge" / "logs" / "backtests" / "XAUUSD_240_2025-11-19_to_2026-05-19.jsonl"
PAUSE_FLAG = Path("/tmp/claude_recheck.paused")

SYMBOL = "PEPPERSTONE:XAUUSD"
DAILY_TF = "D"
DAILY_BARS_NEEDED = 300  # ~12 meses
HORIZON_4H = 10  # mesmo do V0


class MCP:
    def __init__(self):
        self.proc = None; self.id = 0
    def start(self):
        self.proc = subprocess.Popen([NODE, str(MCP_SERVER)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, bufsize=1)
        self._raw("initialize", {"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"regime","version":"1.0"}})
        self.proc.stdin.write(json.dumps({"jsonrpc":"2.0","method":"notifications/initialized","params":{}})+"\n"); self.proc.stdin.flush()
    def stop(self):
        if self.proc:
            try: self.proc.stdin.close()
            except: pass
            try: self.proc.terminate(); self.proc.wait(timeout=5)
            except: self.proc.kill()
    def _raw(self, method, params, t=60):
        self.id += 1
        msg = {"jsonrpc":"2.0","id":self.id,"method":method,"params":params}
        self.proc.stdin.write(json.dumps(msg)+"\n"); self.proc.stdin.flush()
        deadline = time.monotonic() + t
        while time.monotonic() < deadline:
            line = self.proc.stdout.readline()
            if not line: raise RuntimeError("closed stdout")
            try:
                r = json.loads(line)
                if r.get("id") == self.id: return r
            except: continue
        raise TimeoutError(method)
    def call(self, name, args=None, t=60):
        r = self._raw("tools/call", {"name":name, "arguments": args or {}}, t)
        if "error" in r: return {"_error": r["error"]}
        c = r.get("result",{}).get("content",[])
        if c and c[0].get("type")=="text":
            try: return json.loads(c[0]["text"])
            except: return {"_raw": c[0]["text"]}
        return r.get("result",{})


def ema(values, period):
    if not values or len(values) < period: return [None]*len(values)
    k = 2 / (period + 1)
    out = [None]*(period-1)
    out.append(sum(values[:period])/period)
    for v in values[period:]:
        out.append(v * k + out[-1] * (1-k))
    return out


def main():
    if not PAUSE_FLAG.exists():
        print(f"ERRO: pause flag ausente. touch {PAUSE_FLAG}", file=sys.stderr)
        return 1

    print("=== ETAPA 1: regime macro XAU 1D ===\n")
    client = MCP()
    print("Spawnando MCP server...")
    client.start()

    state = client.call("chart_get_state")
    orig_sym = state.get("symbol")
    orig_tf = state.get("resolution")
    print(f"  chart original: {orig_sym} {orig_tf}")

    try:
        print(f"\nCapturar OHLCV diário ({DAILY_BARS_NEEDED} bars)...")
        client.call("chart_set_symbol", {"symbol": SYMBOL}); time.sleep(1)
        client.call("chart_set_timeframe", {"timeframe": DAILY_TF}); time.sleep(2)
        ohlcv_resp = client.call("data_get_ohlcv", {"count": DAILY_BARS_NEEDED, "summary": False})
        # ohlcv resp pode vir em "last_5_bars" ou "bars"
        daily_bars = ohlcv_resp.get("last_5_bars") or ohlcv_resp.get("bars") or []
        if not daily_bars:
            print(f"  ERRO: sem dados OHLCV. Resp: {ohlcv_resp}")
            return 1
        # Ordenar por tempo crescente garantia
        daily_bars = sorted([b for b in daily_bars if b.get("time")], key=lambda x: x["time"])
        print(f"  {len(daily_bars)} bars diários capturados")
        print(f"  período: {datetime.fromtimestamp(daily_bars[0]['time'], tz=timezone.utc).date()} → {datetime.fromtimestamp(daily_bars[-1]['time'], tz=timezone.utc).date()}")

    finally:
        if orig_sym:
            client.call("chart_set_symbol", {"symbol": orig_sym})
            if orig_tf: client.call("chart_set_timeframe", {"timeframe": orig_tf})
        client.stop()
        print("MCP stopped.\n")

    # === Análise post-hoc ===
    print("Carregando backtest V0...")
    bars_4h = []
    with BACKTEST_JSONL.open() as f:
        for line in f:
            try: bars_4h.append(json.loads(line))
            except: pass
    # truncate corruption
    for i, b in enumerate(bars_4h):
        if not (b.get('ohlcv_last_40_bars') or []):
            bars_4h = bars_4h[:i]; break
    print(f"  {len(bars_4h)} bars 4H válidos")

    # Calcular EMA50 + 14d high no diário
    closes_d = [b["close"] for b in daily_bars]
    highs_d  = [b["high"]  for b in daily_bars]
    ema50_d  = ema(closes_d, 50)

    # Pra cada bar diário, distance from max(highs[-14:]) trailing
    dist_from_14d_high = [None]*len(daily_bars)
    for i in range(len(daily_bars)):
        start = max(0, i-13)
        window_highs = highs_d[start:i+1]
        max_h = max(window_highs)
        dist_from_14d_high[i] = (daily_bars[i]["close"] - max_h) / max_h * 100  # % vs high (negativo)

    # Slope EMA50 (subindo se ema_now > ema_5_ago)
    slope_d = [None]*len(daily_bars)
    for i in range(5, len(daily_bars)):
        if ema50_d[i] is not None and ema50_d[i-5] is not None:
            slope_d[i] = "up" if ema50_d[i] > ema50_d[i-5] else ("flat" if abs(ema50_d[i]-ema50_d[i-5])/ema50_d[i-5]<0.005 else "down")

    # Reconstruir os 43 trades V0 — replicar lógica do analyze
    def get_state_bar(bar):
        rsi=nas=None
        for s in (bar.get('study_values') or []):
            if 'Relative Strength' in s.get('name',''):
                try: rsi = float(s.get('values',{}).get('RSI','').replace('−','-'))
                except: pass
            if 'NAS' in s.get('name',''):
                try: nas = float(s.get('values',{}).get('NAS_DISTANCE_FROM_EMA_ATR','').replace('−','-'))
                except: pass
        nas_b = None
        if nas is not None:
            if nas < -2: nas_b='NAS<-2'
            elif nas < -1: nas_b='NAS_-2to-1'
            elif nas < 1: nas_b='NAS_-1to1'
            elif nas < 2: nas_b='NAS_1to2'
            else: nas_b='NAS>2'
        ohlcv = bar.get('ohlcv_last_40_bars') or []
        close = ohlcv[-1].get('close') if ohlcv else None
        in_ob=False
        for s in (bar.get('pine_boxes') or []):
            if 'Custom OB' in s.get('name',''):
                for z in s.get('zones', []):
                    hi,lo = z.get('high'), z.get('low')
                    if hi is not None and lo is not None and close is not None and lo <= close <= hi:
                        in_ob=True; break
                break
        return {'rsi':rsi,'nas_bucket':nas_b,'in_ob':in_ob,'close':close,'entry_time': ohlcv[-1].get('time') if ohlcv else None}

    def get_atr14(bar):
        ohlcv = bar.get('ohlcv_last_40_bars') or []
        if len(ohlcv)<=1: return None
        closed = ohlcv[:-1][-14:]
        r = [b['high']-b['low'] for b in closed if b.get('high') and b.get('low') and b['high']>b['low']]
        return mean(r) if r else None

    trades = []
    for i, b in enumerate(bars_4h):
        st = get_state_bar(b)
        if not (st['in_ob'] and st['nas_bucket']=='NAS_1to2'): continue
        atr = get_atr14(b)
        if not atr or atr<=0 or st['close'] is None: continue
        if i+HORIZON_4H >= len(bars_4h): continue
        next_b = bars_4h[i+HORIZON_4H]
        next_close = (next_b.get('ohlcv_last_40_bars') or [{}])[-1].get('close')
        if next_close is None: continue
        close_R = (next_close - st['close']) / atr
        trades.append({
            'bar_4h_index': i,
            'entry_time': st['entry_time'],
            'entry_price': st['close'],
            'rsi': st['rsi'],
            'close_R': round(close_R, 2),
        })

    print(f"  {len(trades)} trades V0 reconstruídos")

    # Para cada trade, mapear pro bar diário correspondente (o mais recente <= entry_time)
    def find_daily_idx(entry_ts):
        for i in range(len(daily_bars)-1, -1, -1):
            if daily_bars[i]["time"] <= entry_ts:
                return i
        return None

    for t in trades:
        di = find_daily_idx(t['entry_time'])
        if di is None:
            t['daily_idx']=None; continue
        t['daily_idx'] = di
        t['daily_close'] = daily_bars[di]['close']
        t['ema50'] = ema50_d[di]
        t['above_ema50'] = (daily_bars[di]['close'] > ema50_d[di]) if ema50_d[di] else None
        t['dist_from_14d_high_pct'] = dist_from_14d_high[di]
        t['slope_ema50'] = slope_d[di]

    # Filtra trades com dados completos
    valid = [t for t in trades if t.get('ema50') is not None]
    print(f"\n  {len(valid)} trades com dados macro diário disponíveis")

    # === Análise por regime ===
    def stats(group):
        if not group: return {"n":0}
        rs = [t['close_R'] for t in group]
        return {"n":len(group), "win%":round(100*sum(1 for r in rs if r>0)/len(rs),1), "avg_R":round(mean(rs),2), "median_R":round(median(rs),2)}

    print("\n=== Bucket 1: position vs EMA50 1D ===")
    print(f"  Acima EMA50 1D: {stats([t for t in valid if t['above_ema50']])}")
    print(f"  Abaixo EMA50 1D: {stats([t for t in valid if t['above_ema50'] is False])}")

    print("\n=== Bucket 2: distance from 14d high ===")
    buckets_dist = [
        ("dist > -2% (esticado, no high)", lambda t: t['dist_from_14d_high_pct'] > -2),
        ("dist -2 a -4%", lambda t: -4 < t['dist_from_14d_high_pct'] <= -2),
        ("dist -4 a -7% (correção média)", lambda t: -7 < t['dist_from_14d_high_pct'] <= -4),
        ("dist < -7% (correção profunda / falling knife)", lambda t: t['dist_from_14d_high_pct'] <= -7),
    ]
    for label, f in buckets_dist:
        print(f"  {label}: {stats([t for t in valid if f(t)])}")

    print("\n=== Bucket 3: slope EMA50 1D ===")
    print(f"  slope UP: {stats([t for t in valid if t['slope_ema50']=='up'])}")
    print(f"  slope FLAT: {stats([t for t in valid if t['slope_ema50']=='flat'])}")
    print(f"  slope DOWN: {stats([t for t in valid if t['slope_ema50']=='down'])}")

    print("\n=== Bucket COMBINADO: Acima EMA50 + slope UP + dist < -7% ===")
    combos = [
        ("Regime IDEAL: acima EMA50 + slope UP + dist > -7%",
         lambda t: t['above_ema50'] and t['slope_ema50']=='up' and t['dist_from_14d_high_pct'] > -7),
        ("Regime FAVORÁVEL: acima EMA50 + slope UP",
         lambda t: t['above_ema50'] and t['slope_ema50']=='up'),
        ("Regime NEUTRO: acima EMA50 + slope FLAT",
         lambda t: t['above_ema50'] and t['slope_ema50']=='flat'),
        ("Regime HOSTIL: abaixo EMA50 OU slope DOWN",
         lambda t: t['above_ema50'] is False or t['slope_ema50']=='down'),
        ("FALLING KNIFE ALERT: dist < -7%",
         lambda t: t['dist_from_14d_high_pct'] <= -7),
    ]
    for label, f in combos:
        print(f"  {label}: {stats([t for t in valid if f(t)])}")

    # === Tabela individual de trades pra debug ===
    print("\n=== Detalhe dos 5 maiores LOSERS (close_R < 0) ===")
    losers = sorted([t for t in valid if t['close_R'] < 0], key=lambda t: t['close_R'])[:5]
    for t in losers:
        dt = datetime.fromtimestamp(t['entry_time'], tz=timezone.utc).strftime('%Y-%m-%d %H:%M')
        print(f"  {dt} | R={t['close_R']:+.2f} | above_ema50={t['above_ema50']} | dist_14d_high={t['dist_from_14d_high_pct']:+.1f}% | slope={t['slope_ema50']}")

    print("\n=== Detalhe dos 5 maiores WINNERS ===")
    winners = sorted([t for t in valid if t['close_R'] > 0], key=lambda t: -t['close_R'])[:5]
    for t in winners:
        dt = datetime.fromtimestamp(t['entry_time'], tz=timezone.utc).strftime('%Y-%m-%d %H:%M')
        print(f"  {dt} | R={t['close_R']:+.2f} | above_ema50={t['above_ema50']} | dist_14d_high={t['dist_from_14d_high_pct']:+.1f}% | slope={t['slope_ema50']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
