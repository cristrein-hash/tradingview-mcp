#!/usr/bin/env python3
"""Cp CONFLUÊNCIA (Cris 2026-07-15) — estrutura + contexto + CONFLUÊNCIA de indicadores (a ordem que
resulta), com extração CORRIGIDA: NAS labels por first-appearance REAL (o cluster) + SELL/BUY bubbles
(clímax de venda + absorção), não só BUY. Na população correta (fundos-de-perna-significativa). Testa
CONVERGÊNCIA (vários indicadores juntos) que separa os 5 GT + acha outros fundos 3R. RAW-only, causal."""
import gzip, json, bisect, statistics, datetime as dt
from pathlib import Path
import sys; HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE))
import macro_structural_v3 as MM
ds = lambda t: dt.datetime.utcfromtimestamp(int(t)).strftime("%Y-%m-%d %H:%M")
grp = lambda rec, k, s: next((x for x in (rec.get(k) or []) if s.lower() in str(x.get("name", "")).lower()), None)
def fnum(x):
    if x is None: return None
    try: return float(str(x).replace("−", "-").replace(",", ""))
    except Exception: return None
def iso2ep(x):
    try: return int(dt.datetime.fromisoformat(x.replace("Z", "+00:00")).timestamp())
    except Exception: return None
M_FRAC, LEGWIN, HMAX, LEGMIN = 3, 480, 480, 15
BLOCKS = ["XAUUSD_15m_replay_2025-11-25_to_2026-02-25.jsonl.gz",
          "XAUUSD_15m_replay_2026-02-25_to_2026-05-25_rerun_customOBbaseline.jsonl.gz",
          "XAUUSD_15m_replay_2026-05-25_to_2026-07-04.jsonl.gz"]
bars = {}; SV = {}; nas_first = {}; buyb = {}; sellb = {}
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
            if isinstance(b, dict) and b.get("time") is not None:
                bars[b["time"]] = {"o": b["open"], "h": b["high"], "l": b["low"], "c": b["close"]}
        if cur is None: continue
        nas = (grp(r, "study_values", "NAS") or {}).get("values") or {}; rsi = (grp(r, "study_values", "Relative") or {}).get("values") or {}
        SV[cur] = {"nas_dist": fnum(nas.get("NAS_DISTANCE_FROM_EMA_ATR")), "nas_rsi": fnum(nas.get("NAS_RSI")),
                   "rsi": fnum(rsi.get("RSI")), "rsi_ma": fnum(rsi.get("RSI-based MA")), "regbull": fnum(rsi.get("Regular Bullish"))}
        # NAS labels first-appearance REAL (por id global, com known_at = 1º cur onde aparece)
        ng = grp(r, "pine_labels", "NAS")
        for l in (ng.get("labels") or []) if ng else []:
            lid = l.get("id")
            if lid is None or (blk, lid) in nas_first: continue
            nas_first[(blk, lid)] = {"ka": cur, "dir": "LONG" if "LONG" in str(l.get("text", "")).upper() else ("SHORT" if "SHORT" in str(l.get("text", "")).upper() else "?"), "price": l.get("price")}
        # bubbles BUY/SELL com known_at
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
NAS = sorted(nas_first.values(), key=lambda x: x["ka"] or 0); BUYS = sorted(buyb.values(), key=lambda x: x["t"]); SELLS = sorted(sellb.values(), key=lambda x: x["t"])
reg = MM.build_layer1(); KN = [x+86400 for x in MM.T]; macro_at = lambda t: reg[bisect.bisect_right(KN, t)-1] if bisect.bisect_right(KN, t)-1 >= 0 else None
def is_sl(p): return p-M_FRAC >= 0 and p+M_FRAC < N and L[p] == min(L[p-M_FRAC:p+M_FRAC+1]) and L[p] < min(L[p-M_FRAC:p])
SLB = [p for p in range(M_FRAC, N-M_FRAC) if is_sl(p)]
print(f"RAW: {N} barras · NAS labels(first-app) {len(NAS)} (LONG {sum(1 for x in NAS if x['dir']=='LONG')}) · buy-bub {len(BUYS)} · sell-bub {len(SELLS)}")
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
def leg_mag(j):
    hb = max(range(max(0, j-LEGWIN), j+1), key=lambda k: H[k]); return (H[hb]-L[j])/(ATR[j] or 5.0)
