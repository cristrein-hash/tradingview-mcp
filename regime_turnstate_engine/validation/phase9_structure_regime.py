#!/usr/bin/env python3
"""RTSE Fase 9 — REGIME POR ESTRUTURA (3 estados BULL/RANGE/BEAR), como o Cris lê (BOS/CHoCH, HH/HL vs LH/LL).
Conserta os 2 problemas de leitura: (A) bear-espúrio-em-bull = RANGE de acumulação (segura fundo, re-expande);
(B) bounce-em-bear que NÃO toma topo anterior (lower-high) NÃO vira BULL. Zigzag causal %; regime pelas 2 últimas
swings: HH&HL=BULL, LH&LL=BEAR, misto=RANGE. Aplicado na barra de CONFIRMAÇÃO (causal, com lag honesto).
Leitura multi-fatorial por TRAJETÓRIA (sequência de swings), 3 estados, validada 3-classe vs gabarito + CHECK 2026."""
import json,csv,math,statistics as st,bisect,datetime as dt
from pathlib import Path
ROOT=Path("/Users/cristrein/tradingview-mcp");REV=ROOT/"my-strategy/research/revalidation";GT=ROOT/"regime_turnstate_engine/ground_truth"
def load(p): b=[json.loads(l) for l in p.read_text().splitlines()];b.sort(key=lambda x:x["t"]);return b
B4=load(REV/"raw_4h_ohlc.jsonl");T=[b["t"] for b in B4];C=[b["c"] for b in B4];n=len(B4)
boxes=[]
for r in csv.DictReader(open(GT/"cris_regime_boxes.csv")):
    if r["role"]=="MACRO": boxes.append((int(r["start"]),int(r["end"]),r["family"]))
def gt_at(ts):
    for s,e,f in boxes:
        if s<=ts<=e: return f
    return None
def zigzag(p):
    piv=[];dirn=0;hi_p=C[0];hi_i=0;lo_p=C[0];lo_i=0
    for i in range(1,n):
        if C[i]>hi_p: hi_p=C[i];hi_i=i
        if C[i]<lo_p: lo_p=C[i];lo_i=i
        if dirn>=0 and C[i]<=hi_p*(1-p):       # caiu p% do topo corrente -> confirma HIGH
            piv.append((i,hi_i,hi_p,'H'));dirn=-1;lo_p=C[i];lo_i=i
        elif dirn<=0 and C[i]>=lo_p*(1+p):      # subiu p% do fundo corrente -> confirma LOW
            piv.append((i,lo_i,lo_p,'L'));dirn=1;hi_p=C[i];hi_i=i
    return piv
def regime_timeline(p):
    """BOS IMEDIATO: vira BULL quando rompe o topo confirmado anterior, BEAR quando rompe o fundo confirmado,
    RANGE quando rompe um e logo o outro (oscila dentro). Sem esperar confirmação do novo pivô (sem lag)."""
    piv=zigzag(p);reg=[None]*n;pi=0;SH=None;SL=None;regime=None;last_break=None;changes=[]
    for i in range(n):
        while pi<len(piv) and piv[pi][0]<=i:
            _,ip,price,kind=piv[pi]
            if kind=='H': SH=price
            else: SL=price
            pi+=1
        new=regime
        if SH is not None and C[i]>SH:
            new='RANGE' if last_break=='DN' else 'BULL';last_break='UP'
        elif SL is not None and C[i]<SL:
            new='RANGE' if last_break=='UP' else 'BEAR';last_break='DN'
        # RANGE->trend reconfirma: se mantém quebrando o mesmo lado vira tendência
        if new=='RANGE' and regime in('BULL','BEAR'): pass
        if new!=regime: changes.append((i,new))
        regime=new;reg[i]=regime
    return reg,changes
def validate(p):
    reg,changes=regime_timeline(p);agree=tot=0;cnt={'BULL':0,'RANGE':0,'BEAR':0}
    for i in range(n):
        g=gt_at(T[i]);r=reg[i]
        if g is None or r is None: continue
        tot+=1;agree+=(g==r);cnt[g]+=1
    base=max(cnt.values())/tot if tot else 0
    b0,b1=1769727600,1782770400;bb=br=bg=0
    for i in range(n):
        if b0<=T[i]<=b1 and reg[i]:
            bb+=(reg[i]=='BEAR');br+=(reg[i]=='RANGE');bg+=(reg[i]=='BULL')
    t26=bb+br+bg
    return reg,changes,(agree/tot if tot else 0),base,tot,(bb,br,bg,t26)
print(f"{'p%':>4}{'mudanças':>10}{'concord3':>10}{'baseline':>10}  | 2026 macro-BEAR lido como:")
best=0.05
for p in [0.03,0.04,0.05,0.06,0.07]:
    reg,changes,acc,base,tot,(bb,br,bg,t26)=validate(p)
    print(f"{p*100:>4.0f}{len(changes):>10}{acc*100:>9.0f}%{base*100:>9.0f}%  | BEAR {100*bb/t26 if t26 else 0:>3.0f}% / RANGE {100*br/t26 if t26 else 0:>3.0f}% / BULL {100*bg/t26 if t26 else 0:>3.0f}%")
reg,changes,acc,base,tot,_=validate(best)
segs=[];i0=0
for i in range(1,n):
    if reg[i]!=reg[i-1]:
        if reg[i-1] is not None: segs.append((T[i0],T[i],reg[i-1]))
        i0=i
if reg[-1] is not None: segs.append((T[i0],T[-1],reg[-1]))
out=[]
for s,e,f in segs:
    if e<1704067200: continue
    i_s=bisect.bisect_left(T,s);i_e=bisect.bisect_right(T,e)
    if i_e<=i_s: continue
    hi=max(b["h"] for b in B4[i_s:i_e]);lo=min(b["l"] for b in B4[i_s:i_e])
    out.append({"start":int(s),"end":int(e),"regime":f,"hi":round(hi,2),"lo":round(lo,2),
                "d0":dt.datetime.utcfromtimestamp(s).strftime("%Y-%m-%d"),"d1":dt.datetime.utcfromtimestamp(e).strftime("%Y-%m-%d")})
json.dump(out,open("/tmp/causal_segments_v9.json","w"))
print(f"\nSEGMENTOS ESTRUTURAIS (p={best*100:.0f}%) janela 2024+: {len(out)}")
for s in out: print(f"  {s['regime']:5} {s['d0']} -> {s['d1']}  ({s['lo']}-{s['hi']})")
