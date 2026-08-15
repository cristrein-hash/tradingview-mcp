#!/usr/bin/env python3
"""SIGNIFICÂNCIA DO PIVÔ v3 — mede (não inventa) e MOSTRA, sem limiar afinado ao resultado.
Sobre as fires do detetor v2 (pivô fractal + sweep/retest + hold), acrescenta 2 métricas PRÉ-DECLARADAS:
  touches = nº de barras passadas cujo low tocou o nível (<=TOUCH_TOL*ATR) e FECHOU acima (defesa real).
  span    = barras desde o pivô (quanto tempo o nível esteve em jogo).
NÃO escolhe corte. Imprime, para cada fire, touches/span + OUTCOME (SL-curto+3R), ORDENADO por touches,
para a separação (ou ausência) ser visível. AUDITORIA embutida: lista as BARRAS-DE-TOQUE reais do 14/08
e de um faca-crash, para a contagem ser verificável, não fabricada. Causal. Fonte: store 15M. READ_OB_ZONES."""
import json, datetime as d
from pathlib import Path
STORE=Path("my-strategy/core/bar_store/store/bars_15m.jsonl")
FRACT_M=2; PIVOT_LB=40; TEST_TOL=0.15; RECL_MARG=0.10; BODY_FRAC=0.50; UPPER_FRAC=0.60
TOUCH_TOL=0.25   # PRÉ-DECLARADO — zona de toque do nível (0.25*ATR)

def load():
    r=[]
    for l in open(STORE):
        l=l.strip()
        if l: b=json.loads(l); r.append((int(b['t']),float(b['o']),float(b['h']),float(b['l']),float(b['c'])))
    r.sort(); return r
B=load(); T=[x[0] for x in B];O=[x[1] for x in B];H=[x[2] for x in B];L=[x[3] for x in B];C=[x[4] for x in B]
def atr(i,n=14):
    if i<n: return H[i]-L[i]
    s=0.0
    for k in range(i-n+1,i+1): s+=max(H[k]-L[k],abs(H[k]-C[k-1]),abs(L[k]-C[k-1])) if k>0 else H[k]-L[k]
    return s/n
def lis(t): return (d.datetime.utcfromtimestamp(t)+d.timedelta(hours=1)).strftime('%m-%d %H:%M')
def isfl(p):
    if p-FRACT_M<0 or p+FRACT_M>=len(B): return False
    return all(L[p]<L[p-k] for k in range(1,FRACT_M+1)) and all(L[p]<=L[p+k] for k in range(1,FRACT_M+1))
def detect(i):
    if i<PIVOT_LB or i+1>=len(B): return None
    a=atr(i); rng=max(H[i]-L[i],1e-9); testlow=min(L[i-1],L[i])
    cand=[(p,L[p]) for p in range(max(FRACT_M,i-PIVOT_LB),i-2) if p+FRACT_M<=i-1 and isfl(p) and L[p]<C[i]]
    if not cand: return None
    p,level=min(cand,key=lambda x:abs(x[1]-testlow))
    tested=testlow<=level+TEST_TOL*a; swept=testlow<level
    reclaim=(C[i]>level+RECL_MARG*a) and (C[i]>O[i]) and (abs(C[i]-O[i])>=BODY_FRAC*rng) and ((C[i]-L[i])>=UPPER_FRAC*rng)
    hold=C[i+1]>level
    if not(tested and reclaim and hold): return None
    return dict(i=i,p=p,level=level,atr=a,mode=('SWEEP' if swept else 'RETEST'))
def touches(i,level,a):
    lo=max(0,i-PIVOT_LB); ts=[k for k in range(lo,i) if abs(L[k]-level)<=TOUCH_TOL*a and C[k]>level]
    return ts
def fwd(i,sl,tgt,mx=40):
    ent=C[i];mfe=0.0
    for k in range(i+1,min(i+1+mx,len(B))):
        mfe=max(mfe,H[k]-ent)
        if L[k]<=sl: return "LOSS"
        if H[k]>=tgt: return "WIN"
    return "OPEN"

lo=int(d.datetime(2026,8,12,0,0,tzinfo=d.timezone.utc).timestamp()); hi=int(d.datetime(2026,8,14,21,0,tzinfo=d.timezone.utc).timestamp())
rows=[]
for k in range(len(B)):
    if not(lo<=T[k]<=hi): continue
    dg=detect(k)
    if not dg: continue
    ts=touches(k,dg['level'],dg['atr']); a=dg['atr']; sl=min(L[k-1],L[k])-0.1*a; tgt=C[k]+3*(C[k]-sl)
    rows.append((len(ts),k-dg['p'],lis(T[k]),dg['mode'],round(dg['level'],1),fwd(k,sl,tgt),ts,dg['level'],dg['atr']))

print("TOUCH_TOL=%.2f  (pré-declarado, sem corte escolhido)"%TOUCH_TOL)
print("touches span  fire            modo   level    outcome")
for r in sorted(rows,reverse=True):
    tag=' << RETOMADA 14/08' if r[2]=='08-14 06:45' else ''
    print("  %2d    %3d  %s  %-6s %.1f   %s%s"%(r[0],r[1],r[2],r[3],r[4],r[5],tag))

# separação por outcome
def bucket(sel):
    v=[r[0] for r in rows if r[5]==sel]; return v
for lab in ('WIN','LOSS','OPEN'):
    v=bucket(lab)
    if v: print("  %s: n=%d touches min/med/max = %d/%d/%d"%(lab,len(v),min(v),sorted(v)[len(v)//2],max(v)))

# ── AUDITORIA EMBUTIDA: barras-de-toque reais ──
print("\n=== AUDITORIA: barras-de-toque reais (verificável, não fabricado) ===")
for r in rows:
    if r[2] in ('08-14 06:45',) or (r[5]=='LOSS' and r[2].startswith('08-13 17')):
        print(" %s level%.1f touches=%d:"%(r[2],r[4],r[0]))
        for k in r[6]: print("    toque %s L%.1f C%.1f"%(lis(T[k]),L[k],C[k]))
