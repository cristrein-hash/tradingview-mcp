#!/usr/bin/env python3
"""Cp FORÇA DA CAPITULAÇÃO via ATIVAÇÃO CUMULATIVA NA PERNA (Cris 2026-07-15) — o sinal NÃO é cluster no
fundo; é a QUANTIDADE de NAS + bubbles (buy-limits ativados) ao longo de TODA a perna de baixa. Muita
demanda absorvida no caminho = exaustão vendedora = capitulação forte que reverte (sem precisar cluster
final; #1/#5 caem rápido e ativam tudo no caminho). Feature de TRAJETÓRIA (cumulativo leg-high→low),
causal. Mapeia por candidato (fundo-de-perna-significativa) e testa se separa os 5 GT dos ~35 falsos."""
import gzip, json, bisect, statistics, datetime as dt
from pathlib import Path
import sys; HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE))
sys.path.insert(0, "/Users/cristrein/tradingview-mcp/my-strategy/core"); import raw_reader as RR
import macro_structural_v3 as MM
ds = lambda t: dt.datetime.utcfromtimestamp(int(t)).strftime("%Y-%m-%d %H:%M")
grp = RR.study
def iso2ep(x):
    try: return int(dt.datetime.fromisoformat(x.replace("Z", "+00:00")).timestamp())
    except Exception: return None
M_FRAC, LEGWIN, HMAX, LEGMIN = 3, 480, 480, 15
BLOCKS = ["XAUUSD_15m_replay_2025-11-25_to_2026-02-25.jsonl.gz",
          "XAUUSD_15m_replay_2026-02-25_to_2026-05-25_rerun_customOBbaseline.jsonl.gz",
          "XAUUSD_15m_replay_2026-05-25_to_2026-07-04.jsonl.gz"]
bars = {}; nas_first = {}; buyb = {}; sellb = {}
for blk in BLOCKS:
    snaps = RR.records(Path("/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/15M")/blk)
    for r in snaps:
        oh = r.get("ohlcv") or []; cur = oh[-1]["time"] if oh and isinstance(oh[-1], dict) else None
        for b in oh:
            if isinstance(b, dict) and b.get("time") is not None: bars[b["time"]] = {"o": b["open"], "h": b["high"], "l": b["low"], "c": b["close"]}
        if cur is None: continue
        ng = grp(r, "pine_labels", "NAS")
        for l in (ng.get("labels") or []) if ng else []:
            lid = l.get("id")
            if lid is None or (blk, lid) in nas_first: continue
            txt = str(l.get("text", "")).upper(); nas_first[(blk, lid)] = {"ka": cur, "dir": "LONG" if "LONG" in txt else ("SHORT" if "SHORT" in txt else "?")}
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
NAT = [x["ka"] for x in NAS]; BT = [x["t"] for x in BUYS]; ST = [x["t"] for x in SELLS]
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
            return {"o": o}
    return None
def cnt(arr, t0, t1): return bisect.bisect_right(arr, t1)-bisect.bisect_left(arr, t0)
def cntsz(bubs, ts, t0, t1): return sum(bubs[i]["size"] for i in range(bisect.bisect_left(ts, t0), bisect.bisect_right(ts, t1)))
rows = []
for p in SLB:
    if not (t_lo <= T[p] <= t_hi): continue
    hb = max(range(max(0, p-LEGWIN), p+1), key=lambda k: H[k]); atr = ATR[p] or 5.0
    if (H[hb]-L[p])/atr < LEGMIN or not (L[p] <= min(L[max(0, p-192):p+1])+1e-9): continue
    e = reclaim_entry(p)
    if not e: continue
    t0, t1, dur = T[hb], T[p], max(1, p-hb)   # perna: leg-high → low
    f = {"o": e["o"], "gt": any(abs(T[p]-g) < 6*3600 for g in GT), "dt": ds(T[p]), "legbars": dur}
    f["leg_nas_long"] = cnt([x["ka"] for x in NAS if x["dir"] == "LONG"], t0, t1)
    f["leg_nas_all"] = cnt(NAT, t0, t1)
    f["leg_buy"] = cntsz(BUYS, BT, t0, t1)          # buy-limits ativados ao longo da perna
    f["leg_sell"] = cntsz(SELLS, ST, t0, t1)
    f["buy_dens"] = round(f["leg_buy"]/dur, 3); f["nas_dens"] = round(f["leg_nas_long"]/dur, 3)
    # AUCTION THEORY: intensidade total do leilão + absorção (demanda vs oferta), normalizada
    legmag = (H[hb]-L[p])/atr
    f["total_act"] = f["leg_buy"]+f["leg_sell"]+f["leg_nas_all"]          # atividade total de ordens
    f["act_per_atr"] = round(f["total_act"]/max(1, legmag), 1)            # atividade por unidade de queda
    f["absorp"] = round(f["leg_buy"]/max(1, f["leg_sell"]), 2)            # demanda/oferta
    f["act_dens"] = round((f["leg_buy"]+f["leg_sell"])/dur, 2)            # densidade order-flow
    rows.append(f)
