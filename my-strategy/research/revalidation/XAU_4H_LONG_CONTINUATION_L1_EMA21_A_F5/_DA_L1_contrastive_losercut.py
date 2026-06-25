#!/usr/bin/env python3
"""SANITY_PROBE — L1 EMA21 análise CONTRASTIVA AMPLA losers(16) vs winners(18) nos 34 aprovados, conjunto RAW LARGO
(volume up/dn/total + TODAS bolhas buy/sell s/m/L + value-area POC/VAH/VAL + SMC BOS/CHoCH + zonas OB demand/supply
multi + macro weekly/cascade/regime + estrutura intra-leg multi-janela + RSI). Busca combos 1/2/3 que cortem ≥1 loser
com 0 WINNERS, e roda NULL DE PERMUTAÇÃO (embaralha labels) p/ medir taxa de falso-positivo n=34. Causal as-of.
Multi-fatorial convergente (não eixo único). Verified 2026-06-25."""
import json, gzip, bisect, csv, datetime as dt, itertools, random, statistics as st
from pathlib import Path
random.seed(42)
V1 = Path("/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1")
CSV = Path("/Users/cristrein/tradingview-mcp/my-strategy/strategies/xau_4h_long/continuation/L1_EMA21_CONTINUATION/reports/l1_discriminator_filter_v2.csv")
def fn(x):
    try: return float(x)
    except Exception: return None
rows = [r for r in csv.DictReader(open(CSV)) if None not in (fn(r["ret5"]), fn(r["ext_ema"]), fn(r["zone_w"]), fn(r["dist_zone"]), fn(r["nas_shift1"]))
        and fn(r["ret5"]) <= 0.0142 and fn(r["ext_ema"]) <= 2.95 and fn(r["zone_w"]) >= 0.6 and fn(r["dist_zone"]) <= 1.81 and fn(r["nas_shift1"]) >= 1.31]
F = [json.loads(l) for l in open(V1 / "repro_recovery/raw_features_2020_2026.jsonl")]
N = len(F); H = [r["high"] for r in F]; L = [r["low"] for r in F]; C = [r["close"] for r in F]; O = [r["open"] for r in F]
TS = [int(r["ts_epoch"]) for r in F]; RSI = [r.get("rsi") for r in F]; VOL = [r.get("volume") for r in F]
ATR = [None] * N; trs = []
for i in range(1, N):
    trs.append(max(H[i] - L[i], abs(H[i] - C[i - 1]), abs(L[i] - C[i - 1])))
    if i >= 14: ATR[i] = sum(trs[i - 14:i]) / 14
EMA21 = [None] * N; k = 2 / 22; e = C[0]
for i in range(N):
    e = C[i] if i == 0 else C[i] * k + e * (1 - k); EMA21[i] = e
def toep(s):
    try: return int(dt.datetime.fromisoformat(str(s).replace("Z", "+00:00")).timestamp())
    except Exception: return int(dt.datetime.strptime(str(s)[:10], "%Y-%m-%d").replace(tzinfo=dt.timezone.utc).timestamp())
REG = V1 / "../../../../strategies/candidates/regime_classifier_v3/regime_B_v3_classifications.jsonl"
rb = [json.loads(l) for l in open(REG) if json.loads(l).get("ts")]
for r in rb: r["_e"] = toep(r["ts"])
rb.sort(key=lambda r: r["_e"]); rbt = [r["_e"] for r in rb]
def reg_asof(et): k = bisect.bisect_right(rbt, et) - 1; return rb[k] if k >= 0 else {}
MB = {}
for r in csv.DictReader(open(V1 / "results/l2_bpt_full276_macro_bear_v3_decisions.csv")):
    try: MB[int(float(r["bar_idx"]))] = r
    except Exception: pass
def l1_ep(ts): return int(dt.datetime.fromisoformat(ts).replace(tzinfo=dt.timezone.utc).timestamp())
def bar_of(et):
    k = bisect.bisect_left(TS, et); cs = [j for j in (k - 1, k, k + 1) if 0 <= j < N]
    return min(cs, key=lambda j: abs(TS[j] - et)) if cs else None
