#!/usr/bin/env python3
"""Corre o entry Cp APROVADO (1º-reclaim + 3R-fixo, cp_refined.run/entry_first/exit_fixed3R) sobre 15M
Set/2025 -> 2026-07-04 (inclui a 2ª coleta ...2026-05-25_to_2026-07-04), e PLOTA os trades no chart 15M
(apaga os legs v3 antes). Estrutura+confluência-auction+reclaim+SL/3R = regras congeladas do prereg.
RAW-only, causal. py3.9 stdlib. Lógica copiada VERBATIM de cp_refined.py (proveniência)."""
import os, sys, gzip, json, bisect, urllib.request, datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, "/Users/cristrein/tradingview-mcp/alert-bridge")
from draw_xau_4h_trades import MCPClient, price_to_ticks_offset

RAW = Path("/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/15M")
BLOCKS = ["XAUUSD_15m_replay_2025-08-25_to_2025-11-25.jsonl.gz",
          "XAUUSD_15m_replay_2025-11-25_to_2026-02-25.jsonl.gz",
          "XAUUSD_15m_replay_2026-02-25_to_2026-05-25_rerun_customOBbaseline.jsonl.gz",
          "XAUUSD_15m_replay_2026-05-25_to_2026-07-04.jsonl.gz"]   # 2ª coleta incluída
M_FRAC, LEGWIN, LEGMIN, HMAX = 3, 480, 15, 480
BOX_BARS, BAR_S = 20, 900
ds = lambda t: dt.datetime.utcfromtimestamp(int(t)).strftime("%Y-%m-%d %H:%M")
T_LO = int(dt.datetime(2025, 9, 1, tzinfo=dt.timezone.utc).timestamp())
T_HI = int(dt.datetime(2026, 7, 4, tzinfo=dt.timezone.utc).timestamp())

# --- carregar (verbatim cp_refined) ---
bars = {}; buyb = {}; sellb = {}
for blk in BLOCKS:
    snaps = []
    with gzip.open(RAW / blk, "rt") as fh:
        for line in fh:
            try: r = json.loads(line)
            except Exception: continue
            if isinstance(r, dict) and r.get("ohlcv"): snaps.append(r)
    snaps.sort(key=lambda r: r.get("replay_current_date") or 0)
    for r in snaps:
        for b in (r.get("ohlcv") or []):
            if isinstance(b, dict) and b.get("time") is not None:
                bars[b["time"]] = {"o": b["open"], "h": b["high"], "l": b["low"], "c": b["close"]}
        pb = r.get("pine_shapes_bubbles")
        if pb:
            BUY = {"plot_0": 1, "plot_2": 2, "plot_4": 3}; SELL = {"plot_6": 1, "plot_8": 2, "plot_10": 3}
            for act in (pb[0].get("activations") or []):
                tt = act.get("time")
                for plot in (act.get("shapes") or {}):
                    if plot in BUY and (tt, plot) not in buyb: buyb[(tt, plot)] = {"t": tt, "sz": BUY[plot]}
                    if plot in SELL and (tt, plot) not in sellb: sellb[(tt, plot)] = {"t": tt, "sz": SELL[plot]}
T = sorted(bars); O = [bars[t]["o"] for t in T]; H = [bars[t]["h"] for t in T]; L = [bars[t]["l"] for t in T]; C = [bars[t]["c"] for t in T]
N = len(T); ATR = [None] * N; trs = []
for i in range(N):
    if i > 0: trs.append(max(H[i] - L[i], abs(H[i] - C[i - 1]), abs(L[i] - C[i - 1])))
    ATR[i] = sum(trs[-14:]) / 14 if len(trs) >= 14 else None
BUYS = sorted(buyb.values(), key=lambda x: x["t"]); SELLS = sorted(sellb.values(), key=lambda x: x["t"])
BT = [x["t"] for x in BUYS]; ST = [x["t"] for x in SELLS]


def is_sl(p): return p - M_FRAC >= 0 and p + M_FRAC < N and L[p] == min(L[p - M_FRAC:p + M_FRAC + 1]) and L[p] < min(L[p - M_FRAC:p])
SLB = [p for p in range(M_FRAC, N - M_FRAC) if is_sl(p)]
def sz(bubs, ts, t0, t1): return sum(bubs[i]["sz"] for i in range(bisect.bisect_left(ts, t0), bisect.bisect_right(ts, t1)))


