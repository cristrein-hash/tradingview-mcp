#!/usr/bin/env python3
"""Cp DISCRIMINAÇÃO PROFUNDA (Cris 2026-07-15) — na população CORRETA (fundos-de-perna-significativa,
legMag>=15x + is_leg_bottom, ~45 na bear 2026), testa TODAS as características + TODOS os indicadores
RAW causais para separar os 5 GT reais dos ~35 falsos (que continuaram a cair). Multi-fatorial +
trajetória, não eixo-único. Objetivo duplo: apanhar o fundo real E evitar a faca.
CARACTERÍSTICAS: velocidade/clímax · esforço/volume · sweep+reclaim · força-da-reversão · divergência.
INDICADORES RAW (known_at/born_t causais): RSI(nível/min/div) · NAS-long · SMC-CHoCH(close-only) ·
buy-absorção/sell-exaustão(bubbles) · zona demand. Reporta WIN-vs-LOSS por feature + convergência +
onde caem os 5 GT + null base. RAW 15M do HD, sem primitives."""
import gzip, json, bisect, statistics, datetime as dt
from pathlib import Path
import sys; HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE))
import macro_structural_v3 as MM
ds = lambda t: dt.datetime.utcfromtimestamp(int(t)).strftime("%Y-%m-%d %H:%M")
grp = lambda rec, k, s: next((x for x in (rec.get(k) or []) if s.lower() in str(x.get("name", "")).lower()), None)
def fnum(x):
    try: return float(str(x).replace("−", "-"))
    except Exception: return None
def iso2ep(x):
    try: return int(dt.datetime.fromisoformat(x.replace("Z", "+00:00")).timestamp())
    except Exception: return None
M_FRAC, LEGWIN, HMAX, LEGMIN = 3, 480, 480, 15
BLOCKS = ["XAUUSD_15m_replay_2025-11-25_to_2026-02-25.jsonl.gz",
          "XAUUSD_15m_replay_2026-02-25_to_2026-05-25_rerun_customOBbaseline.jsonl.gz",
          "XAUUSD_15m_replay_2026-05-25_to_2026-07-04.jsonl.gz"]
bars = {}; rsi_t = {}; nas_ev = []; smc_ev = []; zones = {}; bbuy = {}; bsell = {}
for blk_i, blk in enumerate(BLOCKS):
    mnas = msmc = -1; nasi = smci = False; snaps = []
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
                bars[b["time"]] = {"o": b["open"], "h": b["high"], "l": b["low"], "c": b["close"], "v": b.get("volume") or 0}
        rv = grp(r, "study_values", "Relative Strength")
        if rv and cur is not None: rsi_t[cur] = fnum((rv.get("values") or {}).get("RSI"))
        ng = grp(r, "pine_labels", "NAS"); ngi = [l.get("id") for l in (ng.get("labels") or []) if l.get("id") is not None] if ng else []
        if not nasi:
            if ngi: mnas = max(ngi); nasi = True
        else:
            for l in (ng.get("labels") or []) if ng else []:
                if l.get("id") is not None and l["id"] > mnas and "LONG" in str(l.get("text", "")).upper(): nas_ev.append(cur)
            if ngi: mnas = max(mnas, max(ngi))
        sg = grp(r, "pine_labels", "Smart Money"); sgi = [l.get("id") for l in (sg.get("labels") or []) if l.get("id") is not None] if sg else []
        if not smci:
            if sgi: msmc = max(sgi); smci = True
        else:
            for l in (sg.get("labels") or []) if sg else []:
                if l.get("id") is not None and l["id"] > msmc: smc_ev.append({"t": cur, "text": str(l.get("text", "")).upper()})
            if sgi: msmc = max(msmc, max(sgi))
        ob = grp(r, "pine_boxes", "Custom OB")
        for bx in (ob.get("all_boxes") if ob else []) or []:
            if bx.get("id") is None: continue
            zk = (blk_i, bx["id"])
            if zk not in zones: zones[zk] = {"text": str(bx.get("text", "")).upper(), "high": bx.get("high"), "low": bx.get("low"), "born_t": cur}
            else: zones[zk]["high"] = bx.get("high"); zones[zk]["low"] = bx.get("low")
        pb = r.get("pine_shapes_bubbles")
        if pb:
            ka = iso2ep(r.get("replay_current_dt") or ""); BUY = {"plot_0": 1, "plot_2": 2, "plot_4": 3}; SELL = {"plot_6": 1, "plot_8": 2, "plot_10": 3}
            for act in (pb[0].get("activations") or []):
                tt = act.get("time")
                for plot in (act.get("shapes") or {}):
                    if plot in BUY and (tt, plot) not in bbuy: bbuy[(tt, plot)] = {"t": tt, "size": BUY[plot], "known_at": ka}
                    if plot in SELL and (tt, plot) not in bsell: bsell[(tt, plot)] = {"t": tt, "size": SELL[plot], "known_at": ka}
