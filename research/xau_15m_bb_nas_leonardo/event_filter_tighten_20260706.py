#!/usr/bin/env python3
"""APERTO CRIATIVO DO FILTRO DE EVENTO (2026-07-06, ordem Cris: ousado sem perder fundos válidos).
O envelope por-feature (bounding-box) é largo — aceita os CANTOS VAZIOS do retângulo. Formas
multivariadas que cortam os cantos mantendo os fundos:
  M1 bounding-box (baseline atual)
  M2 por-FAMÍLIA (evento passa se está no envelope da SUA família de retração — mais apertado)
  M3 MAHALANOBIS ao centroide dos fundos (elimina correlações; corta cantos do retângulo)
  M4 kNN-DENSIDADE (mantém eventos com alta fração de fundos entre os K vizinhos)
  M5 HÍBRIDO família & mahalanobis
Curva: p/ cada método, thresholds que dão recall {100,97,93,90}% → densidade + hit3R + N do pool.
NULL: 50 eventos aleatórios, mesmo procedimento, P(corta>=obs mantendo recall). Objetivo = achar o
ponto que MAIS aperta a densidade mantendo recall alto e SEM perder fundos.
SANITY_PROBE: features causais (até 3º cand); envelope/centroide/cov = calibração declarada; null
permuta rótulo-fundo; recall por círculo; numpy p/ mahalanobis/kNN."""
import json, bisect, hashlib, random
import numpy as np
from pathlib import Path
HERE = Path(__file__).resolve().parent
exec((HERE / "macro_leg_position_veto_20260705.py").read_text().split("VETOS = {")[0])
GTF = HERE / "results" / "ground_truth_bottoms_20260705.json"
assert hashlib.sha256(GTF.read_bytes()).hexdigest() == (HERE / "results" / "ground_truth_bottoms_20260705.sha256").read_text().split()[0]
GT = json.load(open(GTF))
N = len(S); ATR = [b.get("atr") or 5.0 for b in S]; HI = [b["h"] for b in S]; LO = [b["l"] for b in S]
CACHE = {r["cj_t"]: r for r in (json.loads(l) for l in open(HERE / "results" / "raw_feature_cache_20260706.jsonl"))}
UNIV = sorted([u for u in U if u["cj_t"] in R3 and u["cj_t"] in CACHE], key=lambda u: u["cj_t"])
UT = [u["cj_t"] for u in UNIV]
LOWS = []; d0 = 0; ehi = elo = 0
for i in range(1, N):
    if HI[i] > HI[ehi]: ehi = i
    if LO[i] < LO[elo]: elo = i
    if d0 >= 0 and HI[ehi] - LO[i] >= 6 * ATR[i] and ehi < i: d0 = -1; elo = min(range(ehi, i+1), key=lambda k: LO[k])
    elif d0 <= 0 and HI[i] - LO[elo] >= 6 * ATR[i] and elo < i: LOWS.append((i, elo)); d0 = 1; ehi = max(range(elo, i+1), key=lambda k: HI[k])
KLOW = [x[0] for x in LOWS]
for u in UNIV:
    u["_flo"] = u["g_sl"] + 0.1 * (u.get("g_atr") or 5.0); u["_a"] = u.get("g_atr") or 5.0
    u["_circ"] = set(); u["_F"] = CACHE[u["cj_t"]]
    ci = bisect.bisect_right(TS, u["cj_t"]) - 1; j = bisect.bisect_right(KLOW, ci) - 1
    u["_fam"] = "SEM"
    if j >= 0:
        _, l0i = LOWS[j]; L0 = LO[l0i]; H1 = max(HI[k] for k in range(l0i, ci+1))
        if H1 - L0 > 1e-9:
            r = (H1 - u["_flo"]) / (H1 - L0); u["_fam"] = "RASO" if r < 0.5 else ("BANDA" if r <= 1.3 else "FUNDO")
for gi, g in enumerate(GT):
    j = bisect.bisect_left(UT, g["flush_t"] - 8 * 3600)
    while j < len(UNIV) and UT[j] <= g["flush_t"] + 8 * 3600:
        u = UNIV[j]; dd = u["_flo"] - g["flush_low"]
        if -3 * u["_a"] <= dd <= 1 * u["_a"]: u["_circ"].add(gi)
        j += 1
EV = []; cur = []
for u in UNIV:
    if cur and u["cj_t"] - cur[-1]["cj_t"] <= 48*3600 and abs(u["_flo"] - cur[-1]["_flo"]) <= 3*u["_a"]:
        cur.append(u)
    else:
        if cur: EV.append(cur)
        cur = [u]
if cur: EV.append(cur)
FEATS = ["rsi_min8", "nas_dist", "sell_climax4", "below_poc", "poc_dist", "nas_long_rec", "vol_climax", "flow_divergence"]
def ev_vec(ev):
    sub = ev[:3]; F = [u["_F"] for u in sub]
    st_i = bisect.bisect_right(TS, ev[0]["cj_t"]) - 1; a = ev[0]["_a"]
    pre_hi = max(HI[max(0, st_i-96):st_i+1]); ei = bisect.bisect_right(TS, sub[-1]["cj_t"]) - 1
    pre_drop = (pre_hi - min(LO[max(0, st_i-8):ei+1])) / a
    v = [min(f["rsi_min8"] for f in F), min(f["nas_dist"] for f in F), max(f["sell_climax4"] for f in F),
         max(f["below_poc"] for f in F), min(f["poc_dist"] for f in F), max(f["nas_long_rec"] for f in F),
         max(f["vol_climax"] for f in F), max(f["flow_divergence"] for f in F), pre_drop]
    return v
