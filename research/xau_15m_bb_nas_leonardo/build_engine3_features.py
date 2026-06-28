#!/usr/bin/env python3
"""ENGINE 3 — Fase 1: enriquece o stream de candidatos (entry_candidates) com CONFLUÊNCIA NATIVA 4H+1D (Cris 2026-06-28).
Features novas cruzadas: HTF OB-demand (4H/1D) contendo o fundo, HTF RSI, HTF trend, regime-onset (CHoCH up 4H recente),
NAS LONG 4H, clean-sky 4H, + DETECTOR DE FACA multi-TF. Causal: HTF só barras fechadas (t+tf<=cj_t), zonas born<=cj_t.
-> entry_candidates_htf.jsonl"""
import json,bisect,statistics as st
from pathlib import Path
HERE=Path(__file__).parent
CAND=[json.loads(l) for l in (HERE/"entry_candidates.jsonl").read_text().splitlines()]
PRIM={p.name.split(".")[0].replace("XAUUSD_15m_replay_",""):json.loads(p.read_text()) for p in sorted((HERE/"primitives").glob("*.primitives.json"))}
PRIMK={k[:10]:v for k,v in PRIM.items()}
H4=json.loads((HERE/"htf_primitives"/"htf_4H.primitives.json").read_text())
H1=json.loads((HERE/"htf_primitives"/"htf_1D.primitives.json").read_text())
def mk(htf,tf_s):
    s=sorted(htf["series"],key=lambda b:b["t"]); ts=[b["t"] for b in s]
    nas=sorted([e for e in htf["nas_events"] if e.get("t")],key=lambda e:e["t"]); nast=[e["t"] for e in nas]
    smc=sorted([e for e in htf["smc_events"] if e.get("t")],key=lambda e:e["t"]); smct=[e["t"] for e in smc]
    z=htf["zones"]
    return {"s":s,"ts":ts,"tf":tf_s,"nas":nas,"nast":nast,"smc":smc,"smct":smct,"zd":[x for x in z if "DEMAND" in str(x.get("text","")).upper()],"zs":[x for x in z if "SUPPLY" in str(x.get("text","")).upper()]}
M4=mk(H4,14400); M1=mk(H1,86400)
def asof_bar(M,t):
    # último bar HTF FECHADO (t_bar+tf<=t)
    i=bisect.bisect_right(M["ts"],t-M["tf"])-1
    return M["s"][i] if i>=0 else None
def htf_feats(M,pfx,lo,c,t):
    b=asof_bar(M,t)
    f={}
    if not b or not b.get("atr"):
        for k in ("in_demand","dist_demand_atr","rsi","trend","choch_up_rec","nas_long_rec","clean_sky_atr"): f[f"{pfx}_{k}"]=None
        return f
    atr=b["atr"]
    dem=[zz for zz in M["zd"] if zz.get("born_t") is not None and zz["born_t"]<=t and zz.get("high") is not None]
    demin=[zz for zz in dem if zz["low"]-0.3*atr<=lo<=zz["high"]+0.5*atr]
    dembelow=[zz for zz in dem if zz["high"]<=c+0.3*atr]
    f[f"{pfx}_in_demand"]=1 if demin else 0
    f[f"{pfx}_dist_demand_atr"]=round(min((c-zz["high"])/atr for zz in dembelow),2) if dembelow else 99
    f[f"{pfx}_rsi"]=round(b["rsi"],1) if b.get("rsi") is not None else None
    f[f"{pfx}_trend"]=1 if (b.get("ema21") and c>b["ema21"]) else (-1 if b.get("ema21") else 0)
    # regime-onset: CHoCH (proxy) nos últimos ~6 HTF bars
    a=bisect.bisect_left(M["smct"],t-6*M["tf"]); bnd=bisect.bisect_right(M["smct"],t)
    f[f"{pfx}_choch_up_rec"]=1 if any("CHoCH" in str(M["smc"][i].get("text","")) for i in range(a,bnd)) else 0
    an=bisect.bisect_left(M["nast"],t-8*M["tf"]); bn=bisect.bisect_right(M["nast"],t)
    f[f"{pfx}_nas_long_rec"]=sum(1 for i in range(an,bn) if M["nas"][i]["dir"]=="LONG")
    supa=[zz for zz in M["zs"] if zz.get("born_t") is not None and zz["born_t"]<=t and zz.get("low") is not None and zz["low"]>c]
    f[f"{pfx}_clean_sky_atr"]=round(min((zz["low"]-c)/atr for zz in supa),2) if supa else 99
    return f
rows=[]
for r in CAND:
    pr=PRIMK.get(r["block"])
    if not pr: continue
    s=pr["series"]; tmap={b["t"]:i for i,b in enumerate(s)}
    p=tmap.get(r["t"]); cj=tmap.get(r["cj_t"])
    if p is None or cj is None: continue
    lo=s[p]["l"]; c=s[cj]["c"]; t=r["cj_t"]
    f=dict(r)
    f.update(htf_feats(M4,"h4n",lo,c,t)); f.update(htf_feats(M1,"h1n",lo,c,t))
    # confluência HTF demanda + detector de FACA multi-TF
    f["htf_demand_confluence"]=1 if (f.get("h4n_in_demand")==1 and f.get("h1n_in_demand")==1) else 0
    f["htf_demand_any"]=1 if (f.get("h4n_in_demand")==1 or f.get("h1n_in_demand")==1) else 0
    knife = (r.get("rsi_min8",50)<32 and r.get("atr_regime",1)>1.05 and r.get("downleg_decel",0)==0
             and f.get("htf_demand_any",0)==0 and (f.get("h4n_trend") in (-1,None)))
    f["falling_knife"]=1 if knife else 0
    rows.append(f)
with open(HERE/"entry_candidates_htf.jsonl","w") as fo:
    for r in rows: fo.write(json.dumps(r,default=str)+"\n")
MF=sum(r["is_monforte"] for r in rows)
def rate(cond):
    g=[r for r in rows if cond(r)]; return f"{len(g)} (MF {sum(x['is_monforte'] for x in g)}, MEDFRACO {sum(x['is_medfraco'] for x in g)})"
print(f"entry_candidates_htf.jsonl: {len(rows)} | MON+FORTE={MF}")
print(f"  4H in_demand: {rate(lambda r:r.get('h4n_in_demand')==1)}")
print(f"  1D in_demand: {rate(lambda r:r.get('h1n_in_demand')==1)}")
print(f"  HTF demand confluence (4H&1D): {rate(lambda r:r['htf_demand_confluence']==1)}")
print(f"  falling_knife: {rate(lambda r:r['falling_knife']==1)}")
print(f"  NOT knife: {rate(lambda r:r['falling_knife']==0)}")
print(f"  novas HTF feats: {[k for k in rows[0] if k.startswith(('h4n_','h1n_','htf_','falling'))]}")