rows = []; seen = set()
for p in SLB:
    if not (t_lo <= T[p] <= t_hi): continue
    if leg_mag(p) < LEGMIN or not (L[p] <= min(L[max(0, p-192):p+1])+1e-9): continue
    e = reclaim_entry(p)
    if not e or e["ei"] in seen: continue
    seen.add(e["ei"]); ei = e["ei"]; kt = T[ei]; lo, hi = T[max(0, p-16)], kt
    f = {"o": e["o"], "gt": any(abs(T[p]-g) < 6*3600 for g in GT), "dt": ds(T[p])}
    # CONFLUÊNCIA (todos causais, known_at<=entrada)
    f["nas_long"] = sum(1 for x in NAS if x["dir"] == "LONG" and x["ka"] and lo <= x["ka"] <= kt)     # cluster LONG
    f["nas_short"] = sum(1 for x in NAS if x["dir"] == "SHORT" and x["ka"] and lo <= x["ka"] <= kt)
    f["sell_climax"] = sum(x["size"] for x in SELLS if x["ka"] and x["ka"] <= kt and T[max(0, p-8)] <= x["t"] <= T[p])   # venda no flush
    f["buy_absorb"] = sum(x["size"] for x in BUYS if x["ka"] and x["ka"] <= kt and T[p] <= x["t"] <= kt)                 # compra no/pós low
    f["nas_dist"] = min([SV.get(T[i], {}).get("nas_dist") for i in range(bisect.bisect_left(T, lo), p+1) if SV.get(T[i], {}).get("nas_dist") is not None] or [0])
    f["regbull"] = 1 if any((SV.get(T[i], {}).get("regbull") or 0) > 0 for i in range(bisect.bisect_left(T, lo), bisect.bisect_right(T, kt))) else 0
    f["rsi"] = SV.get(T[p], {}).get("rsi") or 50
    rows.append(f)
V2 = [r for r in rows if r["o"] in ("WIN", "LOSS")]; W = [r for r in V2 if r["o"] == "WIN"]; Lo = [r for r in V2 if r["o"] == "LOSS"]
print(f"\nPOPULAÇÃO: N={len(V2)} · WIN {len(W)} ({100*len(W)/len(V2):.0f}%) · LOSS {len(Lo)} · GT {sum(1 for r in rows if r['gt'])}/5\n")
print("5 GT (confluência bruta):")
for r in [x for x in rows if x["gt"]]:
    print(f"  {r['dt']} {r['o']:4} NASlong{r['nas_long']:>3} NASshort{r['nas_short']:>3} SELLclimax{r['sell_climax']:>3} BUYabsorb{r['buy_absorb']:>3} nasdist{r['nas_dist']:.1f} regbull{r['regbull']} rsi{r['rsi']:.0f}")
# medianas WIN vs LOSS
print(f"\n{'feature':13} {'WIN med':>8} {'LOSS med':>8} {'GTmed':>7}")
GTr = [r for r in V2 if r["gt"]]
for k in ("nas_long", "nas_short", "sell_climax", "buy_absorb", "nas_dist", "rsi"):
    print(f"  {k:13} {statistics.median([r[k] for r in W]):>8.1f} {statistics.median([r[k] for r in Lo]):>8.1f} {statistics.median([r[k] for r in GTr]) if GTr else 0:>7.1f}")
# CONFLUÊNCIA: score de convergência (assinatura GT: NAS-long cluster + sell-climax + oversold + div)
def hit(sub): w = sum(1 for r in sub if r["o"] == "WIN"); return w, len(sub), (100*w/len(sub) if sub else 0)
print("\n=== CONFLUÊNCIA (convergência — assinatura GT) ===")
def sc(r): return sum([r["nas_long"] >= 3, r["sell_climax"] >= 15, r["nas_dist"] <= -4, r["regbull"] == 1])
for r in V2: r["score"] = sc(r)
for s in range(0, 5):
    sub = [r for r in V2 if r["score"] == s]; w, n, h = hit(sub); ng = sum(1 for r in sub if r["gt"])
    print(f"  score=={s}: N={n:>2} hit-3R {h:>4.0f}% ({w}/{n}) GT {ng}")
for s in (2, 3, 4):
    sub = [r for r in V2 if r["score"] >= s]; w, n, h = hit(sub); ng = sum(1 for r in sub if r["gt"])
    print(f"  score>={s}: N={n:>2} hit-3R {h:>4.0f}% ({w}/{n}) GT {ng}/5")
print("\n=== COMBOS específicos ===")
for label, cond in [
    ("NASlong>=3 & sellclimax>=15", lambda r: r["nas_long"] >= 3 and r["sell_climax"] >= 15),
    ("NASlong>=3 & sellclimax>=15 & regbull", lambda r: r["nas_long"] >= 3 and r["sell_climax"] >= 15 and r["regbull"] == 1),
    ("NASlong>=4 & sellclimax>=17", lambda r: r["nas_long"] >= 4 and r["sell_climax"] >= 17),
    ("sellclimax>=17 & oversold<=-4", lambda r: r["sell_climax"] >= 17 and r["nas_dist"] <= -4),
    ("NASlong>=3 & oversold<=-4 & regbull", lambda r: r["nas_long"] >= 3 and r["nas_dist"] <= -4 and r["regbull"] == 1)]:
    sub = [r for r in V2 if cond(r)]; w, n, h = hit(sub); ng = sum(1 for r in sub if r["gt"])
    extras = [r["dt"] for r in sub if not r["gt"] and r["o"] == "WIN"]
    print(f"  {label:<40} N={n:>2} hit-3R {h:>4.0f}% ({w}/{n}) GT{ng}/5 | extra-WIN {extras}")