#!/usr/bin/env python3
"""EVENTO — CLASSIFICADOR NÃO-LINEAR kNN (2026-07-06). Score linear falhou; features fracas podem
ter INTERAÇÕES/CLUSTERING que kNN detecta. Classifica o EVENTO pelo seu 1º candidato (máximo
causal; o DA6 mostrou 9/14 features separam já no K=1). Features causais do cache + pre_drop.
Validação: LEAVE-ONE-OUT (voto dos K vizinhos, excluindo o próprio) → AUC + precisão top-decil OOF.
NULL: permuta labels 500× (seed fixa), recomputa AUC LOO → P(AUC>=obs). Se AUC OOF bate null e
top-decil concentra fundos, há estrutura multivariada aproveitável; senão, teto confirmado por ML.
SANITY_PROBE: features SÓ do 1º candidato do evento (causal) + pre_drop causal; LOO exclui o próprio;
null permuta y através do classificador; precisão por evento-fundo (não candidato)."""
import json, bisect, hashlib
import numpy as np
from pathlib import Path
HERE = Path(__file__).resolve().parent
exec((HERE / "macro_leg_position_veto_20260705.py").read_text().split("VETOS = {")[0])
GTF = HERE / "results" / "ground_truth_bottoms_20260705.json"
assert hashlib.sha256(GTF.read_bytes()).hexdigest() == (HERE / "results" / "ground_truth_bottoms_20260705.sha256").read_text().split()[0]
GT = json.load(open(GTF))
Sn = len(S); ATR = [b.get("atr") or 5.0 for b in S]; HI = [b["h"] for b in S]; LO = [b["l"] for b in S]
CACHE = {r["cj_t"]: r for r in (json.loads(l) for l in open(HERE / "results" / "raw_feature_cache_20260706.jsonl"))}
UNIV = sorted([u for u in U if u["cj_t"] in R3 and u["cj_t"] in CACHE], key=lambda u: u["cj_t"])
UT = [u["cj_t"] for u in UNIV]
for u in UNIV:
    u["_flo"] = u["g_sl"] + 0.1 * (u.get("g_atr") or 5.0); u["_a"] = u.get("g_atr") or 5.0
    u["_circ"] = set(); u["_F"] = CACHE[u["cj_t"]]
for gi, g in enumerate(GT):
    j = bisect.bisect_left(UT, g["flush_t"] - 8 * 3600)
    while j < len(UNIV) and UT[j] <= g["flush_t"] + 8 * 3600:
        u = UNIV[j]; d = u["_flo"] - g["flush_low"]
        if -3 * u["_a"] <= d <= 1 * u["_a"]: u["_circ"].add(gi)
        j += 1
EV = []; cur = []
for u in UNIV:
    if cur and u["cj_t"] - cur[-1]["cj_t"] <= 48 * 3600 and abs(u["_flo"] - cur[-1]["_flo"]) <= 3 * u["_a"]:
        cur.append(u)
    else:
        if cur: EV.append(cur)
        cur = [u]
if cur: EV.append(cur)

FEATS = ["rsi_min8", "nas_dist", "rsi_cj", "poc_dist", "below_poc", "vol_climax", "sell_climax4",
         "buy_accum12", "choch_up_rec24", "flow_divergence", "nas_long_rec", "rsi_bull_div",
         "ob_demand_mitig", "big_buy_recency"]
X = []; y = []
for ev in EV:
    u0 = ev[0]; f = u0["_F"]
    st_i = bisect.bisect_right(TS, u0["cj_t"]) - 1
    pre_hi = max(HI[max(0, st_i - 96):st_i + 1]); a = u0["_a"]
    pre_drop = (pre_hi - LO[st_i]) / a
    X.append([f[k] for k in FEATS] + [pre_drop])
    y.append(1 if any(uu["_circ"] for uu in ev) else 0)
X = np.array(X, float); y = np.array(y)
# normaliza (z)
mu = X.mean(0); sd = X.std(0); sd[sd == 0] = 1
Xn = (X - mu) / sd
n = len(y); nf = int(y.sum())
print(f"eventos {n} · fundo {nf} · base {100*nf/n:.1f}% · features {X.shape[1]}")

def loo_scores(Xn, y, K=20):
    # distância euclidiana; score = média de y dos K vizinhos (excl. próprio)
    D = np.sqrt(((Xn[:, None, :] - Xn[None, :, :]) ** 2).sum(2))
    np.fill_diagonal(D, np.inf)
    sc = np.empty(len(y))
    for i in range(len(y)):
        idx = np.argpartition(D[i], K)[:K]
        sc[i] = y[idx].mean()
    return sc

def auc(sc, y):
    pos = sc[y == 1]; neg = sc[y == 0]
    # U-stat AUC
    order = np.argsort(sc); ranks = np.empty(len(sc)); ranks[order] = np.arange(1, len(sc) + 1)
    # tie-correct via average ranks
    s = np.argsort(sc, kind="mergesort"); sr = sc[s]; r = np.arange(1, len(sc) + 1, dtype=float)
    i = 0
    while i < len(sr):
        j = i
        while j + 1 < len(sr) and sr[j + 1] == sr[i]: j += 1
        r[i:j + 1] = (i + j) / 2 + 1; i = j + 1
    rr = np.empty(len(sc)); rr[s] = r
    n1 = y.sum(); n0 = len(y) - n1
    return (rr[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)

sc = loo_scores(Xn, y, K=20)
obs_auc = auc(sc, y)
# precisão top-decil OOF
k = max(10, n // 10)
top = np.argsort(-sc)[:k]
top_prec = y[top].mean(); lift = top_prec / (nf / n)
print(f"kNN LOO K=20: AUC {obs_auc:.4f} · top-decil precisão {100*top_prec:.1f}% (base {100*nf/n:.1f}%, lift {lift:.2f}×) · fundos no top {int(y[top].sum())}/{nf}")
# NULL permutação de labels
rng = np.random.default_rng(701)
ge = 0; NP = 500
for _ in range(NP):
    yp = rng.permutation(y)
    scp = loo_scores(Xn, yp, K=20)
    if auc(scp, yp) >= obs_auc: ge += 1
print(f"NULL permutação labels ({NP}×): P(AUC>=obs)={ge/NP:.4f}")
# outcome do top-decil (esses eventos dão 3R via 1º candidato?)
ev_sorted = [EV[i] for i in np.argsort(-sc)]
topev = ev_sorted[:k]
h = sum(1 for ev in topev if R3[ev[0]["cj_t"]]["R3"] >= 3)
nets = [R3[ev[0]["cj_t"]]["net3"] for ev in topev]
print(f"top-decil outcome (1º cand): hit3R {100*h/k:.1f}% · NET {sum(nets):+.1f}")
json.dump({"n": n, "fund": nf, "auc": round(obs_auc, 4), "p_null": ge / NP,
           "top_prec": round(top_prec, 3), "lift": round(lift, 2)},
          open(HERE / "results" / "event_knn_nonlinear_20260706.json", "w"), indent=1)
print("OK → results/event_knn_nonlinear_20260706.json")
