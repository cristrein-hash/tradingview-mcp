#!/usr/bin/env python3
"""Cp MAPA COMPLETO DE INDICADORES (Cris 2026-07-15) — deixei de fora informação valiosa. Extrai TODOS
os study_values causais do RAW e mapeia WIN-vs-LOSS na população correta (43 fundos-de-perna-significativa):
 NAS TOP BOTTOM DETECTOR: NAS_DISTANCE_FROM_EMA_ATR (oversold) · NAS_RSI · NAS_BOTTOM_SIGNAL/NAS_LONG_SIGNAL
   (o detector de fundo dedicado a disparar) · NAS_TOP_SIGNAL.
 RSI: RSI · RSI-based MA (RSI-vs-MA) · Regular Bullish (divergência do próprio indicador).
 Market Order Bubbles: Shapes. SMC: PlotCandle (estado/direção).
Tudo por-bar (study_values = valor da barra corrente do snapshot = causal). Reporta WIN-vs-LOSS + GT + null."""
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
M_FRAC, LEGWIN, HMAX, LEGMIN = 3, 480, 480, 15
BLOCKS = ["XAUUSD_15m_replay_2025-11-25_to_2026-02-25.jsonl.gz",
          "XAUUSD_15m_replay_2026-02-25_to_2026-05-25_rerun_customOBbaseline.jsonl.gz",
          "XAUUSD_15m_replay_2026-05-25_to_2026-07-04.jsonl.gz"]
bars = {}; SV = {}   # SV[t] = dict de indicadores da barra t
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
        nas = (grp(r, "study_values", "NAS") or {}).get("values") or {}
        rsi = (grp(r, "study_values", "Relative") or {}).get("values") or {}
        mob = (grp(r, "study_values", "Market Order") or {}).get("values") or {}
        SV[cur] = {"nas_dist": fnum(nas.get("NAS_DISTANCE_FROM_EMA_ATR")), "nas_rsi": fnum(nas.get("NAS_RSI")),
                   "nas_long": fnum(nas.get("NAS_LONG_SIGNAL")), "nas_bottom": fnum(nas.get("NAS_BOTTOM_SIGNAL")),
                   "rsi": fnum(rsi.get("RSI")), "rsi_ma": fnum(rsi.get("RSI-based MA")), "regbull": fnum(rsi.get("Regular Bullish")),
                   "mob": fnum(mob.get("Shapes"))}
T = sorted(bars); O = [bars[t]["o"] for t in T]; H = [bars[t]["h"] for t in T]; L = [bars[t]["l"] for t in T]; C = [bars[t]["c"] for t in T]
N = len(T); ATR = [None]*N; trs = []
for i in range(N):
    if i > 0: trs.append(max(H[i]-L[i], abs(H[i]-C[i-1]), abs(L[i]-C[i-1])))
    ATR[i] = sum(trs[-14:])/14 if len(trs) >= 14 else None
reg = MM.build_layer1(); KN = [x+86400 for x in MM.T]; macro_at = lambda t: reg[bisect.bisect_right(KN, t)-1] if bisect.bisect_right(KN, t)-1 >= 0 else None
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
def leg_mag(j):
    hb = max(range(max(0, j-LEGWIN), j+1), key=lambda k: H[k]); return (H[hb]-L[j])/(ATR[j] or 5.0)
def sv_win(t0, t1, key, agg):
    vals = [SV[T[i]][key] for i in range(bisect.bisect_left(T, t0), bisect.bisect_right(T, t1)) if SV.get(T[i], {}).get(key) is not None]
    return agg(vals) if vals else None

