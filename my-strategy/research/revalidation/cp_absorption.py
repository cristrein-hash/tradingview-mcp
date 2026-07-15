#!/usr/bin/env python3
"""Cp REFINO ABSORÇÃO/EXAUSTÃO (Cris 2026-07-15) — sobre a leitura de intensidade-de-leilão (perna
significativa + order-flow cumulativo), adiciona a DINÂMICA: o clímax de venda seguido de EXAUSTÃO
(a venda deixa de ser absorvida = o fundo) + absorção compradora a assumir. Auction theory: capitulação
= oferta esgota-se sob demanda. Features causais (<=entrada). Testa se refina a discriminação dos 5 GT."""
import gzip, json, bisect, statistics, datetime as dt
from pathlib import Path
import sys; HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE))
import macro_structural_v3 as MM
ds = lambda t: dt.datetime.utcfromtimestamp(int(t)).strftime("%Y-%m-%d %H:%M")
grp = lambda rec, k, s: next((x for x in (rec.get(k) or []) if s.lower() in str(x.get("name", "")).lower()), None)
def iso2ep(x):
    try: return int(dt.datetime.fromisoformat(x.replace("Z", "+00:00")).timestamp())
    except Exception: return None
M_FRAC, LEGWIN, HMAX, LEGMIN = 3, 480, 480, 15
BLOCKS = ["XAUUSD_15m_replay_2025-11-25_to_2026-02-25.jsonl.gz",
          "XAUUSD_15m_replay_2026-02-25_to_2026-05-25_rerun_customOBbaseline.jsonl.gz",
          "XAUUSD_15m_replay_2026-05-25_to_2026-07-04.jsonl.gz"]
bars = {}; buyb = {}; sellb = {}
for blk in BLOCKS:
    snaps = []
    with gzip.open(Path("/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/15M")/blk, "rt") as fh:
        for line in fh:
            line = line.strip()
            if not line: continue
            try: r = json.loads(line)
            except Exception: continue
            if isinstance(r, dict) and r.get("ohlcv"): snaps.append(r)
    snaps.sort(key=lambda r: r.get("replay_current_date") or 0)
    for r in snaps:
        oh = r.get("ohlcv") or []; cur = oh[-1]["time"] if oh and isinstance(oh[-1], dict) else None
        for b in oh:
            if isinstance(b, dict) and b.get("time") is not None: bars[b["time"]] = {"o": b["open"], "h": b["high"], "l": b["low"], "c": b["close"]}
        pb = r.get("pine_shapes_bubbles")
        if pb:
            ka = iso2ep(r.get("replay_current_dt") or ""); BUY = {"plot_0": 1, "plot_2": 2, "plot_4": 3}; SELL = {"plot_6": 1, "plot_8": 2, "plot_10": 3}
            for act in (pb[0].get("activations") or []):
                tt = act.get("time")
                for plot in (act.get("shapes") or {}):
                    if plot in BUY and (tt, plot) not in buyb: buyb[(tt, plot)] = {"t": tt, "size": BUY[plot], "ka": ka}
                    if plot in SELL and (tt, plot) not in sellb: sellb[(tt, plot)] = {"t": tt, "size": SELL[plot], "ka": ka}
T = sorted(bars); O = [bars[t]["o"] for t in T]; H = [bars[t]["h"] for t in T]; L = [bars[t]["l"] for t in T]; C = [bars[t]["c"] for t in T]
N = len(T); ATR = [None]*N; trs = []
for i in range(N):
    if i > 0: trs.append(max(H[i]-L[i], abs(H[i]-C[i-1]), abs(L[i]-C[i-1])))
    ATR[i] = sum(trs[-14:])/14 if len(trs) >= 14 else None
BUYS = sorted(buyb.values(), key=lambda x: x["t"]); SELLS = sorted(sellb.values(), key=lambda x: x["t"]); BT = [x["t"] for x in BUYS]; ST = [x["t"] for x in SELLS]
def is_sl(p): return p-M_FRAC >= 0 and p+M_FRAC < N and L[p] == min(L[p-M_FRAC:p+M_FRAC+1]) and L[p] < min(L[p-M_FRAC:p])
SLB = [p for p in range(M_FRAC, N-M_FRAC) if is_sl(p)]
t_lo = int(dt.datetime(2026, 2, 1, tzinfo=dt.timezone.utc).timestamp()); t_hi = int(dt.datetime(2026, 7, 4, tzinfo=dt.timezone.utc).timestamp())
GT = []
for a, b in [(1770015600, 1770210000), (1770339600, 1771448400), (1774242000, 1774270800), (1781128800, 1781128800), (1782781200, 1782907200)]:
    aa = bisect.bisect_left(T, min(a, b)-12*3600); bb = bisect.bisect_right(T, max(a, b)+12*3600); GT.append(T[min(range(aa, bb), key=lambda k: L[k])])
