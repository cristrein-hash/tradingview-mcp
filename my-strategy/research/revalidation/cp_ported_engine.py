#!/usr/bin/env python3
"""ENGINE Cp PORTADO (Cris 2026-07-15) — porte causal dos engines de fundo anteriores, na ORDEM certa:
ESTRUTURA → EVENTO(select-first) → ENTRADA(E5/E6) → INDICADORES(risk-shape) → VALIDAÇÃO. RAW-only 15M do
HD (sem primitives). Correções vs os originais (doc BOTTOM_ENGINE_LOGIC_REFERENCE):
 - cascade CLOSE-ONLY da estrutura de preço (NÃO do label SMC repintante) — resolve a ressalva do DA.
 - regime diário recua-um-dia; labels por known_at/born_t; SL≤entrada; 3R first-touch no horizonte.
Entrada portada = E5/E6: cascade>=3-4 (flush profundo) + reclaim (close>high[-1] & close>open) + higher-low
(o flush-low SEGUROU) + oversold (RSI<=40). Detector de fundo causal = estrutura (regime+is_leg_bottom+
retr_up terços) faz o select-event-first. Valida por estágio + streak + por-ano + null + 5 GT capitulação."""
import gzip, json, bisect, statistics, datetime as dt
from pathlib import Path
import sys; HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE))
sys.path.insert(0, "/Users/cristrein/tradingview-mcp/my-strategy/core"); import raw_reader as RR
import macro_structural_v3 as MM
RAW = Path("/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/15M")
BLOCKS = ["XAUUSD_15m_replay_2025-11-25_to_2026-02-25.jsonl.gz",
          "XAUUSD_15m_replay_2026-02-25_to_2026-05-25_rerun_customOBbaseline.jsonl.gz",
          "XAUUSD_15m_replay_2026-05-25_to_2026-07-04.jsonl.gz"]
ds = lambda t: dt.datetime.utcfromtimestamp(int(t)).strftime("%Y-%m-%d %H:%M")
grp = RR.study
def fnum(x):
    try: return float(str(x).replace("−", "-"))
    except Exception: return None
def iso2ep(x):
    try: return int(dt.datetime.fromisoformat(x.replace("Z", "+00:00")).timestamp())
    except Exception: return None
M_FRAC = 3; HMAX = 480; CASC_WIN = 192

# ---- RAW walk (série + RSI + zonas born_t + bubbles known_at) ----
bars = {}; rsi_t = {}; zones = {}; bub = {}
for blk_i, blk in enumerate(BLOCKS):
    snaps = RR.records(RAW/blk)
    for r in snaps:
        oh = r.get("ohlcv") or []; cur = oh[-1]["time"] if oh and isinstance(oh[-1], dict) else None
        for b in oh:
            if isinstance(b, dict) and b.get("time") is not None:
                bars[b["time"]] = {"o": b["open"], "h": b["high"], "l": b["low"], "c": b["close"]}
        rv = grp(r, "study_values", "Relative Strength")
        if rv and cur is not None: rsi_t[cur] = fnum((rv.get("values") or {}).get("RSI"))
        ob = grp(r, "pine_boxes", "Custom OB")
        for bx in (ob.get("all_boxes") if ob else []) or []:
            zid = bx.get("id")
            if zid is None: continue
            zk = (blk_i, zid)
            if zk not in zones: zones[zk] = {"text": str(bx.get("text", "")).upper(), "high": bx.get("high"), "low": bx.get("low"), "born_t": cur}
            else: zones[zk]["high"] = bx.get("high"); zones[zk]["low"] = bx.get("low")
        pb = r.get("pine_shapes_bubbles")
        if pb:
            ka = iso2ep(r.get("replay_current_dt") or ""); BUY = {"plot_0": 1, "plot_2": 2, "plot_4": 3}
            for act in (pb[0].get("activations") or []):
                tt = act.get("time")
                for plot in (act.get("shapes") or {}):
                    if plot in BUY and (tt, plot) not in bub: bub[(tt, plot)] = {"t": tt, "size": BUY[plot], "known_at": ka}
