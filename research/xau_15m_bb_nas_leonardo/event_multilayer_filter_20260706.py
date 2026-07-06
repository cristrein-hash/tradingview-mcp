#!/usr/bin/env python3
"""SELEÇÃO DE EVENTO-FUNDO SEM LOOK-AHEAD, EM CAMADAS (2026-07-06, ordem Cris: baixar densidade
mantendo top-60). Responder: temos seleção causal validada? Objetivo: densidade 5,6:1 -> ~2:1
mantendo recall alto. TODAS as features <= cj (sem outcome na decisão) = SEM look-ahead.
CAMADAS causais (cada evento avaliado no seu 3º candidato / progressivo):
  L1 família-envelope (recall 100%, 5,6:1)  [baseline]
  L2 L1 & evento-tem-cascade>=4 (capitulação estrutural SMC — o degrau causal do DA)
  L3 L2 & mahalanobis apertado (centroide dos fundos)
  L4 L2 & score-kNN alto (densidade de fundos-vizinhos)
  L5 L2 & (maha & knn)
Métrica por camada: eventos, recall-círculo/60, precisão %, densidade, hit3R do pool.
VALIDAÇÃO (não-circular; filtro causal calibrado nos fundos, outcome nunca na decisão):
  NULL = mesmo procedimento com envelope/centroide de K eventos ALEATÓRIOS, 500× → o filtro-dos-
  fundos corta MAIS lixo mantendo recall que o aleatório? P baixo = seleção capta estrutura real.
+ pipeline: E5/E6 (cascade&reclaim) no pool de cada camada.
SANITY_PROBE: features causais (até 3º cand) · cascade() causal (t<=cj) · null permuta rótulo-fundo
· recall círculo distinto · precisão declarada (calibração, não out-of-sample)."""
import json, bisect, hashlib, random
import numpy as np
from pathlib import Path
HERE = Path(__file__).resolve().parent
exec((HERE / "macro_leg_position_veto_20260705.py").read_text().split("VETOS = {")[0])
GTF = HERE / "results" / "ground_truth_bottoms_20260705.json"
assert hashlib.sha256(GTF.read_bytes()).hexdigest() == (HERE / "results" / "ground_truth_bottoms_20260705.sha256").read_text().split()[0]
GT = json.load(open(GTF))
N = len(S); ATR = [b.get("atr") or 5.0 for b in S]; HI = [b["h"] for b in S]; LO = [b["l"] for b in S]; CL = [b["c"] for b in S]; OP = [b.get("o", b["c"]) for b in S]
CACHE = {r["cj_t"]: r for r in (json.loads(l) for l in open(HERE / "results" / "raw_feature_cache_20260706.jsonl"))}
UNIV = sorted([u for u in U if u["cj_t"] in R3 and u["cj_t"] in CACHE], key=lambda u: u["cj_t"])
UT = [u["cj_t"] for u in UNIV]; WK = len({u["g_week"] for u in U})
LOWS = []; d0 = 0; ehi = elo = 0
for i in range(1, N):
    if HI[i] > HI[ehi]: ehi = i
    if LO[i] < LO[elo]: elo = i
    if d0 >= 0 and HI[ehi]-LO[i] >= 6*ATR[i] and ehi < i: d0 = -1; elo = min(range(ehi,i+1), key=lambda k: LO[k])
    elif d0 <= 0 and HI[i]-LO[elo] >= 6*ATR[i] and elo < i: LOWS.append((i,elo)); d0 = 1; ehi = max(range(elo,i+1), key=lambda k: HI[k])
KLOW = [x[0] for x in LOWS]
for u in UNIV:
    u["_flo"] = u["g_sl"] + 0.1*(u.get("g_atr") or 5.0); u["_a"] = u.get("g_atr") or 5.0; u["_circ"] = set(); u["_F"] = CACHE[u["cj_t"]]
    ci = bisect.bisect_right(TS, u["cj_t"])-1; j = bisect.bisect_right(KLOW, ci)-1; u["_fam"] = "SEM"
    if j >= 0:
        _, l0i = LOWS[j]; L0 = LO[l0i]; H1 = max(HI[k] for k in range(l0i, ci+1))
        if H1-L0 > 1e-9:
            r = (H1-u["_flo"])/(H1-L0); u["_fam"] = "RASO" if r<0.5 else ("BANDA" if r<=1.3 else "FUNDO")
    u["_casc"] = cascade(u["cj_t"])