V2 = [r for r in rows if r["o"] in ("WIN", "LOSS")]; W = [r for r in V2 if r["o"] == "WIN"]; Lo = [r for r in V2 if r["o"] == "LOSS"]; GTr = [r for r in V2 if r["gt"]]
print(f"RAW: NAS {len(NAS)} · buy-bub {len(BUYS)} · sell-bub {len(SELLS)}\nPOPULAÇÃO: N={len(V2)} WIN {len(W)}({100*len(W)/len(V2):.0f}%) GT {sum(1 for r in rows if r['gt'])}/5\n")
print("5 GT (ativação cumulativa na perna):")
for r in [x for x in rows if x["gt"]]:
    print(f"  {r['dt']} {r['o']:4} legbars{r['legbars']:>3} NASlong-leg{r['leg_nas_long']:>3} BUY-leg{r['leg_buy']:>4} SELL-leg{r['leg_sell']:>4} buyDens{r['buy_dens']} nasDens{r['nas_dens']}")
print(f"\n{'feature':13} {'WIN med':>8} {'LOSS med':>8} {'GT med':>7}")
for k in ("leg_nas_long", "leg_nas_all", "leg_buy", "leg_sell", "buy_dens", "nas_dens", "legbars"):
    print(f"  {k:13} {statistics.median([r[k] for r in W]):>8.1f} {statistics.median([r[k] for r in Lo]):>8.1f} {statistics.median([r[k] for r in GTr]) if GTr else 0:>7.1f}")
def hit(sub): w = sum(1 for r in sub if r["o"] == "WIN"); return w, len(sub), (100*w/len(sub) if sub else 0)
print("\n5 GT (AUCTION intensity):")
for r in [x for x in rows if x["gt"]]:
    print(f"  {r['dt']} {r['o']:4} total_act{r['total_act']:>4} act_per_atr{r['act_per_atr']:>6} absorp{r['absorp']:>5} act_dens{r['act_dens']:>5}")
print(f"\n{'auction feat':13} {'WIN med':>8} {'LOSS med':>8} {'GT med':>7}")
for k in ("total_act", "act_per_atr", "absorp", "act_dens"):
    print(f"  {k:13} {statistics.median([r[k] for r in W]):>8.1f} {statistics.median([r[k] for r in Lo]):>8.1f} {statistics.median([r[k] for r in GTr]) if GTr else 0:>7.1f}")
print("\n=== INTENSIDADE-DE-LEILÃO por limiar (força da capitulação) ===")
best = []
for k in ("leg_buy", "buy_dens", "total_act", "act_per_atr", "act_dens", "leg_sell"):
    vals = sorted(set(r[k] for r in V2))
    for thr in vals:
        sub = [r for r in V2 if r[k] >= thr]
        if len(sub) < 6: continue
        w, n, h = hit(sub); ng = sum(1 for r in sub if r["gt"]); best.append((h, k, thr, n, w, ng))
best.sort(reverse=True)
for h, k, thr, n, w, ng in best[:6]: print(f"  {k}>={thr}: hit-3R {h:.0f}% ({w}/{n}) GT {ng}/5")
print("\n=== CONFLUÊNCIA auction (absorção-compradora OU nas+venda-pesada) ===")
for label, cond in [
    ("act_per_atr>=8 (leilão intenso/queda)", lambda r: r["act_per_atr"] >= 8),
    ("act_dens>=0.5 (order-flow denso)", lambda r: r["act_dens"] >= 0.5),
    ("buy_dens>=0.25 OR leg_sell>=180", lambda r: r["buy_dens"] >= 0.25 or r["leg_sell"] >= 180),
    ("total_act>=200 & act_dens>=0.4", lambda r: r["total_act"] >= 200 and r["act_dens"] >= 0.4)]:
    sub = [r for r in V2 if cond(r)]; w, n, h = hit(sub); ng = sum(1 for r in sub if r["gt"])
    extra = [r["dt"] for r in sub if not r["gt"] and r["o"] == "WIN"]
    print(f"  {label:<40} N={n:>2} hit-3R {h:>4.0f}% ({w}/{n}) GT{ng}/5 extra-WIN{extra}")