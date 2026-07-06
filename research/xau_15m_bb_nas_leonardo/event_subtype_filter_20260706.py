#!/usr/bin/env python3
"""FILTRO POR SUB-TIPO DE FUNDO (2026-07-06). Os 60 fundos são heterogéneos — um filtro global
perde-os (cascata pega só 7/60). Correção: clusterizar os sub-tipos de fundo (k-means causal-feat)
e manter eventos PERTO de ALGUM sub-tipo → mantém todos os 60 (cada fundo no seu cluster) e corta o
espaço vazio entre clusters. Baixar densidade mantendo recall.
CONSTRUÇÃO: k-means (numpy) dos eventos-fundo no espaço causal-z (k=4/5/6). Distância de cada evento
ao centroide de fundo mais próximo. Manter dist<=threshold (calibrado por recall alvo). Curva
recall×densidade×precisão. + combinar com cascata. NULL: k-means de K aleatórios, mesma medição.
SEM look-ahead (features<=cj; outcome nunca na decisão).
SANITY_PROBE: features causais até 3º cand; k-means só nos fundos (calibração declarada); dist ao
cluster-fundo mais próximo; null permuta rótulo-fundo; recall círculo distinto."""
import json, bisect, hashlib
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
for u in UNIV:
    u["_flo"] = u["g_sl"] + 0.1*(u.get("g_atr") or 5.0); u["_a"] = u.get("g_atr") or 5.0; u["_circ"] = set(); u["_F"] = CACHE[u["cj_t"]]; u["_casc"] = cascade(u["cj_t"])
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
FEATS9 = True
def vec(ev):
    sub = ev[:3]; F = [u["_F"] for u in sub]
    st_i = bisect.bisect_right(TS, ev[0]["cj_t"])-1; a = ev[0]["_a"]; pre_hi = max(HI[max(0,st_i-96):st_i+1]); ei = bisect.bisect_right(TS, sub[-1]["cj_t"])-1
    return [min(f["rsi_min8"] for f in F), min(f["nas_dist"] for f in F), max(f["sell_climax4"] for f in F), max(f["below_poc"] for f in F),
            min(f["poc_dist"] for f in F), max(f["nas_long_rec"] for f in F), max(f["vol_climax"] for f in F), max(f["flow_divergence"] for f in F),
            (pre_hi-min(LO[max(0,st_i-8):ei+1]))/a, max(u["_casc"] for u in ev[:6])]
for ev in EV:
    ev[0]["_vec"] = vec(ev); ev[0]["_isf"] = any(u["_circ"] for u in ev)
    c = set()
    for u in ev: c |= u["_circ"]
    ev[0]["_cs"] = c
X = np.array([ev[0]["_vec"] for ev in EV]); isf = np.array([ev[0]["_isf"] for ev in EV]); NF = int(isf.sum())
mu = X.mean(0); sd = X.std(0); sd[sd==0]=1; Xn = (X-mu)/sd
def kmeans(P, k, seed, iters=50):
    rng = np.random.default_rng(seed); C = P[rng.choice(len(P), k, replace=False)]
    for _ in range(iters):
        d = np.sqrt(((P[:,None,:]-C[None,:,:])**2).sum(2)); lab = d.argmin(1)
        Cn = np.array([P[lab==j].mean(0) if (lab==j).any() else C[j] for j in range(k)])
        if np.allclose(Cn, C): break
        C = Cn
    return C
def circ(mask):
    c = set()
    for k, ev in zip(mask, EV):
        if k: c |= ev[0]["_cs"]
    return len(c)
def rep(mask, tag):
    kept=int(mask.sum()); kf=int((mask&isf).sum()); pool=[u for k,ev in zip(mask,EV) if k for u in ev]
    h=100*sum(1 for u in pool if R3[u["cj_t"]]["R3"]>=3)/len(pool) if pool else 0
    dens=(kept-kf)/max(1,kf); prec=100*kf/max(1,kept)
    print(f"  {tag:<26} ev {kept:>3} fund {kf}/{NF} círc {circ(mask):>2}/60 prec {prec:>4.1f}% dens {dens:>4.1f}:1 poolhit {h:.1f}%")
    return {"ev":kept,"kf":kf,"circ":circ(mask),"prec":round(prec,1),"dens":round(dens,1)}
