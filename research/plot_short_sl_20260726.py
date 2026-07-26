#!/usr/bin/env python3
"""PLOT canónico (skill plotting-canon) de 5 operações com SL-curto do E1 (winners escondidos: outcome SL
mas MFE>=2R) p/ revisão visual do Cris. ADITIVO — NO_CLEAR (os 9 winners verdes ficam). 1H (trades >2 dias;
exceção de TF declarada, motivo=histórico). long_position + stopLevel/profitLevel ticks 0.01 + label S1-S5
vermelho outcome-SL. Read-back de verificação no fim. Daemons pausados pelo caller."""
import os, sys, json, bisect, time, datetime as dt
from zoneinfo import ZoneInfo
LX = ZoneInfo("Europe/Lisbon")
R = "/Users/cristrein/tradingview-mcp/"
HERE = R + "my-strategy/core"
sys.path.insert(0, HERE); sys.path.insert(0, HERE + "/strategies/xau_4h_long/continuation/L1_EMA21_CONTINUATION")
sys.path.insert(0, R + "alert-bridge")
import tab_pin
from draw_xau_4h_trades import MCPClient, price_to_ticks_offset
WIDTH_S = 6 * 3600
hm = lambda t: dt.datetime.fromtimestamp(int(t), LX).strftime("%d/%m %H:%M")

# ---- reconstruir os escondidos (mesma lógica da auditoria v2: geom válida, SL/AMBIG, MFE>=2R) ----
bars = sorted([json.loads(l) for l in open(R + "my-strategy/core/bar_store/store/bars_15m.jsonl") if l.strip()], key=lambda b: b["t"])
T = [b["t"] for b in bars]; H = [b["h"] for b in bars]; L = [b["l"] for b in bars]

def resolve(d, e, sl, tg, bt, horizon=96):
    i0 = bisect.bisect_right(T, bt); risk = abs(e - sl)
    mfe = 0.0; oc = None
    for i in range(i0, min(i0 + horizon, len(T))):
        hi, lo = H[i], L[i]
        if d == "LONG":
            mfe = max(mfe, (hi - e) / risk); hit_sl = lo <= sl; hit_tp = hi >= tg
        else:
            mfe = max(mfe, (e - lo) / risk); hit_sl = hi >= sl; hit_tp = lo <= tg
        if oc is None:
            oc = "AMBIGUOUS" if (hit_sl and hit_tp) else ("SL" if hit_sl else ("TP" if hit_tp else None))
    return oc or "OPEN", round(mfe, 1)

uniq = {}
for l in open(R + "alert-bridge/logs/e1_candidates.jsonl"):
    if not l.strip(): continue
    c = json.loads(l)
    uniq[(c.get("bar_time"), c.get("rule"), c.get("direction"), c.get("tf"))] = c
t0 = dt.datetime(2026, 7, 16, tzinfo=LX).timestamp()
hidden = []
seen_te = set()
for k, c in sorted(uniq.items(), key=lambda kv: kv[0][0] or 0):
    if (c.get("bar_time") or 0) < t0: continue
    e, sl, tg, d = c.get("entry"), c.get("sl"), c.get("target"), c.get("direction")
    if not (e and sl and tg): continue
    if abs(e - sl) < 1.0: continue
    if d == "LONG" and not (sl < e < tg): continue
    if d == "SHORT" and not (tg < e < sl): continue
    oc, mfe = resolve(d, e, sl, tg, c["bar_time"])
    if oc in ("SL", "AMBIGUOUS") and mfe >= 2.0:
        te = (c["bar_time"], round(e, 1))
        if te in seen_te: continue          # dedup mesmo trade em TFs diferentes
        seen_te.add(te)
        hidden.append({"t": c["bar_time"], "dir": d, "rule": c["rule"], "tf": c["tf"],
                       "e": e, "sl": sl, "tg": tg, "mfe": mfe})
hidden.sort(key=lambda r: -r["mfe"])
top5 = hidden[:5]
print("=== 5 operações SL-curto a plotar (1H, vermelho, S1-S5) ===")
for i, m in enumerate(top5):
    print(f"  S{i+1} {hm(m['t'])} {m['dir']} {m['rule']}@{m['tf']} entry {m['e']} SL {m['sl']} "
          f"(risco {abs(m['e']-m['sl']):.2f} pts) alvo {m['tg']} | MFE {m['mfe']}R")

# ---- plot canónico (aditivo, tab 15M XAUUSD pinada, timeframe 60) ----
tid = tab_pin.discover_tab("15", symbol_suffix="XAUUSD")
os.environ["TVMCP_TARGET_CHART_ID"] = tid
c = MCPClient(); c.start()
try:
    c.call_tool("chart_set_timeframe", {"timeframe": "60"})
    time.sleep(4)
    drawn = 0
    for i, m in enumerate(top5):
        shape = "long_position" if m["dir"] == "LONG" else "short_position"
        r1 = c.call_tool("draw_shape", {"shape": shape,
            "point": {"time": m["t"], "price": m["e"]},
            "point2": {"time": m["t"] + WIDTH_S, "price": m["tg"]},
            "overrides": json.dumps({"stopLevel": price_to_ticks_offset(m["e"], m["sl"]),
                                     "profitLevel": price_to_ticks_offset(m["e"], m["tg"])})})
        drawn += bool(r1.get("success"))
        Rr = abs(m["e"] - m["sl"])
        c.call_tool("draw_shape", {"shape": "text", "point": {"time": m["t"], "price": m["e"] + 0.5 * Rr},
                    "text": f"S{i+1}", "overrides": json.dumps({"color": "#cc0000", "bold": True, "fontsize": 12})})
    print(f"\nplotados {drawn}/5 (aditivo — 9 winners verdes intactos)")
    print("\nVERIFICAÇÃO (read-back):")
    dl = c.call_tool("draw_list") or {}
    n_pos = 0; okw = 0
    for s in dl.get("shapes", []):
        if s.get("name") in ("long_position", "short_position"):
            n_pos += 1
            pr = c.call_tool("draw_get_properties", {"entity_id": s["id"]}) or {}
            pts = pr.get("points", [])
            if len(pts) >= 2 and pts[0].get("time") != pts[1].get("time"): okw += 1
    print(f"  posições no chart: {n_pos} (esperado 14 = 9 verdes + 5 novos) · com largura: {okw}")
finally:
    c.stop()
