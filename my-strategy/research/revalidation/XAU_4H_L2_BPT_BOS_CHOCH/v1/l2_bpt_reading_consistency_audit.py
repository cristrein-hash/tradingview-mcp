#!/usr/bin/env python3
"""CONSISTÊNCIA DA LEITURA — o bloco completo dos 276 (lido em 14 lotes) aplicou o eixo de condicionamento
weekly_slope+cascade (o critério que a leitura à mão dos 8 bear-cases descobriu), ou rotulou pela superfície?
Confere os rótulos LEGITIMATE_BEAR_BUY vs BEAR_PULLBACK_TRAP contra weekly_slope/cascade + se a narrativa
cita o eixo. Diagnóstico de QUALIDADE da leitura, NÃO lift test. Outcome só p/ contexto, nunca árbitro."""
import json, csv, re
D="results"
RD={int(json.loads(l)['episode_id']):json.loads(l) for l in open(f"{D}/l2_bpt_episode_readings_276.jsonl")}
PK={int(json.loads(l)['episode_id']):json.loads(l) for l in open(f"{D}/l2_bpt_episode_context_packets_276.jsonl")}
def fn(v):
    try: return float(v)
    except: return None
def weekly_of(b):
    w=PK[b]['weekly_1d_context']
    return fn(w.get('weekly_slope_decisions')) if fn(w.get('weekly_slope_decisions')) is not None else fn(w.get('weekly_slope_20pct'))
def cascade_of(b):
    rb=PK[b]['regime_B']; c=fn(rb.get('cascade_score'))
    if c is None: c=fn(PK[b]['dspa_path'].get('cascade_now'))
    return c
def mfe(b): return PK[b]['_AUDIT_outcome_NOT_FOR_READING']['mfe_R']
AXIS=re.compile(r'weekl|seman|cascade|cascata|timeframe (maior|superior)|higher.?tf|htf', re.I)

for cls in ('LEGITIMATE_BEAR_BUY','BEAR_PULLBACK_TRAP'):
    bs=[b for b in RD if RD[b]['episode_type']==cls]
    print("="*92); print(f"{cls}  n={len(bs)}")
    # critério-semente: legit = weekly>=0 OU cascade raso(>=-1); trap = weekly<0 E cascade profundo(<=-2)
    cites=0; wk_pos=0; casc_shallow=0; rows=[]
    for b in bs:
        wk=weekly_of(b); c=cascade_of(b)
        narr=(RD[b].get('conditioning_principal','')+' '+RD[b].get('narrative',''))
        cited=bool(AXIS.search(narr)); cites+=cited
        if wk is not None and wk>=0: wk_pos+=1
        if c is not None and c>=-1: casc_shallow+=1
        rows.append((b,RD[b].get('timestamp','')[:10],wk,c,round(mfe(b),1),RD[b]['provisional_decision'],cited))
    print(f"  narrativa CITA o eixo (weekly/cascade/htf): {cites}/{len(bs)} ({100*cites//max(1,len(bs))}%)")
    print(f"  weekly_slope >= 0 : {wk_pos}/{len(bs)}   |   cascade >= -1 (raso): {casc_shallow}/{len(bs)}")
    # mislabels pelo critério-semente
    if cls=='LEGITIMATE_BEAR_BUY':
        mis=[r for r in rows if (r[2] is not None and r[2]<0) and (r[3] is not None and r[3]<=-2)]
        print(f"  >> rotulados LEGIT mas weekly<0 E cascade<=-2 (deveriam ser TRAP p/ critério): {len(mis)}/{len(bs)}")
    else:
        mis=[r for r in rows if (r[2] is not None and r[2]>=0) and (r[3] is not None and r[3]>=-1)]
        print(f"  >> rotulados TRAP mas weekly>=0 E cascade>=-1 (deveriam ser LEGIT p/ critério): {len(mis)}/{len(bs)}")
    print(f"  {'bar':>5} {'date':10} {'weekly':>7} {'casc':>5} {'mfeR':>6} {'dec':6} cites")
    for r in sorted(rows,key=lambda x:(x[2] if x[2] is not None else 9)):
        flag=' <<MIS' if r in mis else ''
        print(f"  {r[0]:>5} {r[1]:10} {str(r[2]):>7} {str(r[3]):>5} {r[4]:>6} {r[5]:6} {'Y' if r[6] else '.'}{flag}")
print("\nDIAGNÓSTICO de consistência. Critério-semente: LEGIT=mergulho em bear c/ weekly ainda de pé (weekly>=0 ou cascade raso);")
print("TRAP=mesma superfície c/ weekly quebrado (weekly<0 E cascade profundo). Mislabel alto = bloco leu superfície, não o eixo.")