def entry_first(j):
    atr = ATR[j] or 5.0; sl = round(L[j] - 0.1 * atr, 2)
    for k in range(j + M_FRAC, min(N, j + 96)):
        if L[k] <= sl: return None
        if C[k] > H[k - 1] and C[k] > O[k]:
            ent = round(C[k], 2); r = ent - sl
            if r > 0.05 * atr: return {"k": k, "ent": ent, "sl": sl, "R": round(r, 2)}
    return None


def exit_fixed3R(k, ent, sl):
    r = ent - sl; tgt = ent + 3 * r
    for m in range(k + 1, min(N, k + HMAX + 1)):
        if L[m] <= sl: return -1.0
        if H[m] >= tgt: return 3.0
    return round((C[min(N - 1, k + HMAX)] - ent) / r, 2)


def run_trades():
    out = []
    for p in SLB:
        if not (T_LO <= T[p] <= T_HI): continue
        hb = max(range(max(0, p - LEGWIN), p + 1), key=lambda k: H[k]); atr = ATR[p] or 5.0; dur = max(1, p - hb)
        if (H[hb] - L[p]) / atr < LEGMIN or not (L[p] <= min(L[max(0, p - 192):p + 1]) + 1e-9): continue
        if not (sz(BUYS, BT, T[hb], T[p]) / dur >= 0.25 or sz(SELLS, ST, T[hb], T[p]) >= 180): continue
        e = entry_first(p)
        if not e: continue
        R = exit_fixed3R(e["k"], e["ent"], e["sl"])
        tgt = round(e["ent"] + 3 * (e["ent"] - e["sl"]), 2)
        oc = "WIN" if R == 3.0 else ("LOSS" if R == -1.0 else f"{R:+.1f}R")
        out.append({"etime": int(T[e["k"]]), "ent": e["ent"], "sl": e["sl"], "tgt": tgt, "R": R, "oc": oc, "fundo": ds(T[p])})
    return out


def find_15m():
    with urllib.request.urlopen("http://localhost:9222/json/list", timeout=8) as r:
        tgs = [t["id"] for t in json.loads(r.read()) if t.get("type") == "page" and "tradingview.com/chart" in (t.get("url") or "").lower()]
    for tid in tgs:
        os.environ["TVMCP_TARGET_CHART_ID"] = tid
        c = MCPClient(); c.start()
        try:
            if str((c.call_tool("chart_get_state") or {}).get("resolution")) == "15": return tid
        finally: c.stop()
    return None


def main():
    tr = run_trades()
    net = sum(r["R"] for r in tr); wins = sum(1 for r in tr if r["R"] > 0)
    print(f"série 15M: {ds(T[0])} -> {ds(T[-1])} (N={N})")
    print(f"Cp trades Set/2025->07-04: N={len(tr)} · WR {100*wins/max(1,len(tr)):.0f}% · NET {net:+.1f}R")
    for i, r in enumerate(tr, 1):
        print(f"  {i:2d} fundo {r['fundo']} -> entry {ds(r['etime'])} ent={r['ent']:.2f} SL={r['sl']:.2f} tgt={r['tgt']:.2f} {r['oc']}")
    tid = find_15m()
    if not tid: print("SEM tab 15M"); return
    os.environ["TVMCP_TARGET_CHART_ID"] = tid
    c = MCPClient(); c.start()
    try:
        print("draw_clear (apaga legs v3):", (c.call_tool("draw_clear") or {}).get("success"))
        if tr:
            c.call_tool("chart_scroll_to_date", {"date": dt.datetime.utcfromtimestamp(tr[0]["etime"]).strftime("%Y-%m-%d")})
            import time as _t; _t.sleep(3)
        drawn = 0
        for k, s in enumerate(tr, 1):
            r = c.call_tool("draw_shape", {"shape": "long_position",
                            "point": {"time": s["etime"], "price": s["ent"]},
                            "point2": {"time": s["etime"] + BOX_BARS * BAR_S, "price": s["tgt"]},
                            "overrides": json.dumps({"stopLevel": price_to_ticks_offset(s["ent"], s["sl"]),
                                                     "profitLevel": price_to_ticks_offset(s["ent"], s["tgt"])})})
            if isinstance(r, dict) and r.get("success"):
                drawn += 1; Rd = abs(s["ent"] - s["sl"])
                c.call_tool("draw_shape", {"shape": "text", "point": {"time": s["etime"], "price": s["ent"] + 0.5 * Rd},
                            "text": f"#{k} {s['oc']}", "overrides": json.dumps({"color": "#6a1b9a", "bold": True, "fontsize": 12})})
        print(f"desenhados {drawn}/{len(tr)} trades Cp")
    finally:
        c.stop()


if __name__ == "__main__":
    main()