def reclaim_entry(j):
    atr = ATR[j] or 5.0; sl = round(L[j]-0.1*atr, 2)
    for k in range(j+M_FRAC, min(N, j+96)):
        if L[k] <= sl: return None
        if C[k] > H[k-1] and C[k] > O[k]:
            ent = C[k]; r = ent-sl
            if r <= 0.05*atr: continue
            tgt = ent+3*r; o = "OPEN"
            for m in range(k+1, min(N, k+HMAX+1)):
                if L[m] <= sl: o = "LOSS"; break
                if H[m] >= tgt: o = "WIN"; break
            return {"ei": k, "o": o}
    return None
def sz(bubs, ts, t0, t1): return sum(bubs[i]["size"] for i in range(bisect.bisect_left(ts, t0), bisect.bisect_right(ts, t1)))
rows = []
for p in SLB:
    if not (t_lo <= T[p] <= t_hi): continue
    hb = max(range(max(0, p-LEGWIN), p+1), key=lambda k: H[k]); atr = ATR[p] or 5.0; dur = max(1, p-hb)
    if (H[hb]-L[p])/atr < LEGMIN or not (L[p] <= min(L[max(0, p-192):p+1])+1e-9): continue
    e = reclaim_entry(p)
    if not e: continue
    ei = e["ei"]; kt = T[ei]
    f = {"o": e["o"], "gt": any(abs(T[p]-g) < 6*3600 for g in GT), "dt": ds(T[p])}
    # intensidade-de-leilão (leg)
    f["act_dens"] = round((sz(BUYS, BT, T[hb], T[p])+sz(SELLS, ST, T[hb], T[p]))/dur, 2)
    # DINÂMICA: clímax de venda (pré-low) -> exaustão (pós-low) + absorção compradora
    f["sell_flush"] = sz(SELLS, ST, T[max(0, p-6)], T[p])          # venda no clímax
    f["sell_post"] = sz(SELLS, ST, T[p], kt)                       # venda pós-low (deve cair = exaustão)
    f["buy_low"] = sz(BUYS, BT, T[max(0, p-2)], kt)                # compra a assumir no/pós low
    f["exhaust"] = round(f["sell_post"]/max(1, f["sell_flush"]), 2)  # <1 = venda exauriu
    f["absorb_ratio"] = round(f["buy_low"]/max(1, f["sell_flush"]), 2)
    rows.append(f)
V2 = [r for r in rows if r["o"] in ("WIN", "LOSS")]; W = [r for r in V2 if r["o"] == "WIN"]; Lo = [r for r in V2 if r["o"] == "LOSS"]; GTr = [r for r in V2 if r["gt"]]
print(f"POPULAÇÃO N={len(V2)} WIN {len(W)}({100*len(W)/len(V2):.0f}%) GT {sum(1 for r in rows if r['gt'])}/5\n")
print("5 GT (absorção/exaustão):")
for r in [x for x in rows if x["gt"]]:
    print(f"  {r['dt']} {r['o']:4} act_dens{r['act_dens']:>5} sell_flush{r['sell_flush']:>4} sell_post{r['sell_post']:>3} buy_low{r['buy_low']:>3} exhaust{r['exhaust']:>5} absorb{r['absorb_ratio']:>5}")
print(f"\n{'feature':13} {'WIN med':>8} {'LOSS med':>8} {'GT med':>7}")
for k in ("act_dens", "sell_flush", "sell_post", "buy_low", "exhaust", "absorb_ratio"):
    print(f"  {k:13} {statistics.median([r[k] for r in W]):>8.2f} {statistics.median([r[k] for r in Lo]):>8.2f} {statistics.median([r[k] for r in GTr]) if GTr else 0:>7.2f}")
def hit(sub): w = sum(1 for r in sub if r["o"] == "WIN"); return w, len(sub), (100*w/len(sub) if sub else 0)
print("\n=== leitura refinada: leilão intenso + exaustão de venda + absorção ===")
for label, cond in [
    ("act_dens>=0.5 & exhaust<=0.6", lambda r: r["act_dens"] >= 0.5 and r["exhaust"] <= 0.6),
    ("act_dens>=0.5 & sell_flush>=8", lambda r: r["act_dens"] >= 0.5 and r["sell_flush"] >= 8),
    ("act_dens>=0.5 & (buy_low>=2 or exhaust<=0.4)", lambda r: r["act_dens"] >= 0.5 and (r["buy_low"] >= 2 or r["exhaust"] <= 0.4)),
    ("sell_flush>=8 & exhaust<=0.5", lambda r: r["sell_flush"] >= 8 and r["exhaust"] <= 0.5),
    ("act_dens>=0.6 & exhaust<=0.5", lambda r: r["act_dens"] >= 0.6 and r["exhaust"] <= 0.5)]:
    sub = [r for r in V2 if cond(r)]; w, n, h = hit(sub); ng = sum(1 for r in sub if r["gt"]); extra = [r["dt"] for r in sub if not r["gt"] and r["o"] == "WIN"]
    print(f"  {label:<44} N={n:>2} hit-3R {h:>4.0f}% ({w}/{n}) GT{ng}/5 extra{extra}")