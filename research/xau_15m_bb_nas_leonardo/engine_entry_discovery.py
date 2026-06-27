#!/usr/bin/env python3
"""ENGINE 2 — Phase D discovery (Cris 2026-06-27). Fonte ÚNICA de métrica. Alvo: ENTRAR nos fundos MON+FORTE
e EVITAR MED+FRACO (e ruído NONE), de um fluxo causal de 4502 mínimas fractais (base MON+FORTE=1,3%).
Por feature: AUC p/ is_monforte. Combos 2-3 (threshold=quantil dir. AUC): maximiza PRECISÃO MON+FORTE com recall>=alvo,
reportando contaminação MED/FRACO e NONE, por-ano e leave-block. Não promove; ranqueia frontier. -> entry_discovery_report.txt+.json"""
import json,statistics as st
from pathlib import Path
from itertools import combinations
HERE=Path(__file__).parent
ROWS=[json.loads(l) for l in (HERE/"entry_candidates.jsonl").read_text().splitlines()]
META={'block','t','cj_t','yr','label','is_monforte','is_medfraco','is_bottom'}
NUMF=[k for k in ROWS[0] if k not in META and isinstance(ROWS[0][k],(int,float))]
N=len(ROWS); MF=sum(r["is_monforte"] for r in ROWS); base=MF/N
print(f"N={N} | MON+FORTE={MF} (base {100*base:.2f}%) | MED+FRACO={sum(r['is_medfraco'] for r in ROWS)} | NONE={sum(1 for r in ROWS if r['label']=='NONE')}")

def auc(feat):
    vv=[(r[feat],r["is_monforte"]) for r in ROWS if r.get(feat) is not None]
    pos=[v for v,y in vv if y]; neg=[v for v,y in vv if not y]
    if not pos or not neg: return .5
    sv=sorted(vv,key=lambda x:x[0]); vals=[v for v,_ in sv]; ranks=[0]*len(vals); j=0
    while j<len(vals):
        k=j
        while k+1<len(vals) and vals[k+1]==vals[j]: k+=1
        rr=(j+k)/2+1
        for m in range(j,k+1): ranks[m]=rr
        j=k+1
    rsp=sum(ranks[m] for m in range(len(sv)) if sv[m][1]==1)
    return (rsp-len(pos)*(len(pos)+1)/2)/(len(pos)*len(neg))

aucs=sorted(((f,auc(f)) for f in NUMF),key=lambda x:-abs(x[1]-.5))
print("\n=== SINGLE features: AUC p/ is_monforte (|AUC-.5| desc) — top 16 ===")
for f,a in aucs[:16]: print(f"  {f:<20}{a:.3f}  ({'+' if a>=.5 else '-'})")

TOP=[f for f,a in aucs[:16]]
dirn={f:(1 if a>=.5 else -1) for f,a in aucs}
# thresholds = quantil que isola a cauda favorável (top/bottom ~40%)
def thr(f,q):
    vals=sorted(r[f] for r in ROWS if r.get(f) is not None)
    return vals[int(q*len(vals))]
TH={f:(thr(f,0.60) if dirn[f]>0 else thr(f,0.40)) for f in TOP}
def passes(r,f):
    v=r.get(f)
    if v is None: return False
    return v>=TH[f] if dirn[f]>0 else v<=TH[f]
def evalsel(sel):
    n=len(sel)
    if n==0: return None
    mf=sum(r["is_monforte"] for r in sel); mfr=sum(r["is_medfraco"] for r in sel); non=sum(1 for r in sel if r["label"]=="NONE")
    return {"n":n,"prec_mf":round(mf/n,3),"recall_mf":round(mf/MF,3),"mf":mf,"medfraco":mfr,
            "contam_mf_vs_medfraco":round(mf/mfr,2) if mfr else 99,"none_pc":round(non/n,2),"lift":round((mf/n)/base,1)}
combos=[]
for sz in (2,3):
    for cc in combinations(TOP,sz):
        sel=[r for r in ROWS if all(passes(r,f) for f in cc)]
        m=evalsel(sel)
        if m and m["mf"]>=12 and m["recall_mf"]>=0.20:   # recall mínimo razoável
            m["combo"]=cc; combos.append(m)
combos.sort(key=lambda x:(-x["prec_mf"],-x["recall_mf"]))

def peryear(cc):
    out={}
    for y in (2024,2025,2026):
        sel=[r for r in ROWS if r["yr"]==y and all(passes(r,f) for f in cc)]
        mf=sum(r["is_monforte"] for r in sel); out[y]=f"{mf}/{len(sel)}"
    return out
def lb_minprec(cc):
    ps=[]
    for blk in sorted(set(r["block"] for r in ROWS)):
        sel=[r for r in ROWS if r["block"]!=blk and all(passes(r,f) for f in cc)]
        if sel: ps.append(sum(r["is_monforte"] for r in sel)/len(sel))
    return round(min(ps),3) if ps else 0

print(f"\n=== COMBOS 2-3 — PRECISÃO MON+FORTE (base {100*base:.2f}%), recall>=20%, mf>=12 — top 14 ===")
print(f"{'combo':<46}{'n':>4}{'prec':>6}{'lift':>5}{'rec':>5}{'mf':>4}{'mfrac':>6}{'none%':>6}{'lbPrec':>7}")
for c in combos[:14]:
    print(f"{'+'.join(x[:13] for x in c['combo']):<46}{c['n']:>4}{c['prec_mf']:>6}{c['lift']:>5}{c['recall_mf']:>5}{c['mf']:>4}{c['medfraco']:>6}{c['none_pc']:>6}{lb_minprec(c['combo']):>7}")
if combos:
    best=combos[0]; print(f"\nbest por ano (mf/n): {peryear(best['combo'])}  combo={best['combo']}")
json.dump({"base":base,"MF":MF,"singles":[(f,a) for f,a in aucs],"combos":[{k:v for k,v in c.items()} for c in combos[:40]]},
          open(HERE/"entry_discovery.json","w"),default=str,indent=1)
out=[f"N={N} MON+FORTE={MF} base={100*base:.2f}%"]
out.append("SINGLES:"+", ".join(f"{f}:{a:.3f}" for f,a in aucs[:16]))
out.append("\nCOMBOS (prec/lift/recall/mf/medfraco/none%/lbPrec):")
for c in combos[:20]: out.append(f"{'+'.join(c['combo'])}: n{c['n']} prec{c['prec_mf']} lift{c['lift']} rec{c['recall_mf']} mf{c['mf']} medfraco{c['medfraco']} none{c['none_pc']} lb{lb_minprec(c['combo'])}")
(HERE/"entry_discovery_report.txt").write_text("\n".join(out))
print("\n-> entry_discovery_report.txt + entry_discovery.json")
