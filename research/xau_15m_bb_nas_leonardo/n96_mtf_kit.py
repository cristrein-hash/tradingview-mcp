#!/usr/bin/env python3
"""KIT MTF partilhado — N96 loser discrimination, TODOS indicadores × TODOS TFs, RAW-native (2026-07-08).
Fontes canonicas (zero resample, zero Fractal-MTF, zero SLIM):
  15M: primitives/ (RAW-15M lineage, source guard PASS) + bubbles/ (Market Order Bubbles)
  30M/1H: htf_primitives/XAUUSD_{30m,60m}_* (RAW nativo, extractor validado build_30m1h_primitives)
  4H/1D: htf_primitives/htf_{4H,1D} (RAW nativo, build_htf_primitives)
Cada TF traz: series(OHLC+RSI+ATR+EMA21[+SVP POC/VAH/VAL em 4H/1D]), smc_events(BOS/CHoCH/EQH/EQL),
nas_events(LONG/SHORT), zones(Custom OB DEMAND/SUPPLY, born_t/last_t lifecycle).
CAUSAL: acessores usam so barras/eventos/zonas com t/born_t < entry_t (barra HTF corrente EXCLUIDA;
zonas por born_t, NUNCA last_t). Bubbles por known_at<=entry_t.
Familias CORRIGIDAS pelo Cris. Helpers: disc(feat_by_n), oof_mining_null(X)."""
import json, glob, bisect, sys
import numpy as np, statistics as st
sys.path.insert(0,"/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo")
from agent_ctx_kit import S,TS,HI,LO,CL,ATR,EMA,RSI,N,ENTRIES,score
HERE="/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo"
assert len(ENTRIES)==96 and sum(e["out"] for e in ENTRIES)==52, "N96 nao reproduz"
# ---- familias CORRIGIDAS (Cris) ----
FAM={"MGMT":{24,32,64,77},   # nao-filtrar (gestao/BE/timing)
     "C":{17,18,20,21,23,25,31,36,42,46,48,55,56,57,58,59,60,65,79,83,84,85},  # distribuicao/topo-range-bear
     "D":{27,49,50,66,67,68,69,80,86,87,89,92,93,94},  # bear ativo
     "R":{5,6,7,8}}          # range neutro
def famof(n):
    for k,s in FAM.items():
        if n in s: return k
    return "WIN"
# ---- fontes multi-TF ----
def _load(files):
    ser={}; smc=[]; nas=[]; zones=[]
    for f in files:
        d=json.load(open(f))
        for b in d["series"]: ser[b["t"]]=b
        smc+=[e for e in d.get("smc_events",[]) if e.get("t")]
        nas+=[e for e in d.get("nas_events",[]) if e.get("t")]
        zones+=[z for z in d.get("zones",[]) if z.get("born_t")]
    S2=sorted(ser.values(),key=lambda b:b["t"])
    return {"ser":S2,"t":[b["t"] for b in S2],"smc":sorted(smc,key=lambda e:e["t"]),
            "smct":[e["t"] for e in sorted(smc,key=lambda e:e["t"])],
            "nas":sorted(nas,key=lambda e:e["t"]),"nast":[e["t"] for e in sorted(nas,key=lambda e:e["t"])],
            "zones":sorted(zones,key=lambda z:z["born_t"]),"zborn":[z["born_t"] for z in sorted(zones,key=lambda z:z["born_t"])]}
TF={
 "15M":{"ser":S,"t":TS,**{k:_load(sorted(glob.glob(HERE+"/primitives/*.primitives.json")))[k] for k in ("smc","smct","nas","nast","zones","zborn")}},
 "30M":_load(sorted(glob.glob(HERE+"/htf_primitives/XAUUSD_30m_*.primitives.json"))),
 "1H": _load(sorted(glob.glob(HERE+"/htf_primitives/XAUUSD_60m_*.primitives.json"))),
 "4H": _load([HERE+"/htf_primitives/htf_4H.primitives.json"]),
 "1D": _load([HERE+"/htf_primitives/htf_1D.primitives.json"]),
}
BARSEC={"15M":900,"30M":1800,"1H":3600,"4H":4*3600,"1D":24*3600}
# ---- 15M bubbles (Market Order Bubbles) ----
BUB=sorted([json.loads(l) for f in glob.glob(HERE+"/bubbles/*.jsonl") for l in open(f)], key=lambda x:(x.get("known_at") or x["t"]))
BUBK=[(x.get("known_at") or x["t"]) for x in BUB]
# ---- acessores CAUSAIS ----
def bars_upto(tf, t):
    """barras da serie TF FECHADAS antes de t (t_bar+bar_sec<=t). Barra corrente EXCLUIDA."""
    T=TF[tf]; hi=bisect.bisect_right(T["t"], t-BARSEC[tf]); return T["ser"][:hi]
