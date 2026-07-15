#!/usr/bin/env python3
"""PLOT + AVALIAÇÃO Cp trades (Cris 2026-07-15) — as entradas da CONFLUÊNCIA AUCTION (fundo-de-perna-
significativa + buy_dens>=0.25 OU leg_sell>=180) como TRADES: long_position (entry→3R) + SL + label
auction/resultado no 15M. Mantém retângulos + as 5 notas FUNDO CAPITULAÇÃO. Pausa obrigatória. SEM
screenshot (o visual é do Cris). Painel: N·hit3R·WR·streak·por-resultado·GT-vs-extra. RAW-only."""
import gzip, json, bisect, statistics, sys, datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent; REPO = Path("/Users/cristrein/tradingview-mcp")
sys.path.insert(0, str(REPO/"alert-bridge")); sys.path.insert(0, str(HERE))
import macro_structural_v3 as MM
from draw_xau_4h_trades import MCPClient, price_to_ticks_offset
ds = lambda t: dt.datetime.utcfromtimestamp(int(t)).strftime("%Y-%m-%d %H:%M")
grp = lambda rec, k, s: next((x for x in (rec.get(k) or []) if s.lower() in str(x.get("name", "")).lower()), None)
def iso2ep(x):
    try: return int(dt.datetime.fromisoformat(x.replace("Z", "+00:00")).timestamp())
    except Exception: return None
PAUSE = Path("/tmp/claude_recheck.paused"); BAR = 900; M_FRAC, LEGWIN, HMAX, LEGMIN = 3, 480, 480, 15
BLOCKS = ["XAUUSD_15m_replay_2025-11-25_to_2026-02-25.jsonl.gz",
          "XAUUSD_15m_replay_2026-02-25_to_2026-05-25_rerun_customOBbaseline.jsonl.gz",
          "XAUUSD_15m_replay_2026-05-25_to_2026-07-04.jsonl.gz"]
bars = {}; buyb = {}; sellb = {}
for blk in BLOCKS:
    snaps = []
    with gzip.open(Path("/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/15M")/blk, "rt") as fh:
        for line in fh:
            try: r = json.loads(line)
            except Exception: continue
            if isinstance(r, dict) and r.get("ohlcv"): snaps.append(r)
    snaps.sort(key=lambda r: r.get("replay_current_date") or 0)
    for r in snaps:
        oh = r.get("ohlcv") or []
        for b in oh:
            if isinstance(b, dict) and b.get("time") is not None: bars[b["time"]] = {"o": b["open"], "h": b["high"], "l": b["low"], "c": b["close"]}
        pb = r.get("pine_shapes_bubbles")
        if pb:
            ka = iso2ep(r.get("replay_current_dt") or ""); BUY = {"plot_0": 1, "plot_2": 2, "plot_4": 3}; SELL = {"plot_6": 1, "plot_8": 2, "plot_10": 3}
            for act in (pb[0].get("activations") or []):
                tt = act.get("time")
                for plot in (act.get("shapes") or {}):
                    if plot in BUY and (tt, plot) not in buyb: buyb[(tt, plot)] = {"t": tt, "size": BUY[plot]}
                    if plot in SELL and (tt, plot) not in sellb: sellb[(tt, plot)] = {"t": tt, "size": SELL[plot]}
T = sorted(bars); O = [bars[t]["o"] for t in T]; H = [bars[t]["h"] for t in T]; L = [bars[t]["l"] for t in T]; C = [bars[t]["c"] for t in T]
N = len(T); ATR = [None]*N; trs = []
for i in range(N):
    if i > 0: trs.append(max(H[i]-L[i], abs(H[i]-C[i-1]), abs(L[i]-C[i-1])))
    ATR[i] = sum(trs[-14:])/14 if len(trs) >= 14 else None
BT = sorted(x["t"] for x in buyb.values()); ST = sorted(x["t"] for x in sellb.values())
BUYS = sorted(buyb.values(), key=lambda x: x["t"]); SELLS = sorted(sellb.values(), key=lambda x: x["t"])
def is_sl(p): return p-M_FRAC >= 0 and p+M_FRAC < N and L[p] == min(L[p-M_FRAC:p+M_FRAC+1]) and L[p] < min(L[p-M_FRAC:p])
SLB = [p for p in range(M_FRAC, N-M_FRAC) if is_sl(p)]
t_lo = int(dt.datetime(2026, 2, 1, tzinfo=dt.timezone.utc).timestamp()); t_hi = int(dt.datetime(2026, 7, 4, tzinfo=dt.timezone.utc).timestamp())
GT = []
for a, b in [(1770015600, 1770210000), (1770339600, 1771448400), (1774242000, 1774270800), (1781128800, 1781128800), (1782781200, 1782907200)]:
    aa = bisect.bisect_left(T, min(a, b)-12*3600); bb = bisect.bisect_right(T, max(a, b)+12*3600); GT.append(T[min(range(aa, bb), key=lambda k: L[k])])