SVP = "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/4H/XAUUSD_4H_replay_2019-12_to_2026-current_SVP_LUX_RAW.jsonl.gz"
def to_ep(t): t = float(t); return int(t / 1000) if t > 1e11 else int(t)
def pv(s):
    if s is None: return None
    s = str(s).replace(" ", "").replace(",", "").replace("−", "-").strip(); m = 1.0
    if s and s[-1] in ("K", "M", "B"): m = {"K": 1e3, "M": 1e6, "B": 1e9}[s[-1]]; s = s[:-1]
    try: return float(s) * m
    except Exception: return None
def gv(rec, nm):
    return next((s.get("values", {}) for s in (rec.get("study_values") or []) if nm in str(s.get("name", ""))), {})
D = {}
with gzip.open(SVP, "rt") as fh:
    for line in fh:
        if '"ohlcv"' not in line: continue
        rec = json.loads(line); oh = rec.get("ohlcv"); last = oh[-1] if isinstance(oh, list) and oh else None
        if not isinstance(last, dict): continue
        at = to_ep(last.get("time"))
        if at is None or at in D: continue
        vp = gv(rec, "Session Volume Profile")
        g = next((x for x in (rec.get("pine_boxes") or []) if "Custom OB" in str(x.get("name", ""))), {})
        zones = [(z["high"], z["low"]) for z in (g.get("zones") or []) if z.get("high") is not None]
        bg = next((x for x in (rec.get("pine_shapes_bubbles") or []) if "Bubble" in str(x.get("name", ""))), {})
        a = bg.get("activations_per_plot") or {}
        sv = rec.get("session_vp", {}); l3 = (sv.get("last3") or []) if isinstance(sv, dict) else []; poc = vah = val = None
        if l3 and isinstance(l3[-1], dict):
            v = l3[-1].get("v") or []
            if len(v) >= 4: poc, vah, val = v[1], v[2], v[3]
        smc = next((x for x in (rec.get("pine_labels") or []) if "Smart Money" in str(x.get("name", ""))), {}); sl = smc.get("labels") or []
        nasg = next((x for x in (rec.get("pine_labels") or []) if "NAS" in str(x.get("name", "")).upper() or "Nadaraya" in str(x.get("name", ""))), {}); nl = nasg.get("labels") or []
        D[at] = dict(up=pv(vp.get("Up")), dn=pv(vp.get("Down")), tot=pv(vp.get("Total")), zones=zones, poc=poc, vah=vah, val=val,
                     buy_s=pv(a.get("plot_0")) or 0, buy_m=pv(a.get("plot_2")) or 0, buy_l=pv(a.get("plot_4")) or 0,
                     sell_s=pv(a.get("plot_6")) or 0, sell_m=pv(a.get("plot_8")) or 0, sell_l=pv(a.get("plot_10")) or 0,
                     smc=(sl[-1].get("text") if sl else None), nas=(nl[-1].get("text") if nl else None))
DT = sorted(D)
def asof(et): k = bisect.bisect_right(DT, et) - 1; return D[DT[k]] if k >= 0 else {}
def win10(et, key): return sum((D[t].get(key) or 0) for t in [t for t in DT if t <= et][-10:])

