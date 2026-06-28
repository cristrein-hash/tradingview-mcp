#!/usr/bin/env python3
"""SCORER de fluxo p/ engine multi-agente NAS/Bubbles/OB. Base = SUBSTRATO #4 (substrate4_flow.jsonl, N448).
Aplica combo de cortes {feat,dir,q} e devolve painel + losers/runners cortados + NULL (corte aleatório mesmo N) +
per-year. Uso: python3 score_flow.py '[{"feat":"clean_sky_atr","dir":"hi","q":0.25}]'  (sem arg lista features+base)
dir=hi mantém feat>=quantil(q); dir=lo mantém feat<=quantil(1-q); dir=eq1 mantém feat==1; dir=eq0 mantém feat==0."""
import json,sys,statistics as st,random
from pathlib import Path
HERE=Path(__file__).parent
RECS=[json.loads(l) for l in (HERE/"substrate4_flow.jsonl").read_text().splitlines()]
for r in RECS: r["_F"]=r["flow"]
AVAIL=sorted(RECS[0]["flow"].keys())
def quant(vals,q):
    vs=sorted(vals); return vs[min(len(vs)-1,max(0,int(q*len(vs))))] if vs else 0
def apply(combo,pool):
    kept=pool
    for c in combo:
        ft=c["feat"]; d=c.get("dir","hi"); q=c.get("q",0.25)
        vals=[r["_F"][ft] for r in kept if r["_F"].get(ft) is not None]
        if len(vals)<8 and d in("hi","lo"): continue
        if d=="hi": thr=quant(vals,q); kept=[r for r in kept if r["_F"].get(ft) is None or r["_F"][ft]>=thr]
        elif d=="lo": thr=quant(vals,1-q); kept=[r for r in kept if r["_F"].get(ft) is None or r["_F"][ft]<=thr]
        elif d=="eq1": kept=[r for r in kept if r["_F"].get(ft)==1]
        elif d=="eq0": kept=[r for r in kept if r["_F"].get(ft)==0]
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
    base=panel(RECS)
    if len(sys.argv)<2:
        print(json.dumps({"available_features":AVAIL,"substrate4_base":base},indent=2)); return
    combo=json.loads(sys.argv[1]); kept=apply(combo,RECS); k=panel(kept)
    if not k: print(json.dumps({"error":"vazio"})); return
    dl=base["losers"]-k["losers"]; dr=base["runners"]-k["runners"]; ncut=base["N"]-k["N"]
    rng=random.Random(20260628); avs=[]; dds=[]
    for _ in range(500):
        idx=set(rng.sample(range(len(RECS)),ncut)) if 0<ncut<len(RECS) else set()
        kk=[RECS[i] for i in range(len(RECS)) if i not in idx]; pp=panel(kk)
        if pp: avs.append(pp["avgR"]); dds.append(pp["DD"])
    p_avg=round(sum(1 for x in avs if x>=k["avgR"])/len(avs),3) if avs else 1.0
    yrs=list(k["yr"].values())
    out={"combo":combo,"base":base,"after":k,"losers_cut":dl,"runners_cut":dr,
         "efic_losL_per_runL":round(dl/dr,1) if dr>0 else 99.9,
         "null_p_avgR_random_ge":p_avg,"all_years_pos":all(v>=0 for v in yrs),
         "verdict_hint":"PASS" if (p_avg<0.02 and dr<=dl*0.15 and k["avgR"]>=base["avgR"] and all(v>=0 for v in yrs) and dl>=8) else "CHECK"}
    print(json.dumps(out,indent=2,ensure_ascii=False))
if __name__=="__main__": main()