def sz(bubs, ts, t0, t1): return sum(bubs[i]["size"] for i in range(bisect.bisect_left(ts, t0), bisect.bisect_right(ts, t1)))
def entry_full(j):
    atr = ATR[j] or 5.0; sl = round(L[j]-0.1*atr, 2)
    for k in range(j+M_FRAC, min(N, j+96)):
        if L[k] <= sl: return None
        if C[k] > H[k-1] and C[k] > O[k]:
            ent = round(C[k], 2); r = ent-sl
            if r <= 0.05*atr: continue
            tgt = round(ent+3*r, 2); o = "OPEN"
            for m in range(k+1, min(N, k+HMAX+1)):
                if L[m] <= sl: o = "LOSS"; break
                if H[m] >= tgt: o = "WIN"; break
            return {"ei": k, "t_ent": T[k], "ent": ent, "sl": sl, "tgt": tgt, "R": round(r, 2), "o": o}
    return None
# construir as trades da confluência auction
trades = []
for p in SLB:
    if not (t_lo <= T[p] <= t_hi): continue
    hb = max(range(max(0, p-LEGWIN), p+1), key=lambda k: H[k]); atr = ATR[p] or 5.0; dur = max(1, p-hb)
    if (H[hb]-L[p])/atr < LEGMIN or not (L[p] <= min(L[max(0, p-192):p+1])+1e-9): continue
    e = entry_full(p)
    if not e: continue
    buy_dens = sz(BUYS, BT, T[hb], T[p])/dur; leg_sell = sz(SELLS, ST, T[hb], T[p]); act_dens = (sz(BUYS, BT, T[hb], T[p])+leg_sell)/dur
    if not (buy_dens >= 0.25 or leg_sell >= 180): continue        # CONFLUÊNCIA AUCTION
    e["gt"] = any(abs(T[p]-g) < 6*3600 for g in GT); e["act_dens"] = round(act_dens, 2); e["dt"] = ds(T[p]); trades.append(e)

# PAINEL
v = [t for t in trades if t["o"] in ("WIN", "LOSS")]; w = sum(1 for t in v if t["o"] == "WIN")
eq = pk = dd = strk = mx = 0
for t in v:
    x = 3 if t["o"] == "WIN" else -1; eq += x; pk = max(pk, eq); dd = min(dd, eq-pk); strk = strk+1 if x < 0 else 0; mx = min(mx, -strk)
print(f"=== PAINEL Cp (confluência auction) ===")
print(f"  N={len(trades)} ({len(v)} resolvidos) · WIN {w} · LOSS {len(v)-w} · OPEN {len(trades)-len(v)}")
print(f"  hit-3R {100*w/max(1,len(v)):.0f}% · NET {sum(3 if t['o']=='WIN' else -1 for t in v):+}R · maxDD {dd}R · streak {mx} · GT {sum(1 for t in trades if t['gt'])}/5")

# PLOT
def main():
    assert PAUSE.exists(), "pausa ausente"
    c = MCPClient(); c.start()
    try:
        st = c.call_tool("chart_get_state")
        if "XAUUSD" not in str(st.get("symbol", "")): print(json.dumps({"HARD_STOP": st.get("symbol")})); return
        if str(st.get("resolution")) not in ("15", "15m"): c.call_tool("chart_set_timeframe", {"timeframe": "15"})
        rm = kp = 0
        for it in c.call_tool("draw_list").get("shapes", []):
            if it.get("name") in ("rectangle", "text_note"): kp += 1; continue     # MANTÉM retângulos + notas do Cris
            if c.call_tool("draw_remove_one", {"entity_id": it["id"]}).get("success"): rm += 1
        print(json.dumps({"removidos": rm, "mantidos(ret+notas)": kp}))
        COL = {"WIN": "#1a8917", "LOSS": "#c62828", "OPEN": "#888888"}
        for t in trades:
            c.call_tool("draw_shape", {"shape": "long_position", "point": {"time": t["t_ent"], "price": t["ent"]},
                "point2": {"time": t["t_ent"]+20*BAR, "price": t["tgt"]},
                "overrides": json.dumps({"stopLevel": price_to_ticks_offset(t["ent"], t["sl"]), "profitLevel": price_to_ticks_offset(t["ent"], t["tgt"])})})
            tag = ("★GT " if t["gt"] else "") + f"Cp {t['o']} act{t['act_dens']} R{t['R']}"
            c.call_tool("draw_shape", {"shape": "text", "point": {"time": t["t_ent"], "price": t["sl"]},
                "text": tag, "overrides": json.dumps({"color": COL[t["o"]], "fontsize": 9, "bold": t["gt"]})})
        if trades: c.call_tool("chart_scroll_to_date", {"date": trades[0]["dt"][:10]})
        print(json.dumps({"plotadas": len(trades)}))
    finally:
        try: c.stop()
        except Exception: pass

if __name__ == "__main__":
    main()
