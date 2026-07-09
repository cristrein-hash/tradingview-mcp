#!/usr/bin/env python3
"""LIB partilhada — SL/EXIT review da XAU 15M N83 (Markup-Demand + Intra-BEAR Capitulation).
Reproduz FIELMENTE o pipeline do entry_engine_master_20260707.py (loader primitives -> legwalk r=6 ->
entry reclaim EMA21 win=24 -> SL=demand_low-0.1*ATR[i] (V1) -> tgt=+3R -> outcome first-touch SL-first,
horizon=1440) e adiciona simulação PARAMÉTRICA de SL/exit alternativos sobre os MESMOS bars RAW.
Fail-loud: reproduce_base() asserta byte-match (ent/sl/tgt/out) vs o master JSON salvo.
RAW/source-first: primitives nativos (sem SLIM/proxy). Sem produção/Telegram/chart."""
import json, glob, bisect
import datetime as dt
from pathlib import Path
HERE=Path(__file__).resolve().parent; RD=HERE.parent
MASTER_JSON=RD/"results/entry_engine_master_20260707.json"
REGIME_JSON=RD/"results/n96_causal_regime.json"
CUT_JSON=RD/"results/n96_intra_bear_cut_list.json"
FAMILY_CSV=RD/"results/n96_loser_family_map_corrected.csv"

# ---- loader (idêntico ao engine, linhas 15-25) ----
series={}
for p in sorted(glob.glob(str(RD/"primitives"/"*.primitives.json"))):
    d=json.load(open(p))
    for b in d["series"]: series.setdefault(b["t"],b)
S=sorted(series.values(),key=lambda b:b["t"]); TS=[b["t"] for b in S]; N=len(S)
HI=[b["h"] for b in S]; LO=[b["l"] for b in S]; CL=[b["c"] for b in S]
ATR=[b.get("atr") or 5.0 for b in S]; EMA=[b.get("ema21") for b in S]

# ---- legwalk r=6 (idêntico) ----
def zz(r):
    piv=[]; d=0; ehi=elo=0
    for i in range(1,N):
        a=ATR[i]
        if HI[i]>HI[ehi]: ehi=i
        if LO[i]<LO[elo]: elo=i
        if d<=0 and HI[i]-LO[elo]>=r*a and elo<i: piv.append(("L",elo,LO[elo],i)); d=1; ehi=max(range(elo,i+1),key=lambda k:HI[k])
        elif d>=0 and HI[ehi]-LO[i]>=r*a and ehi<i: piv.append(("H",ehi,HI[ehi],i)); d=-1; elo=min(range(ehi,i+1),key=lambda k:LO[k])
    return piv
def legwalk(r=6):
    piv=zz(r); ev=[]; prevH=prevL=None; lastH=None
    for tp,i,pr,ci in piv:
        if tp=="H": prevH=pr; lastH=pr
        else:
            if prevH is not None and lastH is not None:
                kind="MARKUP" if (prevL is None or pr>prevL) else "CORRECAO"
                ev.append({"i":i,"lo":pr,"conf_i":ci,"kind":kind})
            prevL=pr
    return ev

# ---- entry causal (idêntico: win=24, SL V1, 3R, first-touch SL-first, horizon 1440) ----
HORIZON=1440
def build_entry(e, win=24, horizon=HORIZON):
    i=e["i"]; lo=e["lo"]; a=ATR[i] or 5
    j=None
    for k in range(i+1,min(N,i+win+1)):
        if EMA[k] is not None and CL[k]>EMA[k] and CL[k]>CL[k-1]: j=k; break
    if j is None: return None
    ent=CL[j]; sl=lo-0.1*a; risk=ent-sl
    if risk<=0.05*a: return None
    tgt=ent+3*risk
    out=0; end=None
    for m in range(j+1, min(N,j+horizon+1)):
        if LO[m]<=sl: out=0; end=m; break
        if HI[m]>=tgt: out=1; end=m; break
    return {"i":i,"lo":lo,"j":j,"t":TS[j],"ent":ent,"sl":sl,"tgt":tgt,"risk":risk,
            "reclaim_lag":j-i,"out":out,"end":end}

