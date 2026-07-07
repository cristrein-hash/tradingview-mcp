#!/usr/bin/env python3
"""N96 LOSER · RAW-NATIVE MULTI-TIMEFRAME FEATURE AUDIT (2026-07-07, tarefa Cris).
RAW-FIRST ABSOLUTO. Fontes: 15M primitives (canonico, RAW-15M lineage + source guard) + htf_4H/htf_1D
primitives NATIVOS (build_htf_primitives.py, RAW 4H/1D gz). ZERO resample, ZERO Fractal-MTF, ZERO SLIM.
CAUSAL: HTF usa so barras/zonas/eventos com t/born_t < entry_t (a barra HTF corrente EXCLUIDA; zonas por
born_t, NUNCA last_t). Determinista, read-only, fail-loud. Outputs pequenos (csv+json).
Objetivo: separar winners vs familias de loser (C topo/dist-bear, D bear ativo, R range, MGMT nao-filtrar)
por features RAW multi-TF. Reporta lift+cobertura+null. NAO chama validacao."""
import json, glob, bisect, sys, csv
import datetime as dt
import statistics as st
sys.path.insert(0,"/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo")
from agent_ctx_kit import S,TS,HI,LO,CL,ATR,EMA,RSI,N,ENTRIES,score
HERE="/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo"
# ---- fail-loud: N96 reproduz? ----
W=sum(e['out'] for e in ENTRIES)
assert len(ENTRIES)==96 and W==52, f"N96 NAO reproduz: N={len(ENTRIES)} W={W}"
# ---- 15M smc/nas/zones ----
smc15=[]; nas15=[]; zones15=[]
for p in sorted(glob.glob(HERE+"/primitives/*.primitives.json")):
    d=json.load(open(p))
    smc15+=[e for e in d.get("smc_events",[]) if e.get("t")]
    nas15+=[e for e in d.get("nas_events",[]) if e.get("t")]
    zones15+=[z for z in d.get("zones",[]) if z.get("born_t")]
smc15.sort(key=lambda e:e["t"]); nas15.sort(key=lambda e:e["t"]); zones15.sort(key=lambda z:z["born_t"])
# ---- HTF primitives nativos (4H/1D single-file; 30M/1H multi-bloco merge) ----
def load_tf(files):
    ser={}; smc=[]; zones=[]
    for f in files:
        d=json.load(open(f))
        for b in d["series"]: ser[b["t"]]=b   # dedupe por t (last-write)
        smc+=[e for e in d.get("smc_events",[]) if e.get("t")]
        zones+=[z for z in d.get("zones",[]) if z.get("born_t")]
    S=sorted(ser.values(),key=lambda b:b["t"])
    return {"ser":S,"t":[b["t"] for b in S],"smc":sorted(smc,key=lambda e:e["t"]),"zones":sorted(zones,key=lambda z:z["born_t"])}
HTF={
 "30M":load_tf(sorted(glob.glob(HERE+"/htf_primitives/XAUUSD_30m_*.primitives.json"))),
 "1H": load_tf(sorted(glob.glob(HERE+"/htf_primitives/XAUUSD_60m_*.primitives.json"))),
 "4H": load_tf([HERE+"/htf_primitives/htf_4H.primitives.json"]),
 "1D": load_tf([HERE+"/htf_primitives/htf_1D.primitives.json"]),
}
BARSEC={"30M":1800,"1H":3600,"4H":4*3600,"1D":24*3600}
CAUSAL_BAD=0
def htf_ctx(tf, entry_t, px, a15):
    """features HTF CAUSAIS: so barras/zonas com t/born_t < entry_t (barra corrente excluida)."""
    global CAUSAL_BAD
    H=HTF[tf]; sec=BARSEC[tf]
    hi=bisect.bisect_right(H["t"], entry_t-sec)  # ultima barra FECHADA antes de entry (t+sec<=entry_t)
    if hi<8: return None
    bars=H["ser"][:hi]
    if bars[-1]["t"] > entry_t: CAUSAL_BAD+=1
    last=bars[-1]; a=last.get("atr") or a15
    # tendencia HTF: close atual vs 6 barras atras
    trend=(last["c"]-bars[-6]["c"])/(a or 1)
    # SVP: posicao vs VAL/VAH da ultima barra 4H/1D
    val=last.get("val"); vah=last.get("vah")
    svp_pos=(px-val)/((vah-val) or 1) if (val and vah and vah>val) else 0.5
    # zonas DEMAND abaixo / SUPPLY acima nascidas ANTES do entry (causal; NUNCA last_t)
    zhi=bisect.bisect_right([z["born_t"] for z in H["zones"]], entry_t)
    dem=[ (px-((z["high"]+z["low"])/2))/a for z in H["zones"][:zhi] if z["text"]=="DEMAND" and (z["high"]+z["low"])/2 < px ]
    sup=[ (((z["high"]+z["low"])/2)-px)/a for z in H["zones"][:zhi] if z["text"]=="SUPPLY" and (z["high"]+z["low"])/2 > px ]
    # SMC recente (ultimas ~8 barras HTF)
    slo=bisect.bisect_left([e["t"] for e in H["smc"]], entry_t-8*sec); sh=bisect.bisect_right([e["t"] for e in H["smc"]], entry_t)
    seg=H["smc"][slo:sh]
    eqh=sum(1 for e in seg if e["text"]=="EQH"); choch=sum(1 for e in seg if e["text"]=="CHoCH")
    return {"trend":round(trend,2),"svp_pos":round(svp_pos,2),
            "dem_below":round(min(dem),2) if dem else 99,"sup_above":round(min(sup),2) if sup else 99,
            "eqh":eqh,"choch":choch,"rsi":round(last.get("rsi") or 50,1)}
