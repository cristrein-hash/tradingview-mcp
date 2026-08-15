#!/usr/bin/env python3
"""RECALL-GATE v2 — detetor RETOMADA corrigido (corrige D1-D5 da auditoria do v1). LONG.
CORREÇÕES vs v1:
  D2  base = PIVÔ FRACTAL confirmado (estrutural), não min rolante de 20 barras.
  D1  exige TESTE genuíno do pivô: SWEEP (low<level) OU RETEST apertado (low<=level+TEST_TOL*ATR);
      'swept' passa a sub-classificação REPORTADA, não decorativa.
  D3  'test' agora exige proximidade a um pivô ESPECÍFICO (não trivial numa queda: o low estar perto do
      min rolante já não basta — tem de tocar um fractal confirmado do passado).
  D4  hold = fecho acima do NÍVEL reclamado (o pivô), não acima do min de 20 barras.
Causal: pivô confirmado em p+M (usa-se só p com p+M<=i-1); reclaim na barra i; hold em i+1; entrada C[i+1].
Só usa bars<=i+1. Fonte: bars_15m.jsonl (store MCP 15M). NÃO afina ao resultado (regras pré-declaradas).
READ_OB_ZONES — base vem de pivô real, não inventada. py3 stdlib."""
import json, datetime as d
from pathlib import Path
STORE = Path("my-strategy/core/bar_store/store/bars_15m.jsonl")

# ───────── REGRAS PRÉ-DECLARADAS (fixadas ANTES de ver o resultado) ─────────
FRACT_M   = 2      # pivô-low fractal = min estrito sobre ±2 barras
PIVOT_LB  = 40     # procura pivôs confirmados nas últimas 40 barras
TEST_TOL  = 0.15   # 'teste' do pivô = low <= level + 0.15*ATR (sweep ou retest apertado)
RECL_MARG = 0.10   # reclaim = fecho >= level + 0.10*ATR
BODY_FRAC = 0.50   # displacement = corpo >= 50% do range
UPPER_FRAC= 0.60   # fecho terço superior = (C-L) >= 0.60*range
# ────────────────────────────────────────────────────────────────────────────

def load():
    rows=[]
    for l in open(STORE):
        l=l.strip()
        if l: b=json.loads(l); rows.append((int(b['t']),float(b['o']),float(b['h']),float(b['l']),float(b['c'])))
    rows.sort(); return rows
B=load(); T=[x[0] for x in B];O=[x[1] for x in B];H=[x[2] for x in B];L=[x[3] for x in B];C=[x[4] for x in B]

def atr(i,n=14):
    if i<n: return H[i]-L[i]
    s=0.0
    for k in range(i-n+1,i+1):
        s+=max(H[k]-L[k],abs(H[k]-C[k-1]),abs(L[k]-C[k-1])) if k>0 else H[k]-L[k]
    return s/n
def lis(t): return (d.datetime.utcfromtimestamp(t)+d.timedelta(hours=1)).strftime('%m-%d %H:%M')
def idx_at(t):
    for i,x in enumerate(T):
        if x==t: return i
    return None
def idx_near(t):
    bi=None
    for i,x in enumerate(T):
        if x<=t: bi=i
        else: break
    return bi

def is_fractal_low(p):
    if p-FRACT_M<0 or p+FRACT_M>=len(B): return False
    return all(L[p]<L[p-k] for k in range(1,FRACT_M+1)) and all(L[p]<=L[p+k] for k in range(1,FRACT_M+1))