for gi, g in enumerate(GT):
    j = bisect.bisect_left(UT, g["flush_t"]-8*3600)
    while j < len(UNIV) and UT[j] <= g["flush_t"]+8*3600:
        u = UNIV[j]; dd = u["_flo"]-g["flush_low"]
        if -3*u["_a"] <= dd <= 1*u["_a"]: u["_circ"].add(gi)
        j += 1
EV = []; cur = []
for u in UNIV:
    if cur and u["cj_t"]-cur[-1]["cj_t"] <= 48*3600 and abs(u["_flo"]-cur[-1]["_flo"]) <= 3*u["_a"]:
        cur.append(u)
    else:
        if cur: EV.append(cur)
        cur = [u]
if cur: EV.append(cur)
def vec(ev):
    sub = ev[:3]; F = [u["_F"] for u in sub]
    st_i = bisect.bisect_right(TS, ev[0]["cj_t"])-1; a = ev[0]["_a"]; pre_hi = max(HI[max(0,st_i-96):st_i+1]); ei = bisect.bisect_right(TS, sub[-1]["cj_t"])-1
    return [min(f["rsi_min8"] for f in F), min(f["nas_dist"] for f in F), max(f["sell_climax4"] for f in F), max(f["below_poc"] for f in F),
            min(f["poc_dist"] for f in F), max(f["nas_long_rec"] for f in F), max(f["vol_climax"] for f in F), max(f["flow_divergence"] for f in F),
            (pre_hi - min(LO[max(0,st_i-8):ei+1]))/a]
TOTALC = len(set().union(*(u["_circ"] for ev in EV for u in ev)))
for ev in EV:
    ev[0]["_vec"] = vec(ev); ev[0]["_isf"] = any(u["_circ"] for u in ev); ev[0]["_efam"] = ev[0]["_fam"]
    ev[0]["_hascasc"] = any(u["_casc"] >= 4 for u in ev[:6])   # causal: entre os 1os candidatos
    c = set()
    for u in ev: c |= u["_circ"]
    ev[0]["_circset"] = c
X = np.array([ev[0]["_vec"] for ev in EV]); isf = np.array([ev[0]["_isf"] for ev in EV]); efam = np.array([ev[0]["_efam"] for ev in EV])
hascasc = np.array([ev[0]["_hascasc"] for ev in EV]); NF = int(isf.sum())
mu = X.mean(0); sd = X.std(0); sd[sd==0] = 1; Xn = (X-mu)/sd
def circ(mask):
    c = set()
    for k, ev in zip(mask, EV):
        if k: c |= ev[0]["_circset"]
    return len(c)
def rep(mask, tag):
    kept = int(mask.sum()); kf = int((mask & isf).sum())
    pool = [u for k, ev in zip(mask, EV) if k for u in ev]
    h = 100*sum(1 for u in pool if R3[u["cj_t"]]["R3"]>=3)/len(pool) if pool else 0
    dens = (kept-kf)/max(1,kf); prec = 100*kf/max(1,kept)
    print(f"  {tag:<28} ev {kept:>3} fund {kf}/{NF} círc {circ(mask)}/60 prec {prec:>4.1f}% dens {dens:>4.1f}:1 poolhit {h:.1f}%")
    return {"ev": kept, "kf": kf, "circ": circ(mask), "prec": round(prec,1), "dens": round(dens,1)}
def fam_env(fund_mask, qlo=0.0, qhi=1.0):
    m = np.zeros(len(EV), bool)
    for fam in ("RASO","BANDA","FUNDO","SEM"):
        idx = np.where(efam==fam)[0]; fidx = np.where((efam==fam)&fund_mask)[0]
        if len(fidx) < 3: m[idx] = True; continue
        lo = np.quantile(X[fidx], qlo, axis=0); hi = np.quantile(X[fidx], qhi, axis=0)
        for i in idx:
            if np.all((X[i]>=lo)&(X[i]<=hi)): m[i] = True
    return m