T = sorted(bars); O = [bars[t]["o"] for t in T]; H = [bars[t]["h"] for t in T]; L = [bars[t]["l"] for t in T]; C = [bars[t]["c"] for t in T]; V = [bars[t]["v"] for t in T]
N = len(T); ATR = [None]*N; trs = []
for i in range(N):
    if i > 0: trs.append(max(H[i]-L[i], abs(H[i]-C[i-1]), abs(L[i]-C[i-1])))
    ATR[i] = sum(trs[-14:])/14 if len(trs) >= 14 else None
RSI = [rsi_t.get(t) for t in T]; BUYS = sorted(bbuy.values(), key=lambda x: x["t"]); SELLS = sorted(bsell.values(), key=lambda x: x["t"])
reg = MM.build_layer1(); KN = [x+86400 for x in MM.T]; macro_at = lambda t: reg[bisect.bisect_right(KN, t)-1] if bisect.bisect_right(KN, t)-1 >= 0 else None
def is_sl(p): return p-M_FRAC >= 0 and p+M_FRAC < N and L[p] == min(L[p-M_FRAC:p+M_FRAC+1]) and L[p] < min(L[p-M_FRAC:p])
def is_sh(p): return p-M_FRAC >= 0 and p+M_FRAC < N and H[p] == max(H[p-M_FRAC:p+M_FRAC+1]) and H[p] > max(H[p-M_FRAC:p])
SLB = [p for p in range(M_FRAC, N-M_FRAC) if is_sl(p)]; SHB = [p for p in range(M_FRAC, N-M_FRAC) if is_sh(p)]
print(f"RAW: {N} barras · vol>0 {sum(1 for v in V if v)>0} · NAS {len(nas_ev)} · SMC {len(smc_ev)} · zonas {len(zones)} · buy-bub {len(BUYS)} sell-bub {len(SELLS)}")
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
            return {"ei": k, "o": o, "R": r}
    return None

def feats(j, ei):
    atr = ATR[j] or 5.0; f = {}
    # VELOCIDADE/CLÍMAX
    f["vel8"] = round((C[j-8]-C[j])/atr, 2) if j >= 8 else 0        # queda em 8b (positivo=queda rápida)
    f["vel16"] = round((C[j-16]-C[j])/atr, 2) if j >= 16 else 0
    hb = max(range(max(0, j-LEGWIN), j+1), key=lambda k: H[k]); dur = max(1, j-hb)
    leg_vel = (H[hb]-L[j])/atr/dur                                  # velocidade média da perna
    f["climax"] = round(((C[j-8]-C[j])/atr/8)/max(0.01, leg_vel), 2)  # flush vs média da perna (>1=clímax)
    f["atr_spike"] = round(atr/(ATR[j-20] or atr), 2)
    # ESFORÇO/VOLUME
    vavg = statistics.mean([V[k] for k in range(max(0, j-20), j) if V[k]]) if any(V[max(0, j-20):j]) else 0
    f["vol_spike"] = round(V[j]/vavg, 2) if vavg else 0
    # SWEEP + RECLAIM
    plows = [L[p] for p in SLB if p < j-M_FRAC and p >= j-64]
    f["sweep"] = round((min(plows)-L[j])/atr, 2) if plows and L[j] < min(plows) else 0
    f["recl_lag"] = ei-j; f["recl_strength"] = round((C[ei]-L[j])/atr, 2)
    # FORÇA DA REVERSÃO (bounce nos primeiros 16b)
    hi16 = max(H[j:min(N, j+16)]); f["rev_strength"] = round((hi16-L[j])/atr, 2)
    # DIVERGÊNCIA + RSI
    r_now = RSI[j]; f["rsi"] = round(r_now, 1) if r_now else None
    f["rsi_min8"] = round(min([x for x in RSI[max(0, j-8):j+1] if x] or [50]), 1)
    div = False
    pl = [(p, L[p]) for p in SLB if p < j-M_FRAC and p >= j-96]
    if pl and r_now is not None:
        pp, plo = pl[-1]; rp = RSI[pp]
        if rp is not None and L[j] < plo and r_now > rp: div = True
    f["rsi_div"] = int(div)
    # INDICADORES: buy-absorção / sell-exaustão / NAS / SMC-choch(close-only) / demand
    kt = T[ei]
    f["buy_abs"] = sum(x["size"] for x in BUYS if x["known_at"] and x["known_at"] <= kt and T[max(0, j-16)] <= x["t"] <= kt)
    f["sell_late"] = sum(x["size"] for x in SELLS if x["known_at"] and x["known_at"] <= kt and T[max(0, j-8)] <= x["t"] <= T[j])
    f["nas_long"] = int(any(t and T[max(0, j-8)] <= t <= kt for t in nas_ev))
    i = bisect.bisect_left(SHB, j)-1; sh = H[SHB[i]] if i >= 0 else None
    f["choch_up"] = int(sh is not None and any(C[k] > sh for k in range(j+1, ei+1)))
    f["in_demand"] = int(any("DEMAND" in z["text"] and z["born_t"] and z["born_t"] <= T[j] and z["low"] is not None and z["low"] <= L[j] <= z["high"] for z in zones.values()))
    return f

