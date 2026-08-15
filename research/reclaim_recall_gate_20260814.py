#!/usr/bin/env python3
"""RECALL-GATE do detetor RETOMADA (sweep/retest -> reclaim-displacement -> hold) — LONG.
Pergunta: o detetor (a) APANHA a retomada de 14/08 06:45 Lis (que o sistema perdeu) e
          (b) REJEITA os 5 longs-faca de 13/08 (que o sistema deu e perderam)?
NÃO afina thresholds ao resultado — regras PRÉ-DECLARADAS abaixo. Emite os campos-diagnóstico de
cada caso (separação visível). Causal: entrada no fecho da barra-hold (i+1); só usa bars<=i+1.
Fonte: my-strategy/core/bar_store/store/bars_15m.jsonl (store MCP-capturado, 15M canónico live).
READ_OB_ZONES — este script NÃO inventa zona: a base = min-low estrutural das barras reais. py3 stdlib."""
import json, datetime as d
from pathlib import Path

STORE = Path("my-strategy/core/bar_store/store/bars_15m.jsonl")

# ───────── REGRAS PRÉ-DECLARADAS (fixadas ANTES de ver o resultado; não tocar p/ "fazer passar") ─────────
LB = 20          # janela p/ a base (swing-low recente) = [i-LB, i-3]  (5h em 15M)
RETEST_ATR = 0.30   # retest = preço volta a <= base + 0.30*ATR
RECLAIM_ATR = 0.10  # reclaim = fecho > base + 0.10*ATR (margem acima do nível)
BODY_FRAC = 0.50    # displacement = corpo >= 50% do range da barra
UPPER_FRAC = 0.60   # fecho no terço superior = (C-L) >= 0.60*range
# ─────────────────────────────────────────────────────────────────────────────────────────────────────

def load():
    rows=[]
    for l in open(STORE):
        l=l.strip()
        if not l: continue
        b=json.loads(l); rows.append((int(b['t']),float(b['o']),float(b['h']),float(b['l']),float(b['c'])))
    rows.sort()
    return rows

B=load()
T=[x[0] for x in B]; O=[x[1] for x in B]; H=[x[2] for x in B]; L=[x[3] for x in B]; C=[x[4] for x in B]

def atr(i,n=14):
    if i<n: return H[i]-L[i]
    s=0.0
    for k in range(i-n+1,i+1):
        tr=max(H[k]-L[k], abs(H[k]-C[k-1]), abs(L[k]-C[k-1])) if k>0 else H[k]-L[k]
        s+=tr
    return s/n

def lis(t): return (d.datetime.utcfromtimestamp(t)+d.timedelta(hours=1)).strftime('%m-%d %H:%M')
def idx_at(t):
    for i,x in enumerate(T):
        if x==t: return i
    return None
def idx_near(t):  # barra cujo t <= dado t (entrada A1/A2 pode não cair no fecho exato)
    best=None
    for i,x in enumerate(T):
        if x<=t: best=i
        else: break
    return best

def diag(i):
    """Campos-diagnóstico do detetor na barra i (reclaim candidate). Causal: usa bars<=i+1."""
    if i<LB+3 or i+1>=len(B): return None
    a=atr(i)
    base=min(L[i-LB:i-2])                     # base estrutural (recente), exclui as 2 ultimas
    rng=max(H[i]-L[i],1e-9)
    retest = min(L[i-1],L[i]) <= base + RETEST_ATR*a
    swept  = min(L[i-1],L[i]) < base
    reclaim = (C[i] > base + RECLAIM_ATR*a) and ((C[i]-O[i])>0) and \
              ((abs(C[i]-O[i]))>=BODY_FRAC*rng) and ((C[i]-L[i])>=UPPER_FRAC*rng)
    hold = C[i+1] > base
    fire = bool(retest and reclaim and hold)
    return dict(base=round(base,1), atr=round(a,2), swept=swept, retest=retest,
                reclaim=reclaim, hold=hold, FIRE=fire,
                bar="O%.1f H%.1f L%.1f C%.1f"%(O[i],H[i],L[i],C[i]))

def fwd(i, sl, tgt, up=True, maxbars=40):
    """outcome forward causal a partir do fecho da barra i: WIN/LOSS/OPEN + MFE."""
    ent=C[i]; mfe=0.0
    for k in range(i+1,min(i+1+maxbars,len(B))):
        mfe=max(mfe, H[k]-ent if up else ent-L[k])
        if up:
            if L[k]<=sl: return "LOSS", round(mfe,1)
            if H[k]>=tgt: return "WIN", round(mfe,1)
    return "OPEN", round(mfe,1)

print("="*90)
print("REGRAS PRÉ-DECLARADAS:", f"LB={LB} RETEST_ATR={RETEST_ATR} RECLAIM_ATR={RECLAIM_ATR} BODY={BODY_FRAC} UPPER={UPPER_FRAC}")
print("Entrada = fecho da barra-hold (i+1), causal. Base = min-low[i-LB:i-2] (estrutural real).")
print("="*90)

# ── POSITIVO: retomada 14/08 06:45 Lis = 05:45 UTC ──
t_reclaim=int(d.datetime(2026,8,14,5,45,tzinfo=d.timezone.utc).timestamp())
i=idx_at(t_reclaim)
print("\n[POSITIVO] Retomada 14/08 06:45 Lis (o sistema PERDEU) — QUEREMOS FIRE=True")
if i is None: print("  barra não encontrada")
else:
    dg=diag(i); print("  ", lis(T[i]), dg)
    if dg and dg['FIRE']:
        sl=min(L[i-1],L[i])-0.1*dg['atr']; tgt=C[i]+3*(C[i]-sl)
        print("   -> entry@%.1f SL%.1f(swept-0.1ATR) tgt3R%.1f  outcome=%s"%(C[i+1],sl,tgt,fwd(i, sl, tgt)))

# ── NEGATIVOS: 5 longs-faca de 13/08 (o sistema DEU, perderam) ──
facas=[1786597200,1786606200,1786610700,1786640400,1786652100]  # 08-13 06:00/08:30/09:45/18:00/21:15 Lis
print("\n[NEGATIVOS] 5 longs-faca de 13/08 (o sistema DEU) — QUEREMOS FIRE=False em todos")
for ft in facas:
    j=idx_near(ft)
    # testa a barra da entrada e as +-1 à volta (o detetor pode disparar adjacente)
    fired=[]
    for k in (j-1,j,j+1):
        dg=diag(k)
        if dg and dg['FIRE']: fired.append(lis(T[k]))
    dg=diag(j)
    print("  faca %s ent~%.1f | FIRE_janela±1=%s | barra: %s"%(lis(ft), C[j] if j else 0, fired or "NENHUM", dg))

# ── VARREDURA COMPLETA: todos os FIRE em 08-12→08-14 (ver falsos positivos escondidos) ──
lo=int(d.datetime(2026,8,12,0,0,tzinfo=d.timezone.utc).timestamp()); hi=int(d.datetime(2026,8,14,21,0,tzinfo=d.timezone.utc).timestamp())
print("\n[VARREDURA] todos os disparos do detetor 12/08→14/08:")
n=0
for i in range(len(B)):
    if not (lo<=T[i]<=hi): continue
    dg=diag(i)
    if dg and dg['FIRE']:
        n+=1; print("   FIRE", lis(T[i]), "base%.1f swept=%s | %s"%(dg['base'],dg['swept'],dg['bar']))
print("   total disparos:", n)
