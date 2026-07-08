#!/usr/bin/env python3
"""N96 · OB-CONFLUENCE (multi-TF, mesma regiao de entry) + BUBBLE CLUSTERS (2026-07-08, Cris cobrou:
so tinha feito RSI). RAW-native. Cruza zonas Custom OB DEMAND/SUPPLY dos 5 TFs (15M+30M+1H+4H+1D) NA MESMA
REGIAO DE PRECO do entry (confluencia), e analisa clusters de bubbles (Market Order Bubbles 15M) por regiao:
absorcao de venda no fundo (winner) vs climax/exaustao de compra no topo (loser). CAUSAL: zonas born_t<et;
bubbles known_at<=et. Compara winners vs familias C/D/R/MGMT (classificacao corrigida do Cris)."""
import json, glob, bisect, sys, csv
import statistics as st
sys.path.insert(0,"/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo")
from agent_ctx_kit import S,TS,HI,LO,CL,ATR,N,ENTRIES,score
HERE="/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo"
assert len(ENTRIES)==96 and sum(e['out'] for e in ENTRIES)==52, "N96 nao reproduz"
# ---- zonas OB de TODOS os TFs (RAW-native) ----
def load_zones(files):
    z=[]
    for f in files:
        d=json.load(open(f)); z+=[x for x in d.get("zones",[]) if x.get("born_t")]
    return sorted(z,key=lambda x:x["born_t"])
ZTF={
 "15M":load_zones(sorted(glob.glob(HERE+"/primitives/*.primitives.json"))),
 "30M":load_zones(sorted(glob.glob(HERE+"/htf_primitives/XAUUSD_30m_*.primitives.json"))),
 "1H": load_zones(sorted(glob.glob(HERE+"/htf_primitives/XAUUSD_60m_*.primitives.json"))),
 "4H": load_zones([HERE+"/htf_primitives/htf_4H.primitives.json"]),
 "1D": load_zones([HERE+"/htf_primitives/htf_1D.primitives.json"]),
}
ZBORN={tf:[z["born_t"] for z in ZTF[tf]] for tf in ZTF}
# ---- bubbles 15M ----
BUB=sorted([json.loads(l) for f in glob.glob(HERE+"/bubbles/*.jsonl") for l in open(f)], key=lambda x:(x.get("known_at") or x["t"]))
BUBK=[(x.get("known_at") or x["t"]) for x in BUB]
def ob_confluence(et, px, a, K=1.2):
    """quantos TFs tem DEMAND abaixo (<=K ATR) / SUPPLY acima (<=K ATR) na regiao do entry (causal born_t<et)."""
    dem_tf=0; sup_tf=0; dem_min=99; sup_min=99
    for tf in ZTF:
        hi=bisect.bisect_right(ZBORN[tf], et)
        dd=99; su=99
        for z in ZTF[tf][:hi]:
            mid=(z["high"]+z["low"])/2
            if z["text"].startswith("DEMAND") and z["low"]<=px and (px-mid)/a<=K: dd=min(dd,(px-mid)/a)
            if z["text"].startswith("SUPPLY") and z["high"]>=px and (mid-px)/a<=K: su=min(su,(mid-px)/a)
        if dd<99: dem_tf+=1; dem_min=min(dem_min,dd)
        if su<99: sup_tf+=1; sup_min=min(sup_min,su)
    return {"dem_conf":dem_tf,"sup_conf":sup_tf,"dem_min_mtf":round(dem_min,2),"sup_min_mtf":round(sup_min,2),"net_conf":dem_tf-sup_tf}