def reproduce_base():
    """Reconstrói os 96 MARKUP na janela e ASSERTA byte-match vs master JSON. Retorna lista com
    trade_id 1..96 + campos internos (i,lo,j,end) p/ simulação."""
    W0=dt.datetime(2025,8,1).timestamp(); W1=dt.datetime(2026,7,4).timestamp()
    saved=[r for r in json.load(open(MASTER_JSON)) if r.get("kind")=="MARKUP"]
    ev=[e for e in legwalk(6) if W0<=TS[e["i"]]<=W1]
    built=[]
    for e in ev:
        en=build_entry(e)
        if en is None: continue
        en["kind"]=e["kind"]
        if e["kind"]=="MARKUP": built.append(en)
    assert len(built)==len(saved)==96, f"reproducao N: built={len(built)} saved={len(saved)}"
    for k,(b,s) in enumerate(zip(built,saved),1):
        assert b["t"]==s["t"], f"#{k} t mismatch"
        assert round(b["ent"],2)==s["ent"] and round(b["sl"],2)==s["sl"] and round(b["tgt"],2)==s["tgt"], f"#{k} px mismatch"
        assert b["out"]==s["out"], f"#{k} out mismatch"
        b["trade_id"]=k
    return built

def load_context():
    """regime causal (96/96), cut list (13), families (loser-only)."""
    reg=json.load(open(REGIME_JSON))
    regmap={int(k):(v.get("regime") if isinstance(v,dict) else v) for k,v in reg.items()}
    cut=set(json.load(open(CUT_JSON))["cut_13"])
    fam={}
    import csv
    with open(FAMILY_CSV) as f:
        for r in csv.DictReader(f):
            try: fam[int(str(r.get("trade") or r.get("#") or "").lstrip("#"))]=r.get("familia") or r.get("family")
            except Exception: pass
    return regmap,cut,fam

# ---- simulação paramétrica (mesma semântica: first-touch, SL-first no mesmo bar) ----
def simulate(j, ent, sl, tgt, horizon=HORIZON, time_cap=None):
    """Retorna dict: outcome('SL'|'TGT'|'TIME'), end bar, bars_held, R_real (executável:
    SL=-1R-equivalente pelo preço, TGT=+R do alvo, TIME=close no cutoff)."""
    risk=ent-sl
    lastm=min(N-1, j+(time_cap if time_cap else horizon))
    for m in range(j+1, lastm+1):
        if sl is not None and LO[m]<=sl:
            return {"oc":"SL","end":m,"bars":m-j,"R":(sl-ent)/risk if risk>0 else None}
        if tgt is not None and HI[m]>=tgt:
            return {"oc":"TGT","end":m,"bars":m-j,"R":(tgt-ent)/risk if risk>0 else None}
    return {"oc":"TIME","end":lastm,"bars":lastm-j,"R":(CL[lastm]-ent)/risk if risk>0 else None}

# ---- SL alternativos (todos causais no bar de entry j; risco = ent - sl_alt) ----
def sl_current(tr):    # A: demand_low - 0.1*ATR[i] (V1)
    return tr["sl"]
def sl_swing(tr, K=12):  # C: menor low das K barras ATÉ o entry j (inclui j)
    j=tr["j"]; return min(LO[max(0,j-K+1):j+1])-0.1*(ATR[tr["i"]] or 5)
def sl_atr(tr, k=1.5):   # D: ent - k*ATR[j]
    return tr["ent"]-k*(ATR[tr["j"]] or 5)
def sl_hybrid(tr):       # E: min(demand_low, swing12) - 0.1*ATR
    j=tr["j"]; base=min(tr["lo"], min(LO[max(0,j-11):j+1])); return base-0.1*(ATR[tr["i"]] or 5)
def sl_wider(tr):        # F: demand_low - 0.5*ATR (conservador)
    return tr["lo"]-0.5*(ATR[tr["i"]] or 5)

# ---- métricas ----
def dstr(t): return dt.datetime.utcfromtimestamp(int(t)).strftime("%Y-%m-%d")
def panel(Rs):
    n=len(Rs);
    if n==0: return {"n":0}
    w=sum(1 for r in Rs if r>0); s=sum(Rs)
    g=sum(r for r in Rs if r>0); l=-sum(r for r in Rs if r<0)
    eq=0.0;pk=0.0;dd=0.0;stk=0;mst=0
    for r in Rs:
        eq+=r;pk=max(pk,eq);dd=min(dd,eq-pk);stk=stk+1 if r<=0 else 0;mst=max(mst,stk)
    med=sorted(Rs)[n//2]
    return {"n":n,"W":w,"L":n-w,"WR":round(100*w/n,1),"sumR":round(s,1),
            "PF":round(g/l,2) if l>0 else None,"avgR":round(s/n,2),"medianR":round(med,2),
            "maxDD_R":round(dd,1),"streak":mst}
