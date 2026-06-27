#!/usr/bin/env python3
"""DA Engine2 test #5 — FEATURE DIRECTION sanity. legpos90 AUC=0.218 in Eng2 (low legpos->MON+FORTE among 4502)
but Eng1 said high legpos->strong among 199 bottoms. Universe artifact? Compare legpos distributions:
  - MON+FORTE (58) vs MED/FRACO (139) vs NONE (4305)
  - restrict to is_bottom: AUC legpos for is_monforte WITHIN bottoms (Eng1 universe)
Determine whether the flip is a NONE-universe artifact and whether fingerprint transfer is undermined.
-> _DA_entry2_featdir.json"""
import json,statistics as st
from pathlib import Path
HERE=Path(__file__).parent
ROWS=[json.loads(l) for l in (HERE/"entry_candidates.jsonl").read_text().splitlines()]
def auc(rows,feat,lab):
    vv=[(r[feat],r[lab]) for r in rows if r.get(feat) is not None]
    pos=[v for v,y in vv if y]; neg=[v for v,y in vv if not y]
    if not pos or not neg: return None
    sv=sorted(vv,key=lambda x:x[0]); vals=[v for v,_ in sv]; ranks=[0]*len(vals); j=0
    while j<len(vals):
        k=j
        while k+1<len(vals) and vals[k+1]==vals[j]: k+=1
        rr=(j+k)/2+1
        for m in range(j,k+1): ranks[m]=rr
        j=k+1
    rsp=sum(ranks[m] for m in range(len(sv)) if sv[m][1]==1)
    return (rsp-len(pos)*(len(pos)+1)/2)/(len(pos)*len(neg))
def desc(rows,feat):
    vs=[r[feat] for r in rows if r.get(feat) is not None]
    return {"n":len(vs),"mean":round(st.mean(vs),3),"median":round(st.median(vs),3)} if vs else None
OUT={}
for feat in ("legpos90","legpos60"):
    mf=[r for r in ROWS if r["is_monforte"]]; mfr=[r for r in ROWS if r["is_medfraco"]]
    none=[r for r in ROWS if r["label"]=="NONE"]; bot=[r for r in ROWS if r["is_bottom"]]
    print(f"\n=== {feat} ===")
    print(f"  MON+FORTE : {desc(mf,feat)}")
    print(f"  MED/FRACO : {desc(mfr,feat)}")
    print(f"  NONE      : {desc(none,feat)}")
    print(f"  ALL bottoms: {desc(bot,feat)}")
    auc_full=auc(ROWS,feat,"is_monforte")           # Eng2 universe (vs all 4502)
    auc_within=auc(bot,feat,"is_monforte")          # Eng1 universe (MF vs MEDFRACO among 197 bottoms)
    auc_mf_vs_none=auc([r for r in ROWS if r["is_monforte"] or r["label"]=="NONE"],feat,"is_monforte")
    print(f"  AUC(is_monforte | ALL 4502)         = {auc_full:.3f}  [Eng2]")
    print(f"  AUC(is_monforte | within 197 bottoms)= {auc_within:.3f}  [Eng1 universe]")
    print(f"  AUC(is_monforte | MF vs NONE only)   = {auc_mf_vs_none:.3f}")
    OUT[feat]={"mf":desc(mf,feat),"medfraco":desc(mfr,feat),"none":desc(none,feat),"bottoms":desc(bot,feat),
               "auc_full":round(auc_full,3),"auc_within_bottoms":round(auc_within,3),
               "auc_mf_vs_none":round(auc_mf_vs_none,3)}
print("\nINTERP: if auc_full<0.5 (low legpos->MF) but auc_within_bottoms>0.5 (high legpos->MF among bottoms),")
print("the Eng2 'flip' is a NONE-universe artifact: NONE micro-lows sit high in their leg, MF bottoms low,")
print("but among REAL bottoms the Eng1 direction (high legpos=strong) can still hold. Fingerprint transfer")
print("is undermined ONLY IF the direction also flips within bottoms.")
json.dump(OUT,open(HERE/"_DA_entry2_featdir.json","w"),indent=1)
print("-> _DA_entry2_featdir.json")
