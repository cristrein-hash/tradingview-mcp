#!/usr/bin/env python3
"""ENGINE 5 — Fase 0: dossiê COMPLETO por fundo (Cris 2026-06-28). RAW-only, causal. União de TODAS as features já
usadas/mapeadas (E1 fingerprint + E2 reação + E3/E4 HTF nativo 4H/1D + flow/bubbles/NAS/RSI/vol/path/sweep) +
SEQUÊNCIA DE REAÇÃO crua (barras +1..+12 pós-mínima, em ATR) + contexto nativo 4H/1D + mecânica de entrada.
STUDY=58 MON+FORTE; CONTROL=amostra MED/FRACO + NONE. Os agentes leem isto fundo-a-fundo. -> dossier_monforte.jsonl / dossier_control.jsonl"""
import json,bisect,statistics as st
from pathlib import Path
HERE=Path(__file__).parent
PRIM={p.name.split(".")[0].replace("XAUUSD_15m_replay_",""):json.loads(p.read_text()) for p in sorted((HERE/"primitives").glob("*.primitives.json"))}
PRIMK={k[:10]:v for k,v in PRIM.items()}
BF={(r["block"],r["t"]):r for r in (json.loads(l) for l in (HERE/"bottom_features.jsonl").read_text().splitlines())}  # 58 features E1
H4=json.loads((HERE/"htf_primitives"/"htf_4H.primitives.json").read_text()); H1=json.loads((HERE/"htf_primitives"/"htf_1D.primitives.json").read_text())
def htf_prep(H):
    s=sorted(H["series"],key=lambda b:b["t"]); ts=[b["t"] for b in s]
    nas=sorted([e for e in H["nas_events"] if e.get("t")],key=lambda e:e["t"]); nast=[e["t"] for e in nas]
    smc=sorted([e for e in H["smc_events"] if e.get("t")],key=lambda e:e["t"]); smct=[e["t"] for e in smc]
    zd=[z for z in H["zones"] if "DEMAND" in str(z.get("text","")).upper() and z.get("born_t")]
    zs=[z for z in H["zones"] if "SUPPLY" in str(z.get("text","")).upper() and z.get("born_t")]
    return {"s":s,"ts":ts,"nas":nas,"nast":nast,"smc":smc,"smct":smct,"zd":zd,"zs":zs}
M4=htf_prep(H4); M1=htf_prep(H1)
def asof(M,t,tf):
    i=bisect.bisect_right(M["ts"],t-tf)-1; return M["s"][i] if i>=0 else None
def htf_ctx(M,t,tf,c,lo,atr15):
    b=asof(M,t,tf); o={}
    if not b or not b.get("atr"): return {"avail":0}
    a=b["atr"]
    dem=[z for z in M["zd"] if z["born_t"]<=t and z.get("high") is not None]
    db=[z for z in dem if z["high"]<=c+0.3*a]
    o["trend"]=1 if (b.get("ema21") and c>b["ema21"]) else (-1 if b.get("ema21") else 0)
    o["rsi"]=round(b["rsi"],1) if b.get("rsi") is not None else None
    o["dist_demand_atr"]=round(min((c-z["high"])/a for z in db),2) if db else 99
    o["in_demand"]=1 if any(z["low"]-0.3*a<=lo<=z["high"]+0.5*a for z in dem) else 0
    sup=[z for z in M["zs"] if z["born_t"]<=t and z.get("low") is not None and z["low"]>c]
    o["clean_sky_atr"]=round(min((z["low"]-c)/a for z in sup),2) if sup else 99
    sa=bisect.bisect_left(M["smct"],t-6*tf); sb=bisect.bisect_right(M["smct"],t)
    o["choch_rec"]=1 if any("CHoCH" in str(M["smc"][i].get("text","")) for i in range(sa,sb)) else 0
    na=bisect.bisect_left(M["nast"],t-8*tf); nb=bisect.bisect_right(M["nast"],t)
    o["nas_long_rec"]=sum(1 for i in range(na,nb) if M["nas"][i]["dir"]=="LONG")
    return o
