#!/usr/bin/env python3
"""TESTA (Cris aprovou) as 2 intervenções SEPARADAS na base canónica L2/BPT (universo 276 + SL_CONTEXT + let-run):
(A) SKIP entradas no MEIO do range (pos 0.33-0.66, a zona-morte) — filtro de ENTRADA. Efeito na curva + por-ano.
(B) TUNE-FINO de SL só nas entradas de FUNDO (pos<0.33): stop por CLOSE (tolera wick) vs stop por WICK (baseline),
    MESMA SL/RxR — converte give-back em R real? Simulo let-run (verifico que reproduz letrun_struct antes).
Custo 0.35R. HZ=120. CALIBRAÇÃO (skips/tunes calibrados nos mesmos 276) — por-ano é o juiz; não é promoção."""
import csv,io,contextlib,sys,statistics as st,datetime as dt
from pathlib import Path
COST=0.35;HZ=120;VAL=Path("/Users/cristrein/tradingview-mcp/regime_turnstate_engine/validation");sys.path.insert(0,str(VAL))
with contextlib.redirect_stdout(io.StringIO()): import phase10_hybrid_regime as P
reg=P.run(0.03,1.15,0.88);T=P.T;H=P.H;L=P.L;C=P.C;n4=len(C)
D=Path("/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/results")
def seg_lo_hi(bi):
    rg=reg[bi];s=bi
    while s>0 and reg[s-1]==rg: s-=1
    return min(L[s:bi+1]),max(H[s:bi+1])
def sim(bi,entry,sl,mode):
    risk=entry-sl
    if risk<=0: return None
    end=min(bi+HZ,n4-1)
    for j in range(bi+1,end+1):
        if mode=="wick" and L[j]<=sl: return -1.0
        if mode=="close" and C[j]<=sl: return (C[j]-entry)/risk
    return (C[end]-entry)/risk
rows=[]
for r in csv.DictReader(open(D/"l2_bpt_regua_structural.csv")):
    bi=int(r["bar_idx"]);y=dt.datetime.utcfromtimestamp(T[bi]).year
    if y<2023: continue
    entry=float(r["entry"]);sl=float(r["sl"]);lo,hi=seg_lo_hi(bi)
    pos=(entry-lo)/(hi-lo) if hi>lo else 0.5
    rows.append({"bi":bi,"yr":y,"regime":reg[bi],"entry":entry,"sl":sl,"pos":pos,
        "letrun":float(r["letrun_struct"]),"mfe":float(r["mfe_struct"]),
        "R_wick":round((sim(bi,entry,sl,"wick") or 0)-COST,2),
        "R_close":round((sim(bi,entry,sl,"close") or 0)-COST,2)})
def curve(rs):
    rs=sorted(rs,key=lambda x:x["bi"]);n=len(rs);s=sum(x["R_wick"] for x in rs);w=sum(1 for x in rs if x["R_wick"]>0)
    cum=peak=dd=0;cs=mxl=0
    for x in rs:
        cum+=x["R_wick"];peak=max(peak,cum);dd=min(dd,cum-peak);cs=cs+1 if x["R_wick"]<=0 else 0;mxl=max(mxl,cs)
    return f"N={n:3} WR={100*w/n:3.0f}% sumR={s:+6.1f} avgR={s/n:+5.2f} DD={dd:6.1f} loseStk={mxl}"
# verificação do simulador
err=max(abs(x["R_wick"]+COST-x["letrun"]) for x in rows)
print(f"[verificação] sim wick vs letrun_struct: erro máx = {err:.2f} ({'OK reproduz' if err<0.4 else 'DIVERGE — rever'})")
print("\n"+"="*80);print("(A) SKIP MEIO-DO-RANGE (pos 0.33-0.66) — filtro de entrada");print("="*80)
mid=[x for x in rows if x["regime"]=="RANGE" and 0.33<=x["pos"]<0.66]
keep=[x for x in rows if x not in mid]
print(f"  trades no meio-range removidos: {len(mid)} (sumR desses: {sum(x['R_wick'] for x in mid):+.1f})")
print(f"  BASE (131):        {curve(rows)}")
print(f"  BASE − meio-range: {curve(keep)}")
print("  por-ano (Δ sumR ao remover meio-range) — ajuda todo ano ou só onde meio foi mau?")
for y in sorted(set(x['yr'] for x in rows)):
    b=sum(x['R_wick'] for x in rows if x['yr']==y);k=sum(x['R_wick'] for x in keep if x['yr']==y)
    m=[x for x in mid if x['yr']==y];print(f"    {y}: base {b:+6.1f} -> filtrado {k:+6.1f}  (Δ {k-b:+.1f}, removidos {len(m)})")
print("\n"+"="*80);print("(B) TUNE-FINO SL nas entradas de FUNDO (pos<0.33): CLOSE-stop vs WICK-stop, MESMA SL");print("="*80)
fun=[x for x in rows if x["regime"]=="RANGE" and x["pos"]<0.33]
sw=sum(x["R_wick"] for x in fun);scl=sum(x["R_close"] for x in fun)
ww=sum(1 for x in fun if x["R_wick"]>0);wcl=sum(1 for x in fun if x["R_close"]>0)
print(f"  entradas de FUNDO (RANGE pos<0.33): N={len(fun)}")
print(f"  WICK-stop (baseline): sumR {sw:+.1f} | WR {100*ww/len(fun):.0f}%")
print(f"  CLOSE-stop (tune):    sumR {scl:+.1f} | WR {100*wcl/len(fun):.0f}%   (Δ {scl-sw:+.1f}R)")
print("  trades onde o tune converteu wick-stop→run (R_wick<=0 mas R_close>0):")
for x in sorted(fun,key=lambda z:z["R_close"]-z["R_wick"],reverse=True):
    if x["R_close"]-x["R_wick"]>0.5:
        print(f"    {dt.datetime.utcfromtimestamp(T[x['bi']]).strftime('%Y-%m-%d')} pos {x['pos']:.2f} wick {x['R_wick']:+.2f} -> close {x['R_close']:+.2f} (MFE {x['mfe']:.1f})")
print("  ⚠️ trades onde o tune PIOROU (close-stop deixou perda maior):")
for x in fun:
    if x["R_close"]-x["R_wick"]<-0.3:
        print(f"    {dt.datetime.utcfromtimestamp(T[x['bi']]).strftime('%Y-%m-%d')} wick {x['R_wick']:+.2f} -> close {x['R_close']:+.2f}")