rows = []; seen = set()
for p in SLB:
    if not (t_lo <= T[p] <= t_hi): continue
    if leg_mag(p) < LEGMIN or not (L[p] <= min(L[max(0, p-192):p+1])+1e-9): continue
    e = reclaim_entry(p)
    if not e or e["ei"] in seen: continue
    seen.add(e["ei"]); ei = e["ei"]; kt = T[ei]; lt = T[p]
    f = {"o": e["o"], "gt": any(abs(T[p]-g) < 6*3600 for g in GT), "dt": ds(T[p])}
    # reads causais (janela [low-8, entry], tudo <= entrada)
    f["nas_dist_min"] = sv_win(T[max(0, p-8)], lt, "nas_dist", min)              # mais oversold ate ao low
    f["nas_rsi"] = SV.get(lt, {}).get("nas_rsi")
    f["nas_bottom_fired"] = 1 if (sv_win(T[max(0, p-4)], kt, "nas_bottom", max) or 0) > 0 else 0
    f["nas_long_fired"] = 1 if (sv_win(T[max(0, p-4)], kt, "nas_long", max) or 0) > 0 else 0
    f["rsi_at"] = SV.get(lt, {}).get("rsi"); f["rsi_ma_at"] = SV.get(lt, {}).get("rsi_ma")
    f["rsi_belowma"] = 1 if (f["rsi_at"] is not None and f["rsi_ma_at"] is not None and f["rsi_at"] < f["rsi_ma_at"]) else 0
    f["rsi_reclaim_ma"] = 1 if (SV.get(kt, {}).get("rsi") is not None and SV.get(kt, {}).get("rsi_ma") is not None and SV[kt]["rsi"] > SV[kt]["rsi_ma"]) else 0
    f["regbull_fired"] = 1 if (sv_win(T[max(0, p-8)], kt, "regbull", max) or 0) > 0 else 0    # divergência do indicador
    f["mob_buy"] = 1 if (sv_win(T[max(0, p-8)], kt, "mob", max) or 0) > 0 else 0
    rows.append(f)
V2 = [r for r in rows if r["o"] in ("WIN", "LOSS")]; W = [r for r in V2 if r["o"] == "WIN"]; Lo = [r for r in V2 if r["o"] == "LOSS"]
print(f"POPULAÇÃO: N={len(V2)} · WIN {len(W)} ({100*len(W)/len(V2):.0f}%) · LOSS {len(Lo)} · GT {sum(1 for r in rows if r['gt'])}/5\n")
CONT = ["nas_dist_min", "nas_rsi", "rsi_at", "rsi_ma_at"]
BOOL = ["nas_bottom_fired", "nas_long_fired", "rsi_belowma", "rsi_reclaim_ma", "regbull_fired", "mob_buy"]
print(f"{'indicador (contínuo)':22} {'WIN med':>8} {'LOSS med':>8}")
for k in CONT:
    wv = [r[k] for r in W if r[k] is not None]; lv = [r[k] for r in Lo if r[k] is not None]
    if wv and lv: print(f"  {k:22} {statistics.median(wv):>8.2f} {statistics.median(lv):>8.2f}")
print(f"\n{'indicador (fire %)':22} {'WIN fire%':>9} {'LOSS fire%':>10} {'hit-3R quando fire':>18}")
for k in BOOL:
    wf = 100*sum(r[k] for r in W)/len(W); lf = 100*sum(r[k] for r in Lo)/len(Lo)
    sub = [r for r in V2 if r[k] == 1]; hit = 100*sum(1 for r in sub if r["o"] == "WIN")/len(sub) if sub else 0
    print(f"  {k:22} {wf:>8.0f}% {lf:>9.0f}% {f'{hit:.0f}% (N={len(sub)})':>18}")
print("\n5 GT (indicadores):")
for r in [x for x in rows if x["gt"]]:
    print(f"  {r['dt']} {r['o']:4} nasdist{r['nas_dist_min']} nasrsi{r['nas_rsi']} nasBot{r['nas_bottom_fired']} nasLong{r['nas_long_fired']} rsi{r['rsi_at']} belowMA{r['rsi_belowma']} reclaimMA{r['rsi_reclaim_ma']} regbull{r['regbull_fired']} mob{r['mob_buy']}")