print(f"eventos {len(EV)} · fundo {NF} · densidade base {(len(EV)-NF)/NF:.1f}:1")
Xf = Xn[isf]
out = {}
for k in (4, 5, 6):
    C = kmeans(Xf, k, 30+k)
    dall = np.sqrt(((Xn[:,None,:]-C[None,:,:])**2).sum(2)).min(1)  # dist ao centroide-fundo mais próximo
    df = dall[isf]
    print(f"\nk-means k={k} (dist ao sub-tipo mais próximo):")
    for q, lab in ((1.0,"recall100"), (0.95,"recall95"), (0.90,"recall90"), (0.85,"recall85"), (0.80,"recall80")):
        thr = np.quantile(df, q); mask = dall <= thr
        out[f"k{k}_{lab}"] = rep(mask, f"k{k} {lab}")

# melhor: k=5 recall90 — null causal
C = kmeans(Xf, 5, 35); dall = np.sqrt(((Xn[:,None,:]-C[None,:,:])**2).sum(2)).min(1)
thr = np.quantile(dall[isf], 0.90); mask90 = dall <= thr; obs_cut = len(EV)-int(mask90.sum())
rng = np.random.default_rng(980); ge=0; NP=300
for _ in range(NP):
    fm = np.zeros(len(EV), bool); fm[rng.choice(len(EV), NF, replace=False)]=True
    C2 = kmeans(Xn[fm], 5, int(rng.integers(1,1e6))); d2 = np.sqrt(((Xn[:,None,:]-C2[None,:,:])**2).sum(2)).min(1)
    thr2 = np.quantile(d2[fm], 0.90)
    if (len(EV)-int((d2<=thr2).sum())) >= obs_cut: ge+=1
print(f"\nNULL k5-recall90 (k-means de {NF} aleatórios, {NP}×): P(corta>=obs)={ge/NP:.4f}")

# pipeline E6 no pool k5-recall90
for ev in EV:
    min_flo=1e18
    for pos,u in enumerate(ev,1):
        ci=bisect.bisect_right(TS,u["cj_t"])-1; prevmin=min_flo
        u["_hl"]=int(u["_flo"]>prevmin+0.05*u["_a"]) if pos>1 else 0; min_flo=min(min_flo,u["_flo"])
        u["_reclaim"]=int(ci>=1 and CL[ci]>HI[ci-1] and CL[ci]>OP[ci])
def pipeline(mask, tag):
    pe=[ev for k,ev in zip(mask,EV) if k]
    def fst(ev):
        for u in ev:
            if u["_casc"]>=3 and u["_hl"]==1 and u["_reclaim"]==1: return u
        return None
    rows=[fst(ev) for ev in pe if fst(ev)]
    if not rows: print(f"  {tag}: sem sinais"); return
    nets=[R3[r["cj_t"]]["net3"] for r in sorted(rows,key=lambda x:x["cj_t"])]
    h=sum(1 for r in rows if R3[r["cj_t"]]["R3"]>=3); w=sum(1 for x in nets if x>0)
    eq=pk=dd=0.0; mL=cl=0
    for x in nets:
        eq+=x;pk=max(pk,eq);dd=min(dd,eq-pk)
        if x<=0: cl+=1;mL=max(mL,cl)
        else: cl=0
    yr={}
    for r in rows: yr[r["yr"]]=round(yr.get(r["yr"],0)+R3[r["cj_t"]]["net3"],1)
    cc=set()
    for r in rows: cc|=r["_circ"]
    print(f"  {tag:<16} N{len(rows)} WR {100*w/len(rows):.1f}% hit3R {100*h/len(rows):.1f}% NET {sum(nets):+.1f} DD {dd:.1f} stk-{mL} círc {len(cc)} | {yr}")
print("\nPIPELINE E6 no pool k5-recall90:")
pipeline(mask90, "k5-r90")
json.dump(out, open(HERE/"results"/"event_subtype_filter_20260706.json","w"), indent=1, default=float)
print("OK → results/event_subtype_filter_20260706.json")
