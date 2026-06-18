#!/usr/bin/env python3
"""OPÇÃO A — valida o TAKE engine EXISTENTE (decisões cegas ao resultado, SEM retune/novo filtro/
reclassificação) particionando por JANELA TEMPORAL e REGIME EXÓGENO, e re-rodando os MESMOS baselines
casados DENTRO de cada partição (baseline absorve o drift do regime -> bater ele = skill, não beta).
Regime exógeno simples: price vs SMA200(4H) no entry -> BULL/NONBULL (NÃO é regime v3, NÃO vira gate).
Priors curados são ~todos 2020 -> validar TAKE em 2023-26 = OOS-relativo-aos-priors."""
import json,csv,gzip,random
from collections import Counter,defaultdict
from datetime import datetime,timezone
random.seed(20260618)
D="results"
fr=[json.loads(l) for l in open("/tmp/raw_features_2020_2026.jsonl")]
H=[r['high'] for r in fr];L=[r['low'] for r in fr];C=[r['close'] for r in fr];O=[r['open'] for r in fr];TS=[r['ts_epoch'] for r in fr];N=len(fr)
ATR=[None]*N;trs=[]
for i in range(1,N):
    trs.append(max(H[i]-L[i],abs(H[i]-C[i-1]),abs(L[i]-C[i-1])))
    if i>=14: ATR[i]=sum(trs[i-14:i])/14
PL5=[False]*N
for j in range(5,N-5):
    if L[j]<min(L[j-5:j]) and L[j]<min(L[j+1:j+6]): PL5[j]=True
def swing_origin(i):
    p=C[i];a=ATR[i];lo=None
    for j in range(i-5,4,-1):
        if PL5[j] and L[j]<p: lo=L[j];break
    if lo is None: lo=min(L[max(0,i-6):i+1])
    return max(p-(lo-0.1*a),0.3*a)
def legpos(i):
    p=C[i];hi=max(H[max(0,i-90):i+1]);lo=min(L[max(0,i-90):i+1]);return 100*(p-lo)/(hi-lo) if hi>lo else 50
def sma(i,n):
    s=C[max(0,i-n+1):i+1];return sum(s)/len(s)
def regime(i):  # EXÓGENO: price vs SMA200 4H (causal). BULL acima, NONBULL abaixo/igual.
    return 'BULL' if C[i]>sma(i,200) else 'NONBULL'
def year(i): return datetime.fromtimestamp(TS[i],tz=timezone.utc).year
RAW="/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD";COB="OB Detector"
GZ=[f"{RAW}/4H/XAUUSD_240m_replay_2020-01-01_to_2023-01-01.jsonl.gz",f"{RAW}/4H/XAUUSD_240m_replay_2023-01-03_to_2026-05-25.jsonl.gz"]
demlow={}
for gz in GZ:
    with gzip.open(gz,'rt') as f:
        for line in f:
            try:d=json.loads(line)
            except:continue
            ov=d.get('ohlcv') or []
            if not ov:continue
            cob=next((s for s in (d.get('pine_boxes') or []) if COB in (s.get('name') or '')),None)
            if cob: demlow[ov[-1]['time']]=[b['low'] for b in (cob.get('all_boxes') or []) if (b.get('text') or '').upper()=='DEMAND' and b.get('low') is not None]
def demand_sl(i):
    p=C[i];a=ATR[i];lows=demlow.get(TS[i])
    if lows:
        below=[lo for lo in lows if lo<p]
        if below:
            nd=max(below)
            if (p-nd)<=5*a: return max(p-(nd-0.1*a),0.3*a)
    return swing_origin(i)
def realR(i,risk=None):
    risk=risk or demand_sl(i);p=C[i];stop=p-risk;pd=False;rz=0.0;rem=1.0;e=min(i+60,N-1)
    for j in range(i+1,e+1):
        if L[j]<=stop:
            f=O[j] if O[j]<=stop else stop;return rz+rem*((f-p)/risk)-0.10
        if not pd and H[j]>=p+2*risk: rz+=1.0;rem=0.5;pd=True;stop=p
        if pd and H[j]>=p+6*risk: return rz+rem*6.0-0.10
    return rz+rem*((C[e]-p)/risk)-0.10