def bubbles_region(e, a):
    """clusters de bubbles 15M na regiao/janela do entry (causal known_at<=et)."""
    et=e["t"]; i=e["i"]; lo=LO[i]; px=e["ent"]
    hi=bisect.bisect_right(BUBK, et)
    W={"S":1,"M":2,"L":3}
    seg=[BUB[k] for k in range(hi) if et-32*900 <= BUB[k]["t"] <= et]  # ultimas ~32 barras
    if not seg: return {"buy_ml":0,"sell_ml":0,"sell_at_low":0,"buy_at_high":0,"bub_net":0,"sell_absorbed":0}
    buy_ml=sum(W[b["size"]] for b in seg if b["side"]=="BUY" and b["size"] in ("M","L"))
    sell_ml=sum(W[b["size"]] for b in seg if b["side"]=="SELL" and b["size"] in ("M","L"))
    # SELL bubbles perto do FUNDO (absorcao: vendas no fundo mas preco reclamou)
    sell_at_low=sum(1 for b in seg if b["side"]=="SELL" and b["size"] in ("M","L") and abs(b["l"]-lo)<=0.6*a)
    # BUY bubbles perto do TOPO recente (climax de compra)
    rhi=max(HI[max(0,i-32):i+1])
    buy_at_high=sum(1 for b in seg if b["side"]=="BUY" and b["size"] in ("M","L") and abs(b["h"]-rhi)<=0.6*a)
    sell_absorbed=1 if (sell_at_low>=1 and px>lo+0.3*a) else 0  # vendeu no fundo, preco subiu = absorvido
    return {"buy_ml":buy_ml,"sell_ml":sell_ml,"sell_at_low":sell_at_low,"buy_at_high":buy_at_high,
            "bub_net":buy_ml-sell_ml,"sell_absorbed":sell_absorbed}
FAM={"MGMT":{24,32,64,77},"C":{17,18,20,21,23,25,31,36,42,46,48,55,56,57,58,59,60,65,79,83,84,85},
     "D":{27,49,50,66,67,68,69,80,86,87,89,92,93,94},"R":{5,6,7,8}}
def famof(n):
    for k,s in FAM.items():
        if n in s: return k
    return "WIN"
rows=[]
for e in ENTRIES:
    a=ATR[e["j"]] or 5; px=e["ent"]; et=e["t"]
    r={"n":e["n"],"out":e["out"],"fam":famof(e["n"])}
    r.update(ob_confluence(et,px,a)); r.update(bubbles_region(e,a))
    rows.append(r)
FEATS=[c for c in rows[0] if c not in ("n","out","fam")]
WINr=[r for r in rows if r["out"]==1]
def med(sub,k):
    v=[r[k] for r in sub]; return st.median(v) if v else None
print(f"N96 · OB-confluence + bubbles (5 TFs, mesma regiao). Familias C{len(FAM['C'])} D{len(FAM['D'])} R{len(FAM['R'])} MGMT{len(FAM['MGMT'])}")
print(f"\n{'feature':<15}{'WIN':>8}{'C':>8}{'D':>8}{'R':>8}{'MGMT':>8}")
for k in FEATS:
    cs={fam:med([r for r in rows if r['fam']==fam],k) for fam in ('C','D','R','MGMT')}
    def f(x): return f"{x:>8.2f}" if isinstance(x,(int,float)) else f"{'-':>8}"
    print(f"{k:<15}{f(med(WINr,k))}{f(cs['C'])}{f(cs['D'])}{f(cs['R'])}{f(cs['MGMT'])}")
with open(HERE+"/results/n96_ob_confluence_bubble_audit.csv","w",newline="") as fh:
    w=csv.DictWriter(fh,fieldnames=["n","out","fam"]+FEATS); w.writeheader()
    for r in rows: w.writerow(r)
json.dump({"feature_medians":{k:{"WIN":med(WINr,k),**{fam:med([r for r in rows if r['fam']==fam],k) for fam in ('C','D','R','MGMT')}} for k in FEATS}},
          open(HERE+"/results/n96_ob_confluence_bubble_audit_summary.json","w"),indent=1)
print("\nsaved results/n96_ob_confluence_bubble_audit.{csv,summary.json} · OK")
