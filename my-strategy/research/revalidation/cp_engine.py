#!/usr/bin/env python3
"""ENGINE Cp COMPLETO — capitulação em BEAR, ORDEM: ESTRUTURA → CONTEXTO(terços) → INDICADORES → ENTRY.
Filosofia resgatada (bottom_detector_structural 2026-07-07, correção Cris "nunca snapshot sem estrutura";
Engine 7 top-prohibition; ordering "select bottom-event first"). NÃO indicadores primeiro (erro da sessão).

PIPELINE (cada estágio mede o lift vs null 22%):
 STAGE 0  null   = todos os flushes-capitulação (range>=1.8x, down) na bear 2026 + MB3 3R.
 STAGE 1  ESTRUTURA (regime detector aprovado): classe BEAR_reversal = macro BEAR/RANGE + is_leg_bottom
          (o low É o fundo da perna, menor low desde o último swing-high) + retr_up>=0.45 (retração
          PROFUNDA da perna macro de alta = bottom third; os terços TOP/MIDDLE/BOTTOM).
 STAGE 2  EVENT (not-knife): choch_up = a perna de baixa QUEBROU estrutura p/ cima (close acima do último
          swing-high antes do low, até à entrada) = a perna de baixa terminou (select bottom-event first).
 STAGE 3  INDICADORES (RAW, DEPOIS da estrutura): confluência buy-absorção/NAS/RSI-div/demand.
 ENTRY    MB3 + SL low-real + 3R (a1_causal_entry, auditado sem lookahead). Marca onde caem os 5 GT.
RAW 15M direto do HD, SEM primitives (regra Cris). macro_structural_v3 = regime aprovado."""
import gzip, json, bisect, statistics, datetime as dt
from pathlib import Path
import sys; HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE))
import macro_structural_v3 as MM
from a1_causal_entry import causal_entry, _is_swinglow, M_FRAC, LOWBACK
RAW = Path("/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/15M")
BLOCKS = ["XAUUSD_15m_replay_2025-11-25_to_2026-02-25.jsonl.gz",
          "XAUUSD_15m_replay_2026-02-25_to_2026-05-25_rerun_customOBbaseline.jsonl.gz",
          "XAUUSD_15m_replay_2026-05-25_to_2026-07-04.jsonl.gz"]
ds = lambda t: dt.datetime.utcfromtimestamp(int(t)).strftime("%Y-%m-%d %H:%M")
grp = lambda rec, k, s: next((x for x in (rec.get(k) or []) if s.lower() in str(x.get("name", "")).lower()), None)
def fnum(x):
    try: return float(str(x).replace("−", "-"))
    except Exception: return None
def iso2ep(x):
    try: return int(dt.datetime.fromisoformat(x.replace("Z", "+00:00")).timestamp())
    except Exception: return None

# ---- RAW walk (série + RSI + NAS + zonas + bubbles) ----
bars = {}; rsi_t = {}; nas_ev = []; zones = {}; bub = {}
for blk_i, blk in enumerate(BLOCKS):
    mnas = -1; nasi = False; snaps = []
    with gzip.open(RAW/blk, "rt") as fh:
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
        rv = grp(r, "study_values", "Relative Strength")
        if rv and cur is not None: rsi_t[cur] = fnum((rv.get("values") or {}).get("RSI"))
        ng = grp(r, "pine_labels", "NAS"); ngi = [l.get("id") for l in (ng.get("labels") or []) if l.get("id") is not None] if ng else []
        if not nasi:
            if ngi: mnas = max(ngi); nasi = True
        else:
            for l in (ng.get("labels") or []) if ng else []:
                lid = l.get("id")
                if lid is None or lid <= mnas: continue
                if "LONG" in str(l.get("text", "")).upper(): nas_ev.append(cur)
            if ngi: mnas = max(mnas, max(ngi))
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
                    if plot not in BUY: continue
                    k = (tt, plot)
                    if k not in bub: bub[k] = {"t": tt, "size": BUY[plot], "known_at": ka}
T = sorted(bars); O = [bars[t]["o"] for t in T]; H = [bars[t]["h"] for t in T]; L = [bars[t]["l"] for t in T]; C = [bars[t]["c"] for t in T]
N = len(T); ATR = [None]*N; EMA = [None]*N; ema = None; kE = 2/22; trs = []
for i in range(N):
    ema = C[i] if ema is None else C[i]*kE+ema*(1-kE); EMA[i] = ema
    if i > 0: trs.append(max(H[i]-L[i], abs(H[i]-C[i-1]), abs(L[i]-C[i-1])))
    ATR[i] = sum(trs[-14:])/14 if len(trs) >= 14 else None