def lpb(lp): return 0 if lp<30 else 1 if lp<55 else 2 if lp<75 else 3
# universo p/ baseline, TAGGED por regime
universe=[i for i in range(200,N-61) if ATR[i] and demlow.get(TS[i]) and any(lo<C[i] for lo in demlow[TS[i]])]
uni_reg=defaultdict(lambda:defaultdict(list))  # regime -> legpos_bucket -> [idx]
for i in universe: uni_reg[regime(i)][lpb(legpos(i))].append(i)
# decisões + outcomes
dec={int(r['bar_idx']):r for fp in __import__('glob').glob('/tmp/qual_dec_*.jsonl') for r in [json.loads(l) for l in open(fp) if l.strip()]}
out={int(r['bar_idx']):r for r in csv.DictReader(open(f"{D}/l2_bpt_trade_qualification_outcomes.csv"))}
for i in out:  # imputa faltante
    if i not in dec: dec[i]={'decision':'SKIP'}
def realR_out(i): return float(out[i]['realR'])
def stats(idx):
    if not idx: return "n=0"
    R=[realR_out(i) for i in idx];n=len(R);w=sum(1 for i in idx if out[i]['exitype'].startswith('WIN'))
    return f"n={n:<3} WR={100*w/n:.0f}% avgR={sum(R)/n:+.3f} sumR={sum(R):+.1f} median={sorted(R)[n//2]:+.2f}"
def base_in_regime(idx,reg,B=4000):
    # random long casado por legpos-bucket, sorteado SÓ de bars DESSE regime
    bc=Counter(lpb(legpos(i)) for i in idx);ms=[]
    for _ in range(B):
        s=[]
        for b,cnt in bc.items():
            pool=uni_reg[reg][b]
            if pool: s+=[pool[random.randrange(len(pool))] for _ in range(cnt)]
        if s: ms.append(sum(realR(i) for i in s)/len(s))
    if not ms: return None
    ms.sort();return ms
print("=== OPÇÃO A — validação OOS/regime do TAKE engine (decisões EXISTENTES, sem retune) ===")
print(f"universo demand-backed por regime: BULL={sum(len(v) for v in uni_reg['BULL'].values())} NONBULL={sum(len(v) for v in uni_reg['NONBULL'].values())}\n")
take=[i for i in out if dec[i]['decision']=='TAKE']
skip=[i for i in out if dec[i]['decision']=='SKIP']
def block(name,members):
    tk=[i for i in take if i in members];sk=[i for i in skip if i in members]
    # baseline casado dentro do regime do bloco (usa o regime de cada trade)
    print(f"--- {name} ---")
    print(f"  TAKE  {stats(tk)}")
    print(f"  SKIP  {stats(sk)}")
    if tk:
        avg=sum(realR_out(i) for i in tk)/len(tk)
        # baseline: para bloco temporal, regime de cada trade; para bloco de regime, o próprio
        regs=Counter(regime(i) for i in tk)
        # mistura: sorteia do regime de cada trade
        bc=Counter((regime(i),lpb(legpos(i))) for i in tk);ms=[]
        for _ in range(4000):
            s=[]
            for (rg,b),cnt in bc.items():
                pool=uni_reg[rg][b]
                if pool:s+=[pool[random.randrange(len(pool))] for _ in range(cnt)]
            if s:ms.append(sum(realR(i) for i in s)/len(s))
        ms.sort();p=sum(1 for x in ms if avg>x)/len(ms)
        print(f"  baseline regime+legpos-matched: avgR[5/50/95]=[{ms[int(.05*len(ms))]:.3f}/{ms[len(ms)//2]:.3f}/{ms[int(.95*len(ms))]:.3f}] delta={avg-ms[len(ms)//2]:+.3f} P(TAKE>rand)={p:.3f}  (regimes TAKE: {dict(regs)})")
    print()
# TEMPORAL
block("2020-2022 (prior-heavy)", {i for i in out if year(i)<=2022})
block("2023-2026 (OOS-relativo-aos-priors)", {i for i in out if year(i)>=2023})
# REGIME EXÓGENO
block("REGIME=BULL (price>SMA200)", {i for i in out if regime(i)=='BULL'})
block("REGIME=NONBULL (price<=SMA200)", {i for i in out if regime(i)=='NONBULL'})
# por ano (diagnóstico de power)
print("--- TAKE por ano (power) ---")
for y in range(2020,2027):
    tk=[i for i in take if year(i)==y]
    if tk: print(f"  {y}: {stats(tk)}  regimes={dict(Counter(regime(i) for i in tk))}")