T = []
for r in rows:
    et = l1_ep(r["ts"]); i = bar_of(et)
    if i is None or not ATR[i]: continue
    d = asof(TS[i]); entry = C[i]; rg = reg_asof(TS[i]); mb = MB.get(i, {})
    zones = d.get("zones", []); below = [(hi, lo) for hi, lo in zones if hi <= entry]; above = [(hi, lo) for hi, lo in zones if lo >= entry]
    up, dn = d.get("up") or 0, d.get("dn") or 0; vr = up / (up + dn) if (up + dn) else 0.5
    poc, vah, val = d.get("poc"), d.get("vah"), d.get("val")
    def winpos(w): lo = min(L[max(0, i - w):i + 1]); hi = max(H[max(0, i - w):i + 1]); return (entry - lo) / (hi - lo) if hi > lo else 0.5
    cu = cd = 0
    for j in range(i, max(0, i - 8), -1):
        if C[j] > O[j] and cu == (i - j): cu += 1
        if C[j] < O[j] and cd == (i - j): cd += 1
    volp = (VOL[i] / (sum(v for v in VOL[max(0, i - 20):i] if v) / max(1, len([v for v in VOL[max(0, i - 20):i] if v])))) if VOL[i] and i >= 20 else None
    T.append(dict(win=fn(r["R"]) > 0, R=fn(r["R"]), mfe=fn(r["mfe"]), runner=fn(r["mfe"]) >= 5, ts=r["ts"],
        # VOLUME
        vol_ratio=vr, vol_spike=volp, buy10=win10(TS[i], "buy_l") + win10(TS[i], "buy_m"), sell10=win10(TS[i], "sell_l") + win10(TS[i], "sell_m"),
        sell_l10=win10(TS[i], "sell_l"), buy_l10=win10(TS[i], "buy_l"), sell_now=(d.get("sell_s") or 0) + (d.get("sell_m") or 0) + (d.get("sell_l") or 0),
        # VALUE AREA
        above_vah=int(vah is not None and entry > vah), below_val=int(val is not None and entry < val),
        inside_va=int(val is not None and vah is not None and val <= entry <= vah), above_poc=int(poc is not None and entry > poc),
        dist_poc=((entry - poc) / ATR[i]) if poc is not None else None,
        # MACRO
        weekly=fn(mb.get("weekly_slope")), cascade=fn(rg.get("cascade_score")), regime=rg.get("raw_state"),
        # LEG / SMC / NAS
        choch=int("CHoCH" in str(d.get("smc") or "")), bos=int("BOS" in str(d.get("smc") or "")),
        smc_bear=int(any(x in str(d.get("smc") or "") for x in ("Bearish", "-"))), nas_short=int("SHORT" in str(d.get("nas") or "").upper()),
        # INTRA-LEG / estrutura
        rng10=winpos(10), rng20=winpos(20), rng40=winpos(40), consec_up=cu, consec_dn=cd,
        ext_atr=((entry - EMA21[i]) / ATR[i]) if EMA21[i] else None,
        dist_sup=((min(above, key=lambda z: z[1])[1] - entry) / ATR[i]) if above else 99,
        dist_dem=((entry - max(below, key=lambda z: z[0])[0]) / ATR[i]) if below else 99,
        n_sup=len(above), n_dem=len(below),
        # L1 próprios
        ret5=fn(r["ret5"]), ext_ema=fn(r["ext_ema"]), rsi_vs_ma=fn(r["rsi_vs_ma"]), atr_ratio=fn(r["atr_ratio"]),
        hour=fn(r["hour"]), dow=fn(r["dow"]) if r.get("dow") not in (None, "") else None, rsi=RSI[i]))
nL = sum(1 for t in T if not t["win"]); nW = sum(1 for t in T if t["win"])
print(f"L1 34: winners={nW} losers={nL} runners={sum(1 for t in T if t['runner'])}")

# ---- construir POOL de predicados binários a partir de TODAS as features ----
NUM = ["vol_ratio", "vol_spike", "buy10", "sell10", "sell_l10", "buy_l10", "sell_now", "dist_poc", "weekly", "cascade",
       "rng10", "rng20", "rng40", "consec_up", "consec_dn", "ext_atr", "dist_sup", "dist_dem", "n_sup", "n_dem",
       "ret5", "ext_ema", "rsi_vs_ma", "atr_ratio", "hour", "dow", "rsi"]
BIN = ["above_vah", "below_val", "inside_va", "above_poc", "choch", "bos", "smc_bear", "nas_short"]
preds = []  # (nome, set(idx que satisfaz))
idx = list(range(len(T)))
for f in NUM:
    vals = sorted(set(t[f] for t in T if t[f] is not None))
    if len(vals) < 2: continue
    qs = sorted(set(st.quantiles(vals, n=4) + [st.median(vals)])) if len(vals) >= 4 else vals
    for thr in qs:
        for op, fnop in ((">=", lambda x, th=thr: x >= th), ("<=", lambda x, th=thr: x <= th)):
            s = frozenset(j for j in idx if T[j][f] is not None and fnop(T[j][f]))
            if 1 <= len(s) <= len(T) - 1: preds.append((f"{f}{op}{thr:.3g}", s))
