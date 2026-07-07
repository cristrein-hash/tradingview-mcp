#!/usr/bin/env python3
"""KIT PARTILHADO para o workflow multi-agente de FILTRO MACRO-CONTEXTUAL (2026-07-07).
Fornece ground-truth consistente + scoring anti-poison + helpers CAUSAIS. Os agentes IMPORTAM daqui.
Regra dura: features de contexto usam SÓ barras <= j (barra de decisão do entry). Proibido usar
confirmação de pivô por movimento futuro, zone.last_t futuro, ou qualquer janela que ultrapasse j.

USO pelos agentes:
  import sys; sys.path.insert(0,"/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo")
  from agent_ctx_kit import S,TS,HI,LO,CL,ATR,EMA,RSI,N,ENTRIES,score,causal_swings_upto
  # ENTRIES: lista de dicts {n,i,j,t,ent,sl,tgt,out,reclaim_lag}  (i=low da demanda, j=barra de entry)
  # cada feature = função do j (e barras <=j). Devolver keep_ns = set de n a MANTER.
  print(score(keep_ns))   # metricas anti-poison + by-year
"""
import json, glob, bisect
import datetime as dt
from pathlib import Path
HERE=Path(__file__).resolve().parent
_series={}
for _p in sorted(glob.glob(str(HERE/"primitives"/"*.primitives.json"))):
    for _b in json.load(open(_p))["series"]: _series.setdefault(_b["t"],_b)
S=sorted(_series.values(),key=lambda b:b["t"]); TS=[b["t"] for b in S]; N=len(S)
HI=[b["h"] for b in S]; LO=[b["l"] for b in S]; CL=[b["c"] for b in S]
ATR=[b.get("atr") or 5.0 for b in S]; EMA=[b.get("ema21") for b in S]; RSI=[b.get("rsi") for b in S]
def _zz(r):
    piv=[]; d=0; ehi=elo=0
    for i in range(1,N):
        a=ATR[i]
        if HI[i]>HI[ehi]: ehi=i
        if LO[i]<LO[elo]: elo=i
        if d<=0 and HI[i]-LO[elo]>=r*a and elo<i: piv.append(("L",elo,LO[elo],i)); d=1; ehi=max(range(elo,i+1),key=lambda k:HI[k])
        elif d>=0 and HI[ehi]-LO[i]>=r*a and ehi<i: piv.append(("H",ehi,HI[ehi],i)); d=-1; elo=min(range(ehi,i+1),key=lambda k:LO[k])
    return piv
# --- os 96 entries (mesma caminhada r=6 + reclaim EMA21) — o UNIVERSO dado (validado pelo Cris) ---
def _build_entries():
    piv=_zz(6); EV=[]; prevH=prevL=None; lastH=None
    for tp,i,pr,ci in piv:
        if tp=="H": prevH=pr; lastH=pr
        else:
            if prevH is not None and lastH is not None and (prevL is None or pr>prevL): EV.append({"i":i,"lo":pr,"leg_top":lastH})
            prevL=pr
    W0=dt.datetime(2025,8,1).timestamp(); W1=dt.datetime(2026,7,4).timestamp()
    out=[]; n=0
    for e in EV:
        i=e["i"]
        if not (W0<=TS[i]<=W1): continue
        lo=e["lo"]; a=ATR[i] or 5; j=None
        for k in range(i+1,min(N,i+25)):
            if EMA[k] is not None and CL[k]>EMA[k] and CL[k]>CL[k-1]: j=k; break
        if j is None: continue
        ent=CL[j]; sl=lo-0.1*a; risk=ent-sl
        if risk<=0.05*a: continue
        tgt=ent+3*risk; res=0
        for m in range(j+1,min(N,j+1440)):
            if LO[m]<=sl: res=0; break
            if HI[m]>=tgt: res=1; break
        n+=1
        out.append({"n":n,"i":i,"j":j,"t":TS[j],"ent":round(ent,2),"sl":round(sl,2),"tgt":round(tgt,2),
                    "out":res,"reclaim_lag":j-i,"leg_top":e["leg_top"],"demand_low":lo})
    return out
ENTRIES=_build_entries()
def _yr(t): return dt.datetime.utcfromtimestamp(int(t)).strftime("%Y")
def score(keep_ns):
    """keep_ns: iterable de n a MANTER. Devolve metricas ANTI-POISON + by-year vs base."""
    keep=set(keep_ns); sel=[e for e in ENTRIES if e["n"] in keep]; cut=[e for e in ENTRIES if e["n"] not in keep]
    baseW=sum(e["out"] for e in ENTRIES); baseL=len(ENTRIES)-baseW
    w=sum(e["out"] for e in sel); l=len(sel)-w
    wc=sum(e["out"] for e in cut); lc=len(cut)-wc  # winners cortados / losers cortados
    def yr(sub,y):
        s=[e for e in sub if _yr(e["t"])==y]; return (sum(e["out"] for e in s),len(s))
    y25=yr(sel,"2025"); y26=yr(sel,"2026")
    return {
      "N_kept":len(sel),"hit3r_kept":round(w/len(sel),3) if sel else 0,
      "winners_kept":w,"losers_kept":l,"winners_cut":wc,"losers_cut":lc,
      "poison_ratio":round(wc/lc,2) if lc else (99.0 if wc else 0.0),  # <1 = corta mais loser que winner (BOM)
      "y2025":f"{y25[0]}/{y25[1]}","y2026":f"{y26[0]}/{y26[1]}",
      "base":f"{baseW}/{len(ENTRIES)} ({baseW/len(ENTRIES):.1%})",
    }
def causal_swings_upto(j, r=6):
    """swings CONFIRMADOS estritamente antes/na barra j (conf_bar<=j) — CAUSAL. (tp,idx,price,conf_bar)."""
    return [(tp,i,pr,ci) for tp,i,pr,ci in _zz(r) if ci<=j]
if __name__=="__main__":
    W=sum(e["out"] for e in ENTRIES)
    print(f"ENTRIES {len(ENTRIES)} · winners {W} · losers {len(ENTRIES)-W} · base hit-3R {W/len(ENTRIES):.1%}")
    print("R-subset:", sum(1 for e in ENTRIES if e["reclaim_lag"]<=4), "· score(all)=", score([e["n"] for e in ENTRIES]))
    json.dump(ENTRIES, open(HERE/"results"/"agent_ctx_entries_20260707.json","w"), indent=1)
    print("saved results/agent_ctx_entries_20260707.json")