# construir a população
def leg_mag(j):
    hb = max(range(max(0, j-LEGWIN), j+1), key=lambda k: H[k]); return (H[hb]-L[j])/(ATR[j] or 5.0)
rows = []; seen = set()
for p in SLB:
    if not (t_lo <= T[p] <= t_hi): continue
    if leg_mag(p) < LEGMIN or not (L[p] <= min(L[max(0, p-192):p+1])+1e-9): continue
    e = reclaim_entry(p)
    if not e or e["ei"] in seen: continue
    seen.add(e["ei"]); f = feats(p, e["ei"]); f["o"] = e["o"]; f["gt"] = any(abs(T[p]-g) < 6*3600 for g in GT); f["dt"] = ds(T[p]); rows.append(f)
V2 = [r for r in rows if r["o"] in ("WIN", "LOSS")]; W = [r for r in V2 if r["o"] == "WIN"]; Lo = [r for r in V2 if r["o"] == "LOSS"]
print(f"\nPOPULAÇÃO fundos-de-perna-significativa: N={len(V2)} · WIN {len(W)} ({100*len(W)/len(V2):.0f}%) · LOSS {len(Lo)} · GT {sum(1 for r in rows if r['gt'])}/5")
FEATS = ["vel8", "vel16", "climax", "atr_spike", "vol_spike", "sweep", "recl_lag", "recl_strength", "rev_strength", "rsi", "rsi_min8", "rsi_div", "buy_abs", "sell_late", "nas_long", "choch_up", "in_demand"]
print(f"\n{'feature':13} {'WIN med':>8} {'LOSS med':>8} {'separa?':>9}")
for k in FEATS:
    wm = statistics.median([r[k] for r in W if r[k] is not None]); lm = statistics.median([r[k] for r in Lo if r[k] is not None])
    sep = "SEPARA" if abs(wm-lm) > 0.3*(abs(lm)+abs(wm)+1e-9) else ""
    print(f"  {k:13} {wm:>8.2f} {lm:>8.2f} {sep:>9}")
# melhor limiar univariado + convergência
print("\nmelhor subpop por limiar (marginal hit-3R, N>=6):")
best = []
for k in FEATS:
    vals = sorted(set(round(r[k], 1) for r in V2 if r[k] is not None))
    for thr in vals:
        for sg in (">=", "<="):
            sub = [r for r in V2 if r[k] is not None and (r[k] >= thr if sg == ">=" else r[k] <= thr)]
            if len(sub) < 6: continue
            hr = 100*sum(1 for r in sub if r["o"] == "WIN")/len(sub); best.append((hr, k, sg, thr, len(sub)))
best.sort(reverse=True)
for hr, k, sg, thr, n in best[:6]: print(f"  {k} {sg} {thr}: hit-3R {hr:.0f}% (N={n})")
print("\n5 GT (features):")
for r in [x for x in rows if x["gt"]]:
    print(f"  {r['dt']} {r['o']:4} climax{r['climax']} vol{r['vol_spike']} sweep{r['sweep']} rev{r['rev_strength']} div{r['rsi_div']} buy{r['buy_abs']} nas{r['nas_long']} choch{r['choch_up']} dem{r['in_demand']}")

# ---- CONVERGÊNCIA CAUSAL (vel + sweep + climax, tudo <= entrada; SEM rev_strength lookahead) ----
def hit(sub): w = sum(1 for r in sub if r["o"] == "WIN"); return w, len(sub), (100*w/len(sub) if sub else 0)
print("\n=== CONVERGÊNCIA CAUSAL (proxies da reversão violenta, ANTES da entrada) ===")
for label, cond in [
    ("vel16>=4 & sweep>=2.5", lambda r: r["vel16"] >= 4 and r["sweep"] >= 2.5),
    ("vel16>=4 & sweep>=2.5 & climax>=5", lambda r: r["vel16"] >= 4 and r["sweep"] >= 2.5 and r["climax"] >= 5),
    ("sweep>=2.5 & climax>=5", lambda r: r["sweep"] >= 2.5 and r["climax"] >= 5),
    ("vel16>=4.5 & sweep>=3", lambda r: r["vel16"] >= 4.5 and r["sweep"] >= 3),
    ("climax>=5 & vel16>=4.5", lambda r: r["climax"] >= 5 and r["vel16"] >= 4.5),
    ("sweep>=2.5 & climax>=4 & nas_long", lambda r: r["sweep"] >= 2.5 and r["climax"] >= 4 and r["nas_long"] == 1)]:
    sub = [r for r in V2 if cond(r)]; w, n, h = hit(sub); ng = sum(1 for r in rows if r["gt"] and r["o"] in ("WIN", "LOSS") and cond(r))
    print(f"  {label:<38} N={n:>2} hit-3R {h:>4.0f}% ({w}/{n}) GT-cap {ng}")
print(f"  [base pop 23% · N total {len(V2)}]")