for ev in EV:
    ev[0]["_vec"] = ev_vec(ev); ev[0]["_isf"] = any(u["_circ"] for u in ev)
    ev[0]["_efam"] = ev[0]["_fam"]
X = np.array([ev[0]["_vec"] for ev in EV], float)
isf = np.array([ev[0]["_isf"] for ev in EV])
mu_all = X.mean(0); sd_all = X.std(0); sd_all[sd_all == 0] = 1
Xn = (X - mu_all) / sd_all
NF = int(isf.sum())
print(f"eventos {len(EV)} · fundo {NF} · densidade base {(len(EV)-NF)/NF:.1f}:1")

def circ_of(mask):
    c = set()
    for keep, ev in zip(mask, EV):
        if keep:
            for u in ev: c |= u["_circ"]
    return len(c)
def report(mask, tag):
    kept = int(mask.sum()); kf = int((mask & isf).sum())
    pool = [u for keep, ev in zip(mask, EV) if keep for u in ev]
    h = 100*sum(1 for u in pool if R3[u["cj_t"]]["R3"]>=3)/len(pool) if pool else 0
    dens = (kept - kf) / max(1, kf)
    print(f"  {tag:<22} eventos {kept:>3} fundos {kf}/{NF} círc {circ_of(mask)}/60 dens {dens:>4.1f}:1 hit3R {h:.1f}% (recall {100*kf/NF:.0f}%)")
    return {"kept": kept, "kf": kf, "dens": round(dens,1), "hit": round(h,1)}

# M3 Mahalanobis
Xf = Xn[isf]
cov = np.cov(Xf.T) + np.eye(Xn.shape[1]) * 0.3
inv = np.linalg.pinv(cov); cf = Xf.mean(0)
md = np.sqrt(((Xn - cf) @ inv * (Xn - cf)).sum(1))
md_f = md[isf]
# M4 kNN density
D = np.sqrt(((Xn[:, None, :] - Xn[None, :, :])**2).sum(2)); np.fill_diagonal(D, np.inf)
K = 25
knn_fund = np.array([isf[np.argpartition(D[i], K)[:K]].mean() for i in range(len(EV))])

out = {}
print("\nM3 MAHALANOBIS (threshold = quantil das distâncias dos fundos):")
for q, lab in ((1.0, "recall100"), (0.97, "recall97"), (0.93, "recall93"), (0.90, "recall90")):
    thr = np.sort(md_f)[min(len(md_f)-1, int(q*(len(md_f)-1)))]
    mask = md <= thr
    out[f"M3_{lab}"] = report(mask, f"M3 {lab}")
print("\nM4 kNN-DENSIDADE (threshold p/ recall alvo):")
for q, lab in ((0.0, "recall100"), (0.03, "recall97"), (0.07, "recall93"), (0.10, "recall90")):
    thr = np.sort(knn_fund[isf])[min(len(md_f)-1, int(q*(len(md_f)-1)))]
    mask = knn_fund >= thr
    out[f"M4_{lab}"] = report(mask, f"M4 {lab}")
print("\nM2 POR-FAMÍLIA (bounding-box da própria família, q0-q100):")
efam = np.array([ev[0]["_efam"] for ev in EV])
maskfam = np.zeros(len(EV), bool)
for fam in ("RASO", "BANDA", "FUNDO"):
    idx = np.where((efam == fam))[0]; fidx = np.where((efam == fam) & isf)[0]
    if len(fidx) < 3:
        maskfam[idx] = True; continue
    lo = X[fidx].min(0); hi = X[fidx].max(0)
    for i in idx:
        if np.all((X[i] >= lo) & (X[i] <= hi)): maskfam[i] = True
out["M2_fam"] = report(maskfam, "M2 família")
print("\nM5 HÍBRIDO família & mahalanobis-recall97:")
thr = np.sort(md_f)[int(0.97*(len(md_f)-1))]
mask5 = maskfam & (md <= thr)
out["M5_hibrido"] = report(mask5, "M5 família&maha97")

# NULL para o melhor (M3 recall97): 50 aleatórios
def maha_cut(fund_mask):
    Xf2 = Xn[fund_mask]
    if len(Xf2) < 5: return 0, 0
    cov2 = np.cov(Xf2.T) + np.eye(Xn.shape[1])*0.3; inv2 = np.linalg.pinv(cov2); cf2 = Xf2.mean(0)
    md2 = np.sqrt(((Xn - cf2) @ inv2 * (Xn - cf2)).sum(1))
    thr2 = np.sort(md2[fund_mask])[int(0.97*(fund_mask.sum()-1))]
    keep2 = md2 <= thr2
    return len(EV) - int(keep2.sum()), int((keep2 & fund_mask).sum())
thr = np.sort(md_f)[int(0.97*(len(md_f)-1))]; obs_cut = len(EV) - int((md <= thr).sum())
rng = np.random.default_rng(950); ge = 0; NP = 500
for _ in range(NP):
    fm = np.zeros(len(EV), bool); fm[rng.choice(len(EV), NF, replace=False)] = True
    cut2, rf2 = maha_cut(fm)
    if cut2 >= obs_cut: ge += 1
print(f"\nNULL M3-recall97 (50 aleatórios, {NP}×): P(corta>=obs)={ge/NP:.4f}")
json.dump(out, open(HERE / "results" / "event_filter_tighten_20260706.json", "w"), indent=1, default=float)
print("OK → results/event_filter_tighten_20260706.json")