for f in BIN:
    s = frozenset(j for j in idx if T[j][f]);
    if 1 <= len(s) <= len(T) - 1: preds.append((f"{f}=1", s)); preds.append((f"{f}=0", frozenset(set(idx) - s)))
# dedup por conjunto idêntico
seen = {};
for nm, s in preds:
    if s not in seen: seen[s] = nm
preds = [(nm, s) for s, nm in seen.items()]
LOS = frozenset(j for j in idx if not T[j]["win"]); WIN = frozenset(j for j in idx if T[j]["win"]); RUN = frozenset(j for j in idx if T[j]["runner"])
print(f"predicados únicos = {len(preds)}")

def search(predlist, maxk):
    """retorna lista de combos (descr, idx_cortados) com 0 winners e >=1 loser, k<=maxk"""
    out = []
    # single
    for nm, s in predlist:
        if not (s & WIN) and (s & LOS): out.append(([nm], s))
    # 2 e 3 combos (AND) — só vale a pena combinar predicados que sozinhos já não estouram winners demais
    base = [(nm, s) for nm, s in predlist]
    if maxk >= 2:
        for (n1, s1), (n2, s2) in itertools.combinations(base, 2):
            s = s1 & s2
            if s and not (s & WIN) and (s & LOS): out.append(([n1, n2], s))
    if maxk >= 3:
        for (n1, s1), (n2, s2), (n3, s3) in itertools.combinations(base, 3):
            s = s1 & s2 & s3
            if s and not (s & WIN) and (s & LOS): out.append(([n1, n2, n3], s))
    return out

real = search(preds, 3)
# melhor por nº de losers cortados, depois menos termos
real_sorted = sorted(real, key=lambda c: (-len(c[1]), len(c[0])))
best_by_size = {}
for terms, s in real_sorted:
    nl = len(s)
    if nl not in best_by_size: best_by_size[nl] = (terms, s)
print("\n=== melhores 0-WINNER por nº de losers cortados (single+2+3 combos) ===")
for nl in sorted(best_by_size, reverse=True):
    terms, s = best_by_size[nl]; rc = len(s & RUN)
    cut_ts = [T[j]["ts"][:10] for j in sorted(s)]
    print(f"  corta {nl} loser(s) [{rc} runner] : {' AND '.join(terms)}")
    print(f"      → datas: {cut_ts}")

# ---- NULL DE PERMUTAÇÃO: quantos losers consegue-se cortar 0-winner com labels EMBARALHADAS ----
def max_loser_cut_0win(los_set):
    win_set = frozenset(set(idx) - los_set); best = 0
    for nm, s in preds:
        if not (s & win_set) and (s & los_set): best = max(best, len(s & los_set))
    for (n1, s1), (n2, s2) in itertools.combinations(preds, 2):
        s = s1 & s2
        if s and not (s & win_set) and (s & los_set): best = max(best, len(s & los_set))
    return best
real_single2 = max_loser_cut_0win(LOS)
M = 200; nulldist = []
allidx = list(idx)
for _ in range(M):
    perm = allidx[:]; random.shuffle(perm)
    los_perm = frozenset(perm[:nL])  # mesmo nº de "losers" aleatórios
    nulldist.append(max_loser_cut_0win(los_perm))
ge = sum(1 for x in nulldist if x >= real_single2)
print(f"\n=== NULL DE PERMUTAÇÃO (single+2-combo, {M} shuffles) ===")
print(f"  real: maior loser-cut 0-winner (single/2-combo) = {real_single2}")
print(f"  null: média={st.mean(nulldist):.2f} max={max(nulldist)} | P(null >= real) = {ge/M:.3f}")
print(f"  → se P alto, o corte 0-winner é ARTEFATO de n=34 (qualquer rótulo gera corte igual)")
json.dump([{k: t[k] for k in t} for t in T], open(Path(__file__).parent / "l1_contrastive_features.json", "w"), default=str)
print("\nIn-sample/exploratório n=34. Carregar status (calibração, não validação).")