S = dict(T=T, O=O, H=H, L=L, C=C, EMA=EMA, ATR=ATR, N=N)
RSI = [rsi_t.get(t) for t in T]
buys = sorted(bub.values(), key=lambda x: x["t"])
# agregação DIA para retr_up (perna macro de alta)
days = {}
for i in range(N):
    dk = T[i]//86400; g = days.setdefault(dk, {"h": H[i], "l": L[i], "t": dk*86400})
    g["h"] = max(g["h"], H[i]); g["l"] = min(g["l"], L[i])
DK = sorted(days); DT = [days[k]["t"] for k in DK]; DH = [days[k]["h"] for k in DK]; DL = [days[k]["l"] for k in DK]
reg = MM.build_layer1(); KN1 = [x+86400 for x in MM.T]
macro_at = lambda t0: reg[bisect.bisect_right(KN1, t0)-1] if bisect.bisect_right(KN1, t0)-1 >= 0 else None
print(f"RAW: {N} barras {ds(T[0])}→{ds(T[-1])} · NAS {len(nas_ev)} · zonas {len(zones)} · bubbles {len(buys)}")

# ---- STAGE 1: ESTRUTURA (regime detector) ----
def struct_ctx(j):
    reg_m = macro_at(T[j])
    di = bisect.bisect_right(DT, T[j]-86400)-1
    retr_up = None
    if di >= 25:
        seg = range(max(0, di-126), di+1); loi = min(seg, key=lambda i: DL[i])
        hia = max(range(loi, di+1), key=lambda i: DH[i]) if loi < di else di
        upleg = DH[hia]-DL[loi]
        if upleg > 0: retr_up = (DH[hia]-L[j])/upleg
    is_leg_bottom = L[j] <= min(L[max(0, j-192):j+1])+1e-9
    return reg_m, retr_up, is_leg_bottom

def swing_high_before(j):
    for p in range(j-M_FRAC, max(M_FRAC, j-LOWBACK*2), -1):
        if p-M_FRAC >= 0 and p+M_FRAC < N and H[p] == max(H[p-M_FRAC:p+M_FRAC+1]) and H[p] > max(H[p-M_FRAC:p]):
            return H[p]
    return None

# ENTRY not-knife: entra no CHoCH-up (1º close acima do último swing-high pós-flush, horizonte 96b).
# SL=flush_low-0.1ATR (largo), alvo 3R, SL-first. Select bottom-event first: só entra se a perna virou.
def choch_entry(j):
    sh = swing_high_before(j)
    if sh is None: return None
    atr = ATR[j] or 5.0; sl = round(L[j]-0.1*atr, 2)
    for ei in range(j+1, min(N, j+96)):
        if L[ei] <= sl: return None                     # varreu o flush-low antes de virar = faca, morre
        if C[ei] > sh:                                  # CHoCH-up estrutural = bottom-event confirmado
            ent = C[ei]; r = ent-sl
            if r <= 0: return None
            tgt = ent+3*r; o = "OPEN"
            for m in range(ei+1, min(N, ei+480)):
                if L[m] <= sl: o = "LOSS"; break
                if H[m] >= tgt: o = "WIN"; break
            return dict(ei=ei, anchor_bar=j, ent=ent, sl=sl, R=round(r, 2), o=o, choch_lag=ei-j)
    return None

# ---- STAGE 3: INDICADORES (depois da estrutura) ----
def indic_score(e):
    ei = e["ei"]; ab = e["anchor_bar"]; kt = T[ei]; lo_t = T[max(0, ab-16)]
    buy = sum(x["size"] for x in buys if x["known_at"] and x["known_at"] <= kt and lo_t <= x["t"] <= kt)
    nas = any(t and T[max(0, ab-8)] <= t <= kt for t in nas_ev)
    r_now = RSI[ab]; rsi_ok = r_now is not None and r_now <= 40
    div = False
    lows = [(p, L[p]) for p in range(max(M_FRAC, ab-LOWBACK), ab) if _is_swinglow(L, p, M_FRAC)]
    if lows and r_now is not None:
        pp, pl = lows[-1]; rp = RSI[pp]
        if rp is not None and L[ab] < pl and r_now > rp: div = True
    dem = any("DEMAND" in z["text"] and z["born_t"] and z["born_t"] <= T[ab] and z["low"] is not None and z["low"] <= L[ab] <= z["high"] for z in zones.values())
    return sum([buy >= 3, nas, rsi_ok or div, dem])