T = sorted(bars); O = [bars[t]["o"] for t in T]; H = [bars[t]["h"] for t in T]; L = [bars[t]["l"] for t in T]; C = [bars[t]["c"] for t in T]
N = len(T); ATR = [None]*N; ema = None; kE = 2/22; trs = []
for i in range(N):
    if i > 0: trs.append(max(H[i]-L[i], abs(H[i]-C[i-1]), abs(L[i]-C[i-1])))
    ATR[i] = sum(trs[-14:])/14 if len(trs) >= 14 else None
RSI = [rsi_t.get(t) for t in T]; buys = sorted(bub.values(), key=lambda x: x["t"])
# dia p/ regime (recua-um-dia) + retr_up
days = {}
for i in range(N):
    dk = T[i]//86400; g = days.setdefault(dk, {"h": H[i], "l": L[i], "t": dk*86400})
    g["h"] = max(g["h"], H[i]); g["l"] = min(g["l"], L[i])
DK = sorted(days); DT = [days[k]["t"] for k in DK]; DH = [days[k]["h"] for k in DK]; DL = [days[k]["l"] for k in DK]
reg = MM.build_layer1(); KN1 = [x+86400 for x in MM.T]
macro_at = lambda t0: reg[bisect.bisect_right(KN1, t0)-1] if bisect.bisect_right(KN1, t0)-1 >= 0 else None
print(f"RAW: {N} barras {ds(T[0])}→{ds(T[-1])} · zonas {len(zones)} · bubbles {len(buys)}")

# ---- ESTRUTURA: swing-lows/highs fractais causais (confirmados em p+m) ----
def is_sl(p): return p-M_FRAC >= 0 and p+M_FRAC < N and L[p] == min(L[p-M_FRAC:p+M_FRAC+1]) and L[p] < min(L[p-M_FRAC:p])
def is_sh(p): return p-M_FRAC >= 0 and p+M_FRAC < N and H[p] == max(H[p-M_FRAC:p+M_FRAC+1]) and H[p] > max(H[p-M_FRAC:p])
SLB = [p for p in range(M_FRAC, N-M_FRAC) if is_sl(p)]
SHB = [p for p in range(M_FRAC, N-M_FRAC) if is_sh(p)]
# cascade CLOSE-ONLY: run de lower-lows consecutivos terminando em cada swing-low
casc = {}; prev = None; run = 0
for p in SLB:
    run = run+1 if (prev is not None and L[p] < L[prev]) else 1
    casc[p] = run; prev = p
def swing_high_before(j):
    i = bisect.bisect_left(SHB, j)-1
    return H[SHB[i]] if i >= 0 else None
def retr_up(j):
    di = bisect.bisect_right(DT, T[j]-86400)-1
    if di < 25: return None
    seg = range(max(0, di-126), di+1); loi = min(seg, key=lambda i: DL[i]); hia = max(range(loi, di+1), key=lambda i: DH[i]) if loi < di else di
    up = DH[hia]-DL[loi]
    return (DH[hia]-L[j])/up if up > 0 else None

# ---- INDICADORES (risk-shape) causais ----
def indic(j, ei):
    atr = ATR[j] or 5.0; kt = T[ei]
    lows = [L[p] for p in SLB if p < j and p >= j-64]
    sweep = lows and L[j] < min(lows)-0.1*atr
    buy = sum(x["size"] for x in buys if x["known_at"] and x["known_at"] <= kt and T[max(0, j-16)] <= x["t"] <= kt) >= 3
    dem = any("DEMAND" in z["text"] and z["born_t"] and z["born_t"] <= T[j] and z["low"] is not None and z["low"] <= L[j] <= z["high"] for z in zones.values())
    # not-knife: downleg efficiency (net drop / path) baixo = controlado; aqui usamos velocidade do flush
    return sum([bool(sweep), buy, dem])