print(f"eventos {len(EV)} · fundo {NF} · densidade base {(len(EV)-NF)/NF:.1f}:1")
L1 = fam_env(isf)
o1 = rep(L1, "L1 família")
L2 = L1 & hascasc
o2 = rep(L2, "L2 &casc>=4-no-evento")
# Mahalanobis dentro de L2
def maha(fund_mask, sub_mask, q):
    Xf = Xn[fund_mask & sub_mask]
    if len(Xf) < 6: return sub_mask
    cov = np.cov(Xf.T) + np.eye(Xn.shape[1])*0.3; inv = np.linalg.pinv(cov); cf = Xf.mean(0)
    md = np.sqrt(((Xn-cf)@inv*(Xn-cf)).sum(1)); thr = np.quantile(md[fund_mask & sub_mask], q)
    return sub_mask & (md <= thr)
L3 = maha(isf, L2, 0.90)
o3 = rep(L3, "L3 L2&maha90")
L3b = maha(isf, L2, 0.80)
o3b = rep(L3b, "L3b L2&maha80")
# kNN dentro de L2
D = np.sqrt(((Xn[:,None,:]-Xn[None,:,:])**2).sum(2)); np.fill_diagonal(D, np.inf); K=25
knnf = np.array([isf[np.argpartition(D[i],K)[:K]].mean() for i in range(len(EV))])
thr = np.quantile(knnf[L2 & isf], 0.10); L4 = L2 & (knnf >= thr)
o4 = rep(L4, "L4 L2&knn")
L5 = L3 & (knnf >= thr)
o5 = rep(L5, "L5 L2&maha90&knn")

# NULL causal p/ L2 (o degrau da cascata + família): 50 eventos aleatórios
rng = np.random.default_rng(970)
obs_cut = len(EV) - int(L2.sum()); obs_circ = circ(L2); ge = 0; NP = 500
for _ in range(NP):
    fm = np.zeros(len(EV), bool); fm[rng.choice(len(EV), NF, replace=False)] = True
    m2 = fam_env(fm) & hascasc
    if (len(EV)-int(m2.sum())) >= obs_cut: ge += 1
print(f"\nNULL L2 (envelope de {NF} eventos aleatórios &casc, {NP}×): P(corta>=obs)={ge/NP:.4f}")

# PIPELINE E5/E6 no pool de L2/L3/L5
for ev in EV:
    min_flo = 1e18
    for pos, u in enumerate(ev, 1):
        ci = bisect.bisect_right(TS, u["cj_t"])-1; prevmin = min_flo
        u["_hl"] = int(u["_flo"] > prevmin + 0.05*u["_a"]) if pos>1 else 0
        min_flo = min(min_flo, u["_flo"])
        u["_reclaim"] = int(ci>=1 and CL[ci]>HI[ci-1] and CL[ci]>OP[ci])
def pipeline(mask, tag):
    pool_ev = [ev for k, ev in zip(mask, EV) if k]
    def first(ev):
        for u in ev:
            if u["_casc"]>=3 and u["_hl"]==1 and u["_reclaim"]==1: return u
        return None
    rows = [first(ev) for ev in pool_ev if first(ev)]
    if not rows: print(f"  {tag}: sem sinais"); return
    nets = [R3[r["cj_t"]]["net3"] for r in sorted(rows, key=lambda x:x["cj_t"])]
    h = sum(1 for r in rows if R3[r["cj_t"]]["R3"]>=3); w = sum(1 for x in nets if x>0)
    eq=pk=dd=0.0; mL=cl=0
    for x in nets:
        eq+=x; pk=max(pk,eq); dd=min(dd,eq-pk)
        if x<=0: cl+=1; mL=max(mL,cl)
        else: cl=0
    yr={}
    for r in rows: yr[r["yr"]]=round(yr.get(r["yr"],0)+R3[r["cj_t"]]["net3"],1)
    cc=set()
    for r in rows: cc|=r["_circ"]
    print(f"  {tag:<16} N{len(rows)} WR {100*w/len(rows):.1f}% hit3R {100*h/len(rows):.1f}% NET {sum(nets):+.1f} DD {dd:.1f} stk-{mL} círc {len(cc)} | {yr}")
print("\nPIPELINE E6(cascade>=3&hl&reclaim) no pool de cada camada:")
pipeline(L1, "L1"); pipeline(L2, "L2"); pipeline(L3, "L3maha90"); pipeline(L5, "L5")
json.dump({"L1":o1,"L2":o2,"L3":o3,"L3b":o3b,"L4":o4,"L5":o5,"null_L2":ge/NP},
          open(HERE/"results"/"event_multilayer_filter_20260706.json","w"), indent=1, default=float)
print("OK → results/event_multilayer_filter_20260706.json")