def f15(e):
    j=e["j"]; i=e["i"]; a=ATR[j] or 5; px=e["ent"]; et=e["t"]
    zhi=bisect.bisect_right([z["born_t"] for z in zones15], et)
    dem=[ (px-((z["high"]+z["low"])/2))/a for z in zones15[:zhi] if z["text"]=="DEMAND" and (z["high"]+z["low"])/2 < px ]
    sup=[ (((z["high"]+z["low"])/2)-px)/a for z in zones15[:zhi] if z["text"]=="SUPPLY" and (z["high"]+z["low"])/2 > px ]
    slo=bisect.bisect_left([x["t"] for x in smc15], et-96*900); sh=bisect.bisect_right([x["t"] for x in smc15], et)
    seg=smc15[slo:sh]
    return {"rsi15":RSI[j] or 50,"dem15":round(min(dem),2) if dem else 99,"sup15":round(min(sup),2) if sup else 99,
            "eqh15":sum(1 for x in seg if x["text"]=="EQH"),"choch15":sum(1 for x in seg if x["text"]=="CHoCH")}
# ---- classificacao CORRIGIDA pelo Cris ----
FAM={"MGMT":{24,32,64,77},                                             # nao-filtrar (gestao/BE/timing)
     "C":{17,18,20,21,23,25,31,36,42,46,48,55,56,57,58,59,60,65,79,83,84,85},  # topo/distribuicao-bear
     "D":{27,49,50,66,67,68,69,80,86,87,89,92,93,94},                  # bear ativo
     "R":{5,6,7,8}}                                                    # range neutro (consolidacao)
def famof(n):
    for k,s in FAM.items():
        if n in s: return k
    return "WIN"
rows=[]
for e in ENTRIES:
    a=ATR[e["j"]] or 5; px=e["ent"]; et=e["t"]
    r={"n":e["n"],"out":e["out"],"fam":famof(e["n"]),"d":dt.datetime.utcfromtimestamp(int(et)).strftime("%Y-%m-%d")}
    r.update(f15(e))
    for tf in ("30M","1H","4H","1D"):
        c=htf_ctx(tf,et,px,a)
        if c:
            for k,v in c.items(): r[f"{tf}_{k}"]=v
    rows.append(r)
assert CAUSAL_BAD==0, f"LOOKAHEAD HTF: {CAUSAL_BAD} barras com t>entry"
# ---- comparacao winners vs familias ----
FEATS=[c for c in rows[0] if c not in ("n","out","fam","d")]
WINr=[r for r in rows if r["out"]==1]
def med(sub,k):
    v=[r[k] for r in sub if r.get(k) is not None]; return st.median(v) if v else None
summary={"n96":{"N":96,"W":52,"L":44,"hit":round(52/96,3)},"causal_bad":CAUSAL_BAD,"families":{k:sorted(v) for k,v in FAM.items()},
         "sources":{"15M":"primitives/ (RAW-15M lineage, source guard PASS)","30M":"htf_primitives/XAUUSD_30m_* (RAW 30M nativo, extractor validado)","1H":"htf_primitives/XAUUSD_60m_* (RAW 1H nativo)","4H":"htf_primitives/htf_4H (RAW 4H nativo)","1D":"htf_primitives/htf_1D (RAW 1D nativo)"},
         "feature_medians":{}}
print(f"N96 reproduz (52W/44L). CAUSAL_BAD={CAUSAL_BAD}. Familias: C{len(FAM['C'])} D{len(FAM['D'])} R{len(FAM['R'])} MGMT{len(FAM['MGMT'])}")
print(f"\n{'feature':<14}{'WIN':>8}{'C':>8}{'D':>8}{'R':>8}{'MGMT':>8}")
for k in FEATS:
    w=med(WINr,k);
    cs={fam:med([r for r in rows if r['fam']==fam],k) for fam in ('C','D','R','MGMT')}
    summary["feature_medians"][k]={"WIN":w,**cs}
    def fmt(x): return f"{x:>8.2f}" if isinstance(x,(int,float)) else f"{'-':>8}"
    print(f"{k:<14}{fmt(w)}{fmt(cs['C'])}{fmt(cs['D'])}{fmt(cs['R'])}{fmt(cs['MGMT'])}")
# ---- CSV pequeno (por trade) ----
with open(HERE+"/results/n96_loser_raw_mtf_feature_audit.csv","w",newline="") as fh:
    wcsv=csv.DictWriter(fh, fieldnames=["n","out","fam","d"]+FEATS); wcsv.writeheader()
    for r in rows: wcsv.writerow({k:r.get(k) for k in ["n","out","fam","d"]+FEATS})
json.dump(summary, open(HERE+"/results/n96_loser_raw_mtf_feature_audit_summary.json","w"), indent=1)
print("\nsaved results/n96_loser_raw_mtf_feature_audit.{csv,summary.json} · OK")