# ---- ENTRADA E5/E6 (cascade + reclaim + hl + oversold), causal ----
def entry_e56(p, casc_min):
    """p = swing-low fractal (flush low), confirmado em p+M. Procura reclaim que segura, cascade>=min."""
    if casc.get(p, 0) < casc_min: return None
    r_at = RSI[p]
    if r_at is None or r_at > 40: return None                       # oversold
    flush_low = L[p]; atr = ATR[p] or 5.0; sl = round(flush_low-0.1*atr, 2)
    sh = swing_high_before(p)
    start = p+M_FRAC                                                 # causal: só após confirmação do fractal
    made_hl = False
    for k in range(start, min(N, p+96)):
        if L[k] <= sl: return None                                  # perdeu o flush-low antes de virar = faca
        if k > p and is_sl(k-M_FRAC) and L[k-M_FRAC] > flush_low: made_hl = True   # higher-low formou
        recl = C[k] > H[k-1] and C[k] > O[k]                        # reclaim
        if recl and made_hl:
            ent = C[k]; r = ent-sl
            if r <= 0.05*atr: continue
            tgt = ent+3*r; o = "OPEN"
            for m in range(k+1, min(N, k+HMAX+1)):
                if L[m] <= sl: o = "LOSS"; break
                if H[m] >= tgt: o = "WIN"; break
            return {"ei": k, "j": p, "ent": ent, "sl": sl, "R": round(r, 2), "o": o, "lag": k-p}
    return None

# ---- PIPELINE + VALIDAÇÃO ----
GT = []
for a, b in [(1770015600, 1770210000), (1770339600, 1771448400), (1774242000, 1774270800), (1781128800, 1781128800), (1782781200, 1782907200)]:
    aa = bisect.bisect_left(T, min(a, b)-12*3600); bb = bisect.bisect_right(T, max(a, b)+12*3600)
    if aa < bb: GT.append(T[min(range(aa, bb), key=lambda k: L[k])])
t_lo = int(dt.datetime(2026, 2, 1, tzinfo=dt.timezone.utc).timestamp()); t_hi = int(dt.datetime(2026, 7, 4, tzinfo=dt.timezone.utc).timestamp())

def run(casc_min, struct_gate, ind_min):
    rows = []; seen = set()
    for p in SLB:
        if not (t_lo <= T[p] <= t_hi): continue
        e = entry_e56(p, casc_min)
        if not e or e["ei"] in seen: continue
        if struct_gate:
            rg = macro_at(T[p]); ru = retr_up(p); is_lb = L[p] <= min(L[max(0, p-192):p+1])+1e-9
            if not (rg in ("BEAR", "RANGE") and is_lb and ru is not None and ru >= 0.45): continue
        if ind_min and indic(p, e["ei"]) < ind_min: continue
        seen.add(e["ei"])
        e["yr"] = dt.datetime.utcfromtimestamp(T[p]).year; e["gt"] = any(abs(T[p]-g) < 6*3600 for g in GT)
        rows.append(e)
    return rows

def report(name, rows):
    v = [r for r in rows if r["o"] in ("WIN", "LOSS")]; w = sum(1 for r in v if r["o"] == "WIN")
    hit = 100*w/len(v) if v else 0; net = sum((3 if r["o"] == "WIN" else -1) for r in v)
    # streak de losses
    eq = pk = dd = strk = mx = 0
    for r in v:
        x = 3 if r["o"] == "WIN" else -1; eq += x; pk = max(pk, eq); dd = min(dd, eq-pk)
        strk = strk+1 if x < 0 else 0; mx = min(mx, -strk)
    yrs = {y: report_year(v, y) for y in sorted(set(r["yr"] for r in v))}
    ng = sum(1 for r in rows if r["gt"])
    print(f"  {name:<44} N={len(v):>3} hit3R {hit:>4.0f}% NET {net:>+5}R DD {dd:>+4}R streak {mx:>3} GT{ng}/5 | {yrs}")
def report_year(v, y):
    vv = [r for r in v if r["yr"] == y]; w = sum(1 for r in vv if r["o"] == "WIN")
    return f"{y}:{w}/{len(vv)}"

print("\n=== ENGINE Cp PORTADO — pipeline por estágio (2026 bear) ===")
report("STAGE A entrada E5/E6 casc>=3 (SÓ entrada)", run(3, False, 0))
report("STAGE A' casc>=4", run(4, False, 0))
report("STAGE B +ESTRUTURA (BEAR_reversal gate)", run(3, True, 0))
report("STAGE C +INDICADORES risk-shape>=1", run(3, True, 1))
report("STAGE C' casc>=4 +estrutura +ind>=1", run(4, True, 1))
# baseline null: todas as swing-lows oversold com reclaim (sem cascade)
rn = run(1, False, 0); report("NULL (casc>=1 = qualquer reclaim oversold)", rn)