#!/usr/bin/env python3
"""CRUZA os 7 trades MASTER do Cris (todos venceram) com o MOTOR NOVO (perna 1H + regra de zonas).
Reconstroi a perna 1H (pivo + reclaim EMAs, replica _leg_1h) no MOMENTO de cada trade a partir do store historico
(resample 1H do bars_15m; EMA21 do 15M). Diz o que o motor teria lido: perna, e se SINALIZA na direcao do trade.
Fetch dos desenhos via tab_pin (procedimento salvo). py3.9."""
import os, sys, json, datetime as dt
from zoneinfo import ZoneInfo
LX = ZoneInfo("Europe/Lisbon")
HERE = "/Users/cristrein/tradingview-mcp/my-strategy/core"
sys.path.insert(0, HERE); sys.path.insert(0, HERE + "/strategies/xau_4h_long/continuation/L1_EMA21_CONTINUATION")
sys.path.insert(0, "/Users/cristrein/tradingview-mcp/alert-bridge")
import tab_pin
from draw_xau_4h_trades import MCPClient

B15 = HERE + "/bar_store/store/bars_15m.jsonl"
KNOWN = {"Hx9J3m"}                                        # planeamento antigo, ignorar

# --- 1) fetch master trades (entry/sl/tp/dir/time) da tab 15 via tab_pin ---
tid = tab_pin.discover_tab("15", symbol_suffix="XAUUSD")
os.environ["TVMCP_TARGET_CHART_ID"] = tid
c = MCPClient(); c.start()
trades = []
try:
    dl = c.call_tool("draw_list") or {}
    for s in dl.get("shapes", []):
        if s.get("name") in ("long_position", "short_position") and s["id"] not in KNOWN:
            pr = c.call_tool("draw_get_properties", {"entity_id": s["id"]}) or {}
            pts = pr.get("points", [])
            if not pts: continue
            props = pr.get("properties", {})
            entry = pts[0]["price"]; nm = s["name"]
            d = (props.get("stopLevel") or 0) / 100.0; g = (props.get("profitLevel") or 0) / 100.0
            sl, tp = (round(entry + d, 2), round(entry - g, 2)) if nm == "short_position" else (round(entry - d, 2), round(entry + g, 2))
            trades.append({"id": s["id"], "dir": "LONG" if nm == "long_position" else "SHORT",
                           "entry": entry, "sl": sl, "tp": tp, "t": int(pts[0]["time"])})
finally:
    c.stop()

# --- 2) store 15M + resample 1H ---
b15 = [json.loads(l) for l in open(B15) if l.strip()]
b15.sort(key=lambda x: x["t"])

def resample_1h(b15):
    buck = {}
    for b in b15:
        k = (b["t"] // 3600) * 3600
        d = buck.setdefault(k, {"t": k, "o": b["o"], "h": b["h"], "l": b["l"], "c": b["c"]})
        d["h"] = max(d["h"], b["h"]); d["l"] = min(d["l"], b["l"]); d["c"] = b["c"]
    return [buck[k] for k in sorted(buck)]

b1h = resample_1h(b15)

def ema(vals, n):
    k = 2 / (n + 1); e = vals[0]
    out = [e]
    for v in vals[1:]:
        e = v * k + e * (1 - k); out.append(e)
    return out

def pivots(bars, k=2):
    """swings fractais confirmados (k barras de cada lado). Devolve listas [(idx,price)] de highs e lows."""
    hi, lo = [], []
    for i in range(k, len(bars) - k):
        wl, wr = bars[i - k:i], bars[i + 1:i + 1 + k]
        if bars[i]["h"] > max(x["h"] for x in wl + wr): hi.append((i, bars[i]["h"]))
        if bars[i]["l"] < min(x["l"] for x in wl + wr): lo.append((i, bars[i]["l"]))
    return hi, lo

def leg_at(ts):
    """replica _leg_1h no instante ts: pivo 1H mais recente + reclaim EMA21(15M). Devolve (leg, detalhe)."""
    h1 = [b for b in b1h if b["t"] <= ts]
    b15t = [b for b in b15 if b["t"] <= ts]
    if len(h1) < 8 or len(b15t) < 22: return "?", "sem dados"
    hi, lo = pivots(h1, 2)
    if not hi or not lo: return "?", "sem pivots"
    last_hi_i, last_lo_i = hi[-1][0], lo[-1][0]
    pivot_bias = "up" if last_lo_i > last_hi_i else "down"
    ema21 = ema([b["c"] for b in b15t], 21)[-1]
    price = b15t[-1]["c"]
    ema_confirm = "up" if price > ema21 else "down"
    net = h1[-1]["c"] - h1[max(0, len(h1) - 20)]["c"]      # dominante = sinal do movimento 1H recente
    dom = "up" if net > 0 else "down"
    if pivot_bias == "up" and ema_confirm == "up": leg = "BULL"
    elif pivot_bias == "down" and ema_confirm == "down": leg = "BEAR"
    else: leg = "BULL" if dom == "up" else "BEAR"
    return leg, f"pivo {pivot_bias} · ema {ema_confirm} · dom {dom}"

# --- 3) cruzamento ---
HTF_SUP = 4136.0     # base do supply 4H/1D da semana (4136-4166) — zona de reversao valida p/ short
HTF_DEM = 4024.0     # topo da demanda 1D (3959-4024)
trades.sort(key=lambda t: t["entry"])
print(f"=== CRUZAMENTO MASTER TRADES × MOTOR NOVO ({len(trades)} trades, todos venceram) ===\n")
match = 0
for t in trades:
    leg, det = leg_at(t["t"])
    when = dt.datetime.fromtimestamp(t["t"], LX).strftime("%d/%m %H:%M")
    near_htf_sup = t["entry"] >= HTF_SUP - 12
    near_htf_dem = t["entry"] <= HTF_DEM + 12
    # regra do motor
    if t["dir"] == "LONG":
        if leg == "BULL": verdict, why = "SINALIZA (LONG continuação, demanda da perna BULL)", "com-perna"
        elif near_htf_dem: verdict, why = "SINALIZA (LONG reversão em demanda HTF)", "reversão HTF"
        else: verdict, why = "SKIP (long contra perna BEAR sem demanda HTF)", "contra-perna"
    else:
        if leg == "BEAR": verdict, why = "SINALIZA (SHORT continuação, supply da perna BEAR)", "com-perna"
        elif near_htf_sup: verdict, why = "SINALIZA (SHORT reversão em supply HTF)", "reversão HTF"
        else: verdict, why = "SKIP (short contra perna BULL sem supply HTF)", "contra-perna"
    ok = verdict.startswith("SINALIZA")
    match += ok
    rr = abs(t['tp'] - t['entry']) / max(abs(t['entry'] - t['sl']), 0.01)
    print(f"● {t['dir']:5} entry {t['entry']:.2f} · SL {t['sl']:.2f} · TP {t['tp']:.2f} · RR {rr:.1f} · {when} ({t['id']})")
    print(f"    perna 1H no momento = {leg}  [{det}]")
    print(f"    motor → {verdict}  {'✅' if ok else '⚠️'}\n")
print(f"RESULTADO: motor SINALIZARIA {match}/{len(trades)} dos master trades vencedores")