# ---- PIPELINE ----
GT_LOWS = []
for a, b in [(1770015600, 1770210000), (1770339600, 1771448400), (1774242000, 1774270800), (1781128800, 1781128800), (1782781200, 1782907200)]:
    aa = bisect.bisect_left(T, min(a, b)-12*3600); bb = bisect.bisect_right(T, max(a, b)+12*3600)
    if aa < bb: GT_LOWS.append(T[min(range(aa, bb), key=lambda k: L[k])])
t_lo = int(dt.datetime(2026, 2, 1, tzinfo=dt.timezone.utc).timestamp()); t_hi = int(dt.datetime(2026, 7, 4, tzinfo=dt.timezone.utc).timestamp())
seen = set(); rows = []
for k in range(200, N):
    if not (t_lo <= T[k] <= t_hi): continue
    atr = ATR[k] or 5.0
    if (H[k]-L[k]) < 1.8*atr or C[k] >= O[k]: continue
    mb = causal_entry(S, k, "MB3")                       # entry-KNIFE (imediato) p/ baseline
    if not mb or mb["ei"] in seen or mb["o"] == "OPEN": continue
    seen.add(mb["ei"]); j = mb["anchor_bar"]
    reg_m, retr_up, is_lb = struct_ctx(j)
    ce = choch_entry(j)                                  # entry NOT-KNIFE (pós CHoCH-up)
    rows.append({"mb_o": mb["o"], "reg": reg_m, "retr_up": retr_up, "is_lb": is_lb,
                 "ce": ce, "ind": indic_score(mb),
                 "is_gt": any(abs(T[j]-g) < 6*3600 for g in GT_LOWS)})

def hit(sub, key):
    v = [r for r in sub if r[key] and r[key] != "OPEN"]
    w = sum(1 for r in v if r[key] == "WIN"); return w, len(v), (100*w/len(v) if v else 0)
def line(name, sub, key):
    w, n, h = hit(sub, key); ng = sum(1 for r in sub if r["is_gt"])
    print(f"  {name:<54} N={n:>4}  hit-3R {h:>4.0f}% ({w}/{n})  GT={ng}")

STRUCT = lambda r: r["reg"] in ("BEAR", "RANGE") and r["is_lb"] and r["retr_up"] is not None and r["retr_up"] >= 0.45
print("\n=== PIPELINE ESTRUTURA→CONTEXTO→INDICADORES (lift por estágio) ===")
line("STAGE 0 null: MB3 imediato (a FACA)", rows, "mb_o")
line("STAGE 1 +ESTRUTURA (BEAR_reversal), ainda MB3", [r for r in rows if STRUCT(r)], "mb_o")
# STAGE 2: troca a entrada MB3 pela entrada NOT-KNIFE (choch_entry) — a essência
ce_o = lambda r: (r["ce"] or {}).get("o")
rows2 = [{**r, "ceo": ce_o(r)} for r in rows]
line("STAGE 2 ENTRY not-knife (choch_up) em TODOS os flushes", rows2, "ceo")
line("STAGE 2b +ESTRUTURA + entry not-knife", [r for r in rows2 if STRUCT(r)], "ceo")
for thr in (2, 3):
    line(f"STAGE 3 +INDICADORES(>={thr}) + estrutura + not-knife", [r for r in rows2 if STRUCT(r) and r["ind"] >= thr], "ceo")
qs = statistics.quantiles([r['retr_up'] for r in rows if r['retr_up'] is not None], n=4)
print(f"\n  retr_up terços (todos flushes): Q1 {qs[0]:.2f} Q2 {qs[1]:.2f} Q3 {qs[2]:.2f}")
gtr = [r for r in rows2 if r["is_gt"]]
print(f"  {len(gtr)} GT: reg {[r['reg'] for r in gtr]}")
print(f"    retr_up {[round(r['retr_up'],2) if r['retr_up'] else None for r in gtr]} · is_lb {[r['is_lb'] for r in gtr]}")
print(f"    MB3(faca) {[r['mb_o'] for r in gtr]} · choch-entry(not-knife) {[r['ceo'] for r in gtr]} · struct {[STRUCT(r) for r in gtr]}")