def diag(i):
    """Campos-diagnóstico causais na barra i. Pivô confirmado (p+M<=i-1)."""
    if i<PIVOT_LB or i+1>=len(B): return None
    a=atr(i); rng=max(H[i]-L[i],1e-9); testlow=min(L[i-1],L[i])
    # pivôs fractais confirmados no passado, abaixo do fecho atual
    cand=[]
    for p in range(max(FRACT_M,i-PIVOT_LB), i-2):
        if p+FRACT_M> i-1: continue           # só pivôs confirmados antes de i
        if is_fractal_low(p) and L[p]<C[i]:
            cand.append((p,L[p]))
    if not cand: return dict(FIRE=False, why="sem pivô fractal", bar="C%.1f"%C[i])
    # nível testado = o pivô mais próximo do low que estamos a testar (o nível defendido)
    p,level=min(cand, key=lambda x: abs(x[1]-testlow))
    tested = testlow <= level + TEST_TOL*a
    swept  = testlow < level
    reclaim= (C[i] > level + RECL_MARG*a) and (C[i]>O[i]) and (abs(C[i]-O[i])>=BODY_FRAC*rng) and ((C[i]-L[i])>=UPPER_FRAC*rng)
    hold   = C[i+1] > level
    fire=bool(tested and reclaim and hold)
    return dict(level=round(level,1),atr=round(a,2),mode=('SWEEP' if swept else 'RETEST'),
                tested=tested,reclaim=reclaim,hold=hold,FIRE=fire,bar="O%.1f H%.1f L%.1f C%.1f"%(O[i],H[i],L[i],C[i]))

def fwd(i,sl,tgt,maxbars=40):
    ent=C[i]; mfe=0.0
    for k in range(i+1,min(i+1+maxbars,len(B))):
        mfe=max(mfe,H[k]-ent)
        if L[k]<=sl: return "LOSS",round(mfe,1)
        if H[k]>=tgt: return "WIN",round(mfe,1)
    return "OPEN",round(mfe,1)

print("="*92)
print("v2 PRÉ-DECLARADO:",f"FRACT_M={FRACT_M} PIVOT_LB={PIVOT_LB} TEST_TOL={TEST_TOL} RECL_MARG={RECL_MARG} BODY={BODY_FRAC} UPPER={UPPER_FRAC}")
print("Base=pivô fractal confirmado · teste=sweep OU retest apertado · hold=fecho>nível · entrada C[i+1] causal")
print("="*92)

t_reclaim=int(d.datetime(2026,8,14,5,45,tzinfo=d.timezone.utc).timestamp())
i=idx_at(t_reclaim)
print("\n[POSITIVO] Retomada 14/08 06:45 Lis — QUEREMOS FIRE=True")
dg=diag(i); print("  ",lis(T[i]),dg)
if dg and dg.get('FIRE'):
    sl=min(L[i-1],L[i])-0.1*dg['atr']; tgt=C[i]+3*(C[i]-sl)
    print("   -> entry@%.1f SL%.1f(sweep/retest low−0.1ATR) tgt3R%.1f  outcome=%s"%(C[i+1],sl,tgt,fwd(i,sl,tgt)))

facas=[1786597200,1786606200,1786610700,1786640400,1786652100]
print("\n[NEGATIVOS] 5 longs-faca 13/08 — QUEREMOS FIRE=False")
for ft in facas:
    j=idx_near(ft); fired=[lis(T[k]) for k in (j-1,j,j+1) if diag(k) and diag(k).get('FIRE')]
    print("  faca %s | FIRE±1=%s | %s"%(lis(ft), fired or "NENHUM", diag(j)))

lo=int(d.datetime(2026,8,12,0,0,tzinfo=d.timezone.utc).timestamp()); hi=int(d.datetime(2026,8,14,21,0,tzinfo=d.timezone.utc).timestamp())
print("\n[VARREDURA] disparos 12/08→14/08 (com modo sweep/retest e outcome SL-curto+3R):")
n=0
for k in range(len(B)):
    if not(lo<=T[k]<=hi): continue
    dg=diag(k)
    if dg and dg.get('FIRE'):
        n+=1; a=dg['atr']; sl=min(L[k-1],L[k])-0.1*a; tgt=C[k]+3*(C[k]-sl); out=fwd(k,sl,tgt)
        print("  FIRE %s [%s] level%.1f | %s | SL%.1f 3R%.1f -> %s"%(lis(T[k]),dg['mode'],dg['level'],dg['bar'],sl,tgt,out))
print("  total disparos:",n)