def smc_upto(tf, t, lookback_bars=None):
    T=TF[tf]; hi=bisect.bisect_right(T["smct"], t)
    lo=0 if lookback_bars is None else bisect.bisect_left(T["smct"], t-lookback_bars*BARSEC[tf])
    return T["smc"][lo:hi]
def nas_upto(tf, t, lookback_bars=None):
    T=TF[tf]; hi=bisect.bisect_right(T["nast"], t)
    lo=0 if lookback_bars is None else bisect.bisect_left(T["nast"], t-lookback_bars*BARSEC[tf])
    return T["nas"][lo:hi]
def zones_upto(tf, t):
    """zonas nascidas ANTES de t (causal born_t; NUNCA last_t)."""
    T=TF[tf]; hi=bisect.bisect_right(T["zborn"], t); return T["zones"][:hi]
def bubbles_upto(t, lookback_bars=None):
    hi=bisect.bisect_right(BUBK, t)
    if lookback_bars is None: return BUB[:hi]
    return [BUB[k] for k in range(hi) if BUB[k]["t"]>=t-lookback_bars*900]
# ---- helper de discriminacao ----
def _auc(a,b):
    if not a or not b: return 0.5
    c=t=0
    for x in a:
        for y in b:
            t+=1; c+= 1 if x>y else (0.5 if x==y else 0)
    return c/t
def disc(feat_by_n):
    """feat_by_n: {n: valor}. Devolve medianas WIN/C/D/R/MGMT + AUC(WIN vs cada familia perdedora)."""
    byfam={f:[feat_by_n[e["n"]] for e in ENTRIES if famof(e["n"])==f and feat_by_n.get(e["n"]) is not None] for f in ("WIN","C","D","R","MGMT")}
    def m(x): return round(st.median(x),3) if x else None
    return {"med":{f:m(v) for f,v in byfam.items()},
            "auc_vs_win":{f:round(_auc(byfam["WIN"],byfam[f]),3) for f in ("C","D","R","MGMT")},
            "n":{f:len(v) for f,v in byfam.items()}}
# ---- OOF + mining-null (para candidatas a filtro) ----
_NS=[e["n"] for e in ENTRIES]; _Y=np.array([e["out"] for e in ENTRIES],dtype=float)
def _fit(X,y,l2=1.0,s=300,lr=0.3):
    w=np.zeros(X.shape[1]);b=0.0;m=len(y)
    for _ in range(s):
        p=1/(1+np.exp(-(X@w+b)));g=p-y;w-=lr*(X.T@g/m+l2*w/m);b-=lr*g.mean()
    return w,b
def _loo(Xs,y):
    P=np.zeros(len(y))
    for t in range(len(y)):
        idx=np.arange(len(y))!=t;w,b=_fit(Xs[idx],y[idx]);P[t]=1/(1+np.exp(-(Xs[t]@w+b)))
    return P
def oof_mining_null(X, nperm=200, seed=7):
    """X: (96 x k) na ordem de ENTRIES. LOO logistic keep=prob>0.5 + mining-null. In-sample NAO conta."""
    X=np.asarray(X,dtype=float); y=_Y.copy()
    mu=X.mean(0);sd=X.std(0)+1e-9;Xs=(X-mu)/sd
    P=_loo(Xs,y);keep=P>0.5
    if keep.sum()==0: return {"oof_hit":0,"N_keep":0}
    sc=score([int(n) for n,k in zip(_NS,keep) if k]);obs=sc["hit3r_kept"]
    rng=np.random.default_rng(seed);vals=[]
    for _ in range(nperm):
        yp=rng.permutation(y);Pp=_loo(Xs,yp);kp=Pp>0.5
        if kp.sum(): vals.append(yp[kp].mean())
    vals=np.array(vals);pv=float((vals>=obs).mean())
    return {"oof_hit":round(obs,3),"base":0.542,"N_keep":sc["N_kept"],"poison":sc["poison_ratio"],
            "y2025":sc["y2025"],"y2026":sc["y2026"],"mining_null_p":round(pv,3),
            "verdict":"SINAL" if (pv<0.1 and obs>0.542) else "NO_EDGE_OOF"}
if __name__=="__main__":
    print("TF bars:",{tf:len(TF[tf]["ser"]) for tf in TF},"| zones:",{tf:len(TF[tf]["zones"]) for tf in TF})
    print("bubbles:",len(BUB),"| ENTRIES 96 | FAM C%d D%d R%d MGMT%d"%(len(FAM["C"]),len(FAM["D"]),len(FAM["R"]),len(FAM["MGMT"])))
