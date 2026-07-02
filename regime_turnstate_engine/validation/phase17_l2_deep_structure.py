#!/usr/bin/env python3
"""DISSECAÇÃO PROFUNDA da base canónica L2/BPT 2023+ × regime phase10. Quantifica a tese do Cris:
(A) RANGE: posição-de-entrada-dentro-do-range (causal, vs demanda-fundo) separa winner de loser? Tertis + null + por-ano.
(B) SL_atr × posição × outcome (entrada na demanda → SL apertado → R:R).
(C) MFE-giveback (stopped-before-run): mfe alto + R negativo; mae (profundidade do dip que matou).
(D) BEAR: capitulação-fundo (posição baixa no segmento bear) vs meio-de-downtrend.
let-run pós-custo 0.35. Estrutural, ortogonal a período. Descritivo + null; MFE não-bankable (caveat)."""
import csv,io,contextlib,sys,random,statistics as st,datetime as dt
from pathlib import Path
COST=0.35;VAL=Path("/Users/cristrein/tradingview-mcp/regime_turnstate_engine/validation");sys.path.insert(0,str(VAL))
with contextlib.redirect_stdout(io.StringIO()): import phase10_hybrid_regime as P
reg=P.run(0.03,1.15,0.88);T=P.T;B4=P.B4;H=P.H;L=P.L;C=P.C
D=Path("/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/results")
slx={int(r["i"]):r for r in csv.DictReader(open(D/"l2_bpt_sl_context_policy_results.csv"))}
def seg_bounds(bi):
    """segmento contíguo do MESMO regime que contém bi; range_lo/hi CAUSAL (do início do segmento até bi)."""
    rg=reg[bi];s=bi
    while s>0 and reg[s-1]==rg: s-=1
    lo=min(L[s:bi+1]);hi=max(H[s:bi+1]);return s,lo,hi
rows=[]
for r in csv.DictReader(open(D/"l2_bpt_regua_structural.csv")):
    bi=int(r["bar_idx"]);t=T[bi];y=dt.datetime.utcfromtimestamp(t).year
    if y<2023: continue
    R=round(float(r["letrun_struct"])-COST,2);mfe=float(r["mfe_struct"]);entry=float(r["entry"])
    s,lo,hi=seg_bounds(bi);pos=(entry-lo)/(hi-lo) if hi>lo else 0.5
    sx=slx.get(bi,{})
    rows.append({"bi":bi,"date":dt.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d"),"yr":y,"regime":reg[bi],
        "entry":entry,"R":R,"mfe":mfe,"win":R>0,"pos":pos,"sl_atr":float(sx.get("sl_atr",0) or 0)})
def stats(g):
    n=len(g);return n,(100*sum(1 for x in g if x['win'])/n if n else 0),sum(x['R'] for x in g),(sum(x['R'] for x in g)/n if n else 0)
print("="*86);print("(A) RANGE — POSIÇÃO-DE-ENTRADA NO RANGE (0=demanda-fundo, 1=topo) vs OUTCOME");print("="*86)
RG=[x for x in rows if x['regime']=='RANGE']
RG.sort(key=lambda x:x['pos'])
ter=len(RG)//3
for nm,g in [("FUNDO (pos baixa 1/3)",RG[:ter]),("MEIO 1/3",RG[ter:2*ter]),("TOPO (pos alta 1/3)",RG[2*ter:])]:
    n,wr,s,a=stats(g);print(f"  {nm:24} N={n:2} WR={wr:3.0f}% sumR={s:+6.1f} avgR={a:+5.2f} | pos médio {sum(x['pos'] for x in g)/n:.2f} SLatr médio {sum(x['sl_atr'] for x in g)/n:.1f}")
# null: a diferença avgR fundo-vs-topo é estrutural?
bot=[x['R'] for x in RG if x['pos']<=0.4];top=[x['R'] for x in RG if x['pos']>=0.6]
if bot and top:
    real=st.mean(bot)-st.mean(top);allR=[x['R'] for x in RG];posflag=[1 if x['pos']<=0.4 else 0 for x in RG]
    random.seed(7);dd=[]
    for _ in range(2000):
        random.shuffle(posflag);b=[allR[i] for i in range(len(RG)) if posflag[i]];t2=[allR[i] for i in range(len(RG)) if not posflag[i]]
        if b and t2: dd.append(st.mean(b)-st.mean(t2))
    p=sum(1 for x in dd if abs(x)>=abs(real))/len(dd)
    print(f"  >> FUNDO(pos≤0.4, n{len(bot)}) avgR {st.mean(bot):+.2f}  vs  TOPO(pos≥0.6, n{len(top)}) avgR {st.mean(top):+.2f}  | diff {real:+.2f} null_p={p:.3f}")
print("  por-ano (FUNDO≤0.4 vs TOPO≥0.6 avgR) — estrutura ou calendário?")
for yy in sorted(set(x['yr'] for x in RG)):
    b=[x['R'] for x in RG if x['yr']==yy and x['pos']<=0.4];tp=[x['R'] for x in RG if x['yr']==yy and x['pos']>=0.6]
    fb=f"{st.mean(b):+.2f}(n{len(b)})" if b else "-(n0)";ft=f"{st.mean(tp):+.2f}(n{len(tp)})" if tp else "-(n0)"
    print(f"    {yy}: fundo {fb} / topo {ft}")
print("\n"+"="*86);print("(B) MESMA ANÁLISE no BULL (a posição-no-pullback importa lá também?)");print("="*86)
BL=[x for x in rows if x['regime']=='BULL'];BL.sort(key=lambda x:x['pos']);t2=len(BL)//3
for nm,g in [("FUNDO 1/3",BL[:t2]),("MEIO 1/3",BL[t2:2*t2]),("TOPO 1/3",BL[2*t2:])]:
    n,wr,s,a=stats(g);print(f"  BULL {nm:12} N={n:2} WR={wr:3.0f}% sumR={s:+6.1f} avgR={a:+5.2f} pos {sum(x['pos'] for x in g)/n:.2f}")
print("\n"+"="*86);print("(C) MFE-GIVEBACK: trades com MFE>=5R que realizaram <=0 (stopped-before-run)");print("="*86)
gv=[x for x in rows if x['mfe']>=5 and x['R']<=0]
from collections import Counter
print(f"  total give-backs: {len(gv)} | por regime {dict(Counter(x['regime'] for x in gv))} | MFE somado PERDIDO ~{sum(x['mfe'] for x in gv):.0f}R potencial")
print("  os piores (MFE>=10R → loss):")
for x in sorted(gv,key=lambda x:-x['mfe'])[:8]:
    print(f"    {x['date']} {x['regime']:5} entry {x['entry']:.0f} MFE {x['mfe']:.1f}R → R {x['R']:+.2f} (SLatr {x['sl_atr']:.1f})")
print("\n"+"="*86);print("(D) BEAR: capitulação-fundo vs meio-de-downtrend (posição no segmento bear)");print("="*86)
BR=[x for x in rows if x['regime']=='BEAR']
for x in sorted(BR,key=lambda x:x['bi']):
    tag="CAPITULAÇÃO?" if x['pos']<=0.25 else ("meio/topo" if x['pos']>=0.5 else "")
    if x['win'] or x['mfe']>=4 or x['pos']<=0.25:
        print(f"    {x['date']} pos {x['pos']:.2f} R {x['R']:+.2f} MFE {x['mfe']:.1f} {tag}")
bw=[x for x in BR if x['win']];print(f"  BEAR winners: {len(bw)} | pos médio dos winners {sum(x['pos'] for x in bw)/len(bw) if bw else 0:.2f} (baixo=capitulação)")
