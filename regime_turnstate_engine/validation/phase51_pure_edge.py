#!/usr/bin/env python3
"""Cris: TESTE DO EDGE-PURO. Separar edge-de-entrada do beta-de-exit. As entradas estruturais (gatilho-de-zona) medidas
com 4 exits: let-run HZ120 (colhe beta) vs NEUTROS-AO-BETA (target +2R, target +3R, exit-no-fim-do-regime).
Controlo: entradas ALEATÓRIAS (100 draws) no mesmo regime, mesmos exits. Se estrutural só bate random no let-run = BETA.
Se estrutural > random-p95 com target-fixo/exit-regime = EDGE de entrada real. custo 0.35."""
import json,io,contextlib,sys,bisect,random,datetime as dt
from pathlib import Path
random.seed(20260701)
COST=0.35;HZ=120
VAL=Path("/Users/cristrein/tradingview-mcp/regime_turnstate_engine/validation");sys.path.insert(0,str(VAL))
with contextlib.redirect_stdout(io.StringIO()): import phase10_hybrid_regime as P
reg=P.run(0.03,1.15,0.88);T=P.T;H=P.H;L=P.L;C=P.C;n4=len(C)
def atr(i,k=14): return sum(max(H[j]-L[j],abs(H[j]-C[j-1]),abs(L[j]-C[j-1])) for j in range(i-k+1,i+1))/k
segs=sorted(json.load(open("/tmp/causal_segments_v10.json")),key=lambda s:s['start'])
for s in segs: s['bars']=(s['end']-s['start'])/14400
def bear_deep(idx):
    bs=segs[idx]['start'];win=180*86400
    cand=[s for j,s in enumerate(segs) if j<idx and s['bars']>=15 and s['start']>=bs-win]
    if not cand: cand=[s for j,s in enumerate(segs) if j<idx and s['bars']>=15]
    if not cand: return None
    lo=min(s['lo'] for s in cand);amp=max(s['hi']-s['lo'] for s in cand);return (lo,lo+amp/3)
# ---- EXITS ----
def ex_letrun(bi,entry,sl,segend):
    end=min(bi+HZ,n4-1)
    for j in range(bi+1,end+1):
        if L[j]<=sl: return -1.0
    return (C[end]-entry)/(entry-sl)
def ex_target(bi,entry,sl,segend,m):
    risk=entry-sl;tgt=entry+m*risk;end=min(bi+HZ,n4-1)
    for j in range(bi+1,end+1):
        if L[j]<=sl: return -1.0
        if H[j]>=tgt: return float(m)
    return (C[end]-entry)/risk
def ex_regime(bi,entry,sl,segend):
    end=min(segend,bi+HZ,n4-1)
    for j in range(bi+1,end+1):
        if L[j]<=sl: return -1.0
    return (C[end]-entry)/(entry-sl) if end>bi else 0.0
EXITS=[("let-run120",lambda bi,e,s,se:ex_letrun(bi,e,s,se)),("target+2R",lambda bi,e,s,se:ex_target(bi,e,s,se,2)),
       ("target+3R",lambda bi,e,s,se:ex_target(bi,e,s,se,3)),("exit-fim-regime",lambda bi,e,s,se:ex_regime(bi,e,s,se))]
# ---- ENTRADAS ESTRUTURAIS (gatilho-de-zona, = phase50) ----
def struct_entries():
    out=[]
    for idx in range(1,len(segs)):
        s=segs[idx];prev=segs[idx-1];amp=prev['hi']-prev['lo']
        i0=bisect.bisect_left(T,s['start']);i1=bisect.bisect_right(T,s['end'])-1
        if i1-i0<3: continue
        if s['regime']=='BULL':
            niv=prev['hi'];zlo=niv-amp/3
            k=next((j for j in range(i0,i1+1) if C[j]>niv),None)
            if k is None: continue
            rj=next((j for j in range(k+1,min(k+21,i1+1)) if L[j]<=niv),None)
            if rj is not None: out.append((rj,C[rj],zlo-0.5*atr(rj),i1))
            else: out.append((i0,C[i0],min(L[i0:k+1])-0.5*atr(i0),i1))
        elif s['regime']=='BEAR':
            zd=bear_deep(idx)
            if not zd: continue
            j=next((j for j in range(i0,i1+1) if L[j]<=zd[1]),None)
            if j is not None: out.append((j,C[j],zd[0]-0.5*atr(j),i1))
        else:
            for j in range(i0+2,i1+1):
                rmin=min(L[i0:j+1]);rmax=max(H[i0:j+1])
                if rmax>rmin and (C[j]-rmin)/(rmax-rmin)<0.34: out.append((j,C[j],rmin-0.5*atr(j),i1));break
    return out
def rand_entries():
    """1 entrada aleatória por regime-box (mesmos boxes), SL=entry-1.5ATR"""
    out=[]
    for idx in range(1,len(segs)):
        s=segs[idx];i0=bisect.bisect_left(T,s['start']);i1=bisect.bisect_right(T,s['end'])-1
        if i1-i0<3: continue
        j=random.randint(i0,i1-1);e=C[j];out.append((j,e,e-1.5*atr(j),i1))
    return out
struct=struct_entries()
def evalset(ents,exitfn):
    rs=[round((exitfn(bi,e,sl,se) or 0)-COST,2) for bi,e,sl,se in ents if e-sl>0]
    return sum(rs),sum(rs)/len(rs) if rs else 0,100*sum(1 for r in rs if r>0)/len(rs) if rs else 0,len(rs)
print(f"ENTRADAS ESTRUTURAIS (gatilho-de-zona): N={len(struct)}\n")
print(f"{'EXIT':18} {'ESTRUTURAL sumR/avgR/WR':32} {'RANDOM(100draws) sumR med/p95':32} veredito")
for name,fn in EXITS:
    s_sum,s_avg,s_wr,s_n=evalset(struct,fn)
    rsums=[]
    for _ in range(100):
        rsum,_,_,_=evalset(rand_entries(),fn);rsums.append(rsum)
    rsums.sort();rmed=rsums[50];rp95=rsums[95]
    verd="EDGE" if s_sum>rp95 else ("~beta/random" if s_sum<=rmed else "acima-mediana")
    print(f"{name:18} {f'{s_sum:+6.1f}/{s_avg:+5.2f}/{s_wr:3.0f}%':32} {f'med{rmed:+6.1f} / p95{rp95:+6.1f}':32} {verd}")
print("\nLeitura: se ESTRUTURAL só é EDGE no let-run mas ~random nos target-fixo/exit-regime => o lucro era BETA do exit, não edge de entrada.")