def build(rec):
    block=rec["block"]; t=rec["t"]; pr=PRIMK[block]; s=pr["series"]; tmap={b["t"]:i for i,b in enumerate(s)}
    i=tmap.get(t)
    if i is None or not s[i]["atr"]: return None
    atr=s[i]["atr"]; lo=s[i]["l"]; c0=s[i]["c"]
    smc=sorted([e for e in pr["smc_events"] if e.get("t")],key=lambda e:e["t"]); smct=[e["t"] for e in smc]
    nas=sorted([e for e in pr["nas_events"] if e.get("t") and e.get("dir")],key=lambda e:e["t"]); nast=[e["t"] for e in nas]
    # SEQUÊNCIA DE REAÇÃO +1..+12 (em ATR rel à mínima)
    seq=[]
    for w in range(1,13):
        k=i+w
        if k>=len(s): break
        seq.append({"w":w,"c_atr":round((s[k]["c"]-lo)/atr,2),"h_atr":round((s[k]["h"]-lo)/atr,2),
                    "l_atr":round((s[k]["l"]-lo)/atr,2),"green":int(s[k]["c"]>s[k]["o"])})
    # mecânica de entrada: bars to reclaim ema21, 1o higher-low, sweep prior low, choch 15M após, nas long após
    e21seq=[]
    rec_ema=None
    for w in range(0,13):
        k=i+w
        if k>=len(s): break
        ee=None
        cl=[b["c"] for b in s[max(0,k-60):k+1]]
        if cl:
            kk=2/22; ee=cl[0]
            for v in cl[1:]: ee=v*kk+ee*(1-kk)
        if rec_ema is None and ee and s[k]["c"]>ee: rec_ema=w
    first_hl=next((w for w in range(1,13) if i+w<len(s) and s[i+w]["l"]>lo), None)
    # sweep: furou swing-low anterior?
    sl=next((q for q in range(i-1,3,-1) if q+2<i and s[q]["l"]==min(x["l"] for x in s[q-2:q+3])), None)
    swept=int(sl is not None and lo<s[sl]["l"])
    sa=bisect.bisect_right(smct,t); sb=bisect.bisect_right(smct,s[min(i+12,len(s)-1)]["t"])
    choch_after=int(any("CHoCH" in str(smc[x].get("text","")) for x in range(sa,sb)))
    na=bisect.bisect_right(nast,t); nb=bisect.bisect_right(nast,s[min(i+12,len(s)-1)]["t"])
    naslong_after=sum(1 for x in range(na,nb) if nas[x]["dir"]=="LONG")
    feats=BF.get((block,t),{})
    out={"block":block,"t":t,"date":rec.get("date"),"tier":rec["tier"],"yr":rec.get("yr"),
         "leg_atr":rec.get("leg_atr"),"power_score":rec.get("power_score"),
         "features_E1":{k:v for k,v in feats.items() if k not in ("block","t","yr","tier","tier_clean","leg_atr","power_score")},
         "htf4_native":htf_ctx(M4,t,14400,c0,lo,atr),"htf1_native":htf_ctx(M1,t,86400,c0,lo,atr),
         "reaction_seq":seq,
         "entry_mechanics":{"reclaim_ema_bars":rec_ema,"first_higher_low_bar":first_hl,"swept_prior_low":swept,
                            "choch_15m_after":choch_after,"nas_long_after":naslong_after,
                            "mfe12_atr":round(max((x["h_atr"] for x in seq),default=0),2),
                            "mae12_atr":round(min((x["l_atr"] for x in seq),default=0),2)}}
    return out
import csv as _csv
REV=[r for r in _csv.DictReader(open(HERE/"reversal_power.csv")) if r["kind"]=="BOT"]
for r in REV:
    r["leg_atr"]=float(r["leg_atr"]); r["yr"]=int(r["yr"]); r["t"]=int(r["t"])
    # achar block via primitives
    for bk,pr in PRIMK.items():
        if any(b["t"]==r["t"] for b in pr["series"][:1]) or True:  # set abaixo
            pass
# map t->block
T2B={}
for bk,pr in PRIMK.items():
    for b in pr["series"]: T2B.setdefault(b["t"],bk)
for r in REV: r["block"]=T2B.get(r["t"])
mf=[r for r in REV if r["tier"] in ("MONSTRO","FORTE") and r["block"]]
ctrl=[r for r in REV if r["tier"] in ("MEDIO","FRACO") and r["block"]]
def dump(rows,path):
    n=0
    with open(HERE/path,"w") as f:
        for r in rows:
            d=build(r)
            if d: f.write(json.dumps(d,default=str)+"\n"); n+=1
    return n
n_mf=dump(mf,"dossier_monforte.jsonl"); n_ctrl=dump(ctrl,"dossier_control.jsonl")
print(f"dossier_monforte.jsonl: {n_mf} fundos MON+FORTE | dossier_control.jsonl: {n_ctrl} MED/FRACO")
ex=json.loads((HERE/"dossier_monforte.jsonl").read_text().splitlines()[0])
print("campos por fundo:",list(ex.keys()))
print("E1 features:",len(ex["features_E1"]),"| reaction_seq len:",len(ex["reaction_seq"]),"| entry_mechanics:",list(ex["entry_mechanics"].keys()))
