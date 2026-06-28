#!/usr/bin/env python3
"""SCORER determinístico p/ o engine multi-agente. Sobre a base APROVADA swept-sempre + h1_pos>=0.44 (sempre ON),
aplica um COMBO de cortes de lente {feat,dir,q} e devolve painel + losers/runners cortados + NULL (corte aleatório
mesmo N, p p/ avgR). Uso: python3 score_lens.py '[{"feat":"pos_recent20","dir":"hi","q":0.25}, ...]'
dir=hi mantém feat>=quantil(q) (corta cauda baixa=loser); dir=lo mantém feat<=quantil(1-q). Math single-source."""
import json,sys,statistics as st,random
from pathlib import Path
HERE=Path(__file__).parent
RECS=[json.loads(l) for l in (HERE/"sweptsempre_micro.jsonl").read_text().splitlines()]
for r in RECS:
    r["_F"]={**r["micro"],**{k:v for k,v in r["feat"].items() if isinstance(v,(int,float))}}
AVAIL=sorted(set().union(*[set(r["_F"].keys()) for r in RECS]))
H=[r for r in RECS if r.get("h1_pos",0.5)>=0.44]  # h1_pos sempre aplicado
def quant(vals,q):
    vs=sorted(vals); i=min(len(vs)-1,max(0,int(q*len(vs)))); return vs[i]
def apply(combo,pool):
    kept=pool
    for c in combo:
        ft=c["feat"]; d=c.get("dir","hi"); q=c.get("q",0.25)
        vals=[r["_F"][ft] for r in kept if ft in r["_F"] and r["_F"][ft] is not None]
        if len(vals)<10: continue
        if d=="hi": thr=quant(vals,q); kept=[r for r in kept if r["_F"].get(ft) is None or r["_F"][ft]>=thr]
        else: thr=quant(vals,1-q); kept=[r for r in kept if r["_F"].get(ft) is None or r["_F"][ft]<=thr]
    return kept
def panel(rows):
    R=[x["R"] for x in sorted(rows,key=lambda z:z["cj_t"])]; n=len(R)
    if not n: return None
    sm=sum(R); w=sum(1 for x in R if x>0); eq=pk=dd=0
    for x in R: eq+=x; pk=max(pk,eq); dd=min(dd,eq-pk)
    py={y:round(sum(x["R"] for x in rows if x["yr"]==y),1) for y in (2024,2025,2026)}
    return {"N":n,"WR":round(100*w/n,1),"sumR":round(sm,1),"avgR":round(sm/n,3),"DD":round(dd,1),
            "losers":sum(1 for x in R if x<=0),"runners":sum(1 for x in R if x>=3),"yr":py}
def main():
    if len(sys.argv)<2:
        print(json.dumps({"available_features":AVAIL,"h1_base":panel(H)},indent=2)); return
    combo=json.loads(sys.argv[1])
    base=panel(H); kept=apply(combo,H); k=panel(kept)
    if not k: print(json.dumps({"error":"vazio"})); return
    dl=base["losers"]-k["losers"]; dr=base["runners"]-k["runners"]
    # NULL: remover mesmo nº aleatório de H, 500 reps
    ncut=base["N"]-k["N"]; rng=random.Random(20260628); avs=[]; dds=[]
    for _ in range(500):
        idx=set(rng.sample(range(len(H)),ncut)) if 0<ncut<len(H) else set()
        kk=[H[i] for i in range(len(H)) if i not in idx]; pp=panel(kk)
        if pp: avs.append(pp["avgR"]); dds.append(pp["DD"])
    p_avg=round(sum(1 for x in avs if x>=k["avgR"])/len(avs),3) if avs else 1.0
    out={"combo":combo,"h1_base":base,"after":k,"losers_cut":dl,"runners_cut":dr,
         "efic_losL_per_runL":round(dl/dr,1) if dr>0 else 99.9,
         "null_avgR_mean":round(st.mean(avs),3) if avs else None,"null_p_avgR_random_ge":p_avg,
         "verdict_hint":"PASS" if (p_avg<0.05 and dr<=dl*0.15 and k["avgR"]>=base["avgR"] and all(v>=0 for v in k["yr"].values())) else "CHECK"}
    print(json.dumps(out,indent=2,ensure_ascii=False))
if __name__=="__main__": main()
