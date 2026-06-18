#!/usr/bin/env python3
"""L2/BPT entry/exhaustion case study — features causais (<=entrada) should-cut vs must-preserve.
No SLIM, no tick-volume authority, no outcome-proxy, no future."""
import json, csv
from datetime import datetime, timezone
fr=[json.loads(l) for l in open('/tmp/raw_features_2020_2026.jsonl')]
N=len(fr);H=[r['high'] for r in fr];L=[r['low'] for r in fr];C=[r['close'] for r in fr];TS=[r['ts_epoch'] for r in fr];RS=[r.get('rsi') for r in fr]
ATR=[None]*N;trs=[]
for i in range(1,N):
    trs.append(max(H[i]-L[i],abs(H[i]-C[i-1]),abs(L[i]-C[i-1])))
    if i>=14: ATR[i]=sum(trs[i-14:i])/14
ts2idx={t:i for i,t in enumerate(TS)}
def parse(t): return int(datetime.strptime(t,"%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc).timestamp())
swing={r['episode_id']:r for r in csv.DictReader(open('results/l2_bpt_swing_anatomy.csv'))}
lab={r['episode_id']:r for r in csv.DictReader(open('results/l2_bpt_visual_episode_labels.csv'))}
CUT=['E23','E15','E24','E34','E39'];KEEP=['E1','E5','E13','E17','E21','E27','E30','E40']
def feat(i):
    p=C[i];atr=ATR[i]
    hi90=max(H[max(0,i-90):i+1]);lo90=min(L[max(0,i-90):i+1])
    legpos=100*(p-lo90)/(hi90-lo90) if hi90>lo90 else 50
    return dict(
        legpos=round(legpos),
        distHi=round((hi90-p)/atr,1),         # ATR ate o high de 90d (pequeno=topo)
        extLo20=round((p-min(L[max(0,i-20):i+1]))/atr,1),  # extensao acima do low 20b
        rsi=RS[i],
        accel3=round((p-C[i-3])/atr,1),       # aceleracao vertical 3 bars
        dir20=round((p-C[max(0,i-20)])/atr,1),# direcao recente (>0 subindo into = topo; <0 caindo = reversal)
    )
rows=[]
hdr=f"{'eid':<5}{'set':<6}{'legpos':<7}{'distHi':<7}{'extLo20':<8}{'rsi':<6}{'accel3':<7}{'dir20':<7}{'slope20':<9}{'bearleg':<8}{'reclaim':<13}"
print(hdr)
for grp,eids in [('CUT',CUT),('KEEP',KEEP)]:
    for eid in eids:
        if eid not in swing: continue
        i=ts2idx[parse(swing[eid]['timestamp'])];f=feat(i)
        sl=swing[eid].get('slope20_atr','');bl=lab.get(eid,{}).get('bear_leg_context','');rc=lab.get(eid,{}).get('reclaim_candle','')
        print(f"{eid:<5}{grp:<6}{f['legpos']:<7}{f['distHi']:<7}{f['extLo20']:<8}{str(f['rsi']):<6}{f['accel3']:<7}{f['dir20']:<7}{str(sl):<9}{bl:<8}{str(rc)[:12]:<13}")
        rows.append({'eid':eid,'set':grp,**f,'slope20':sl,'bearleg':bl,'reclaim':rc})
with open('results/l2_bpt_entry_exhaustion_case_study.csv','w',newline='') as fo:
    w=csv.DictWriter(fo,fieldnames=list(rows[0].keys()));w.writeheader();w.writerows(rows)
print("\nWROTE results/l2_bpt_entry_exhaustion_case_study.csv")
