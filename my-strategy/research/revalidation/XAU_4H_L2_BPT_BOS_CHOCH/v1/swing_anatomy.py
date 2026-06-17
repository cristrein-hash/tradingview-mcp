import json,csv,statistics
from collections import Counter,defaultdict
D="results"
frozen=[json.loads(l) for l in open('/tmp/raw_features_2020_2026.jsonl')]
N=len(frozen);H=[r['high'] for r in frozen];L=[r['low'] for r in frozen];C=[r['close'] for r in frozen];O=[r['open'] for r in frozen]
ATR=[None]*N;trs=[]
for i in range(1,N):
    trs.append(max(H[i]-L[i],abs(H[i]-C[i-1]),abs(L[i]-C[i-1])))
    if i>=14: ATR[i]=sum(trs[i-14:i])/14
K=5
ph=[False]*N; pl=[False]*N
for j in range(K,N-K):
    if H[j]>max(H[j-K:j]) and H[j]>max(H[j+1:j+K+1]): ph[j]=True
    if L[j]<min(L[j-K:j]) and L[j]<min(L[j+1:j+K+1]): pl[j]=True
geom={'E%d'%o['episode_id']:o for o in json.load(open('/tmp/plot_geometry.json'))}
matrix={int(r['candidate_id'][1:]):r for r in csv.DictReader(open(f"{D}/l2_bpt_v2_2_candidate_matrix.csv"))}
rev={r['episode_id']:r for r in csv.DictReader(open(f"{D}/l2_bpt_full_res_visual_episode_review.csv"))}

# Cris label groups
WIN={'E1','E13','E17','E27','E30','E40','E21','E23','E5'}
SLFIX={'E2','E3','E4','E19','E20','E22','E28','E29','E31','E32','E38','E41'}
TRAP={'E15','E24','E34','E39','E36','E6','E7','E8','E9','E10','E37','E11'}
PREM={'E25','E26','E35'}
def grp(ep): return 'WIN' if ep in WIN else ('SLFIX' if ep in SLFIX else ('TRAP' if ep in TRAP else ('PREM' if ep in PREM else 'REVIEW')))

def conf_pivots(i):
    # pivots confirmed by bar i (j<=i-5)
    lows=[(j,L[j]) for j in range(K,i-K+1) if pl[j]]
    highs=[(j,H[j]) for j in range(K,i-K+1) if ph[j]]
    return lows,highs

rows=[]
for ep in sorted(geom,key=lambda e:int(e[1:])):
    o=geom[ep]; i=o['bar_idx']; p=C[i]; atr=ATR[i]; pol=float(matrix[i]['level'])
    lows,highs=conf_pivots(i)
    # last 3 lows / highs
    L3=lows[-3:]; Hh=highs[-3:]
    pl1=L3[-1][1] if len(L3)>=1 else None; pl2=L3[-2][1] if len(L3)>=2 else None; pl3=L3[-3][1] if len(L3)>=3 else None
    ph1=Hh[-1][1] if len(Hh)>=1 else None; ph2=Hh[-2][1] if len(Hh)>=2 else None
    low_seq = 'HL' if (pl1 and pl2 and pl1>pl2) else ('LL' if (pl1 and pl2 and pl1<pl2) else '?')
    low_seq2 = 'HL' if (pl2 and pl3 and pl2>pl3) else ('LL' if (pl2 and pl3 and pl2<pl3) else '?')
    high_seq = 'HH' if (ph1 and ph2 and ph1>ph2) else ('LH' if (ph1 and ph2 and ph1<ph2) else '?')
    # is polarity (reclaimed high) a lower-high vs the prior pivot high?
    pol_is_LH = (ph2 is not None and pol < ph2*1.001)  # polarity below an earlier high
    # SWEEP: in last 15 bars before i, a bar that took out the prior pivot low (pl2) by low but closed above it
    sweep=False; swept_level=pl2
    if pl2 is not None:
        for j in range(max(0,i-15),i+1):
            if L[j] < pl2 and C[j] > pl2: sweep=True; break
    # BOS-down recent: a recent CLOSE below the prior pivot low (clean break = bear leg)
    bos_down=False
    if pl2 is not None:
        for j in range(max(0,i-15),i+1):
            if C[j] < pl2: bos_down=True; break
    # most recent confirmed pivot low BELOW entry = structural SL origin
    below=[lv for (jj,lv) in lows if lv<p]
    sl_origin = max(below) if below else (pl1 if pl1 else None)
    sl_dist = round((p-sl_origin)/atr,2) if (sl_origin and atr) else None
    # leg direction into entry (10-bar)
    leg = round((C[i]-C[max(0,i-10)])/atr,2) if atr else None
    # close vs 20-bar slope (macro down?)
    slope20 = round((C[i]-C[max(0,i-20)])/atr,2) if atr else None
    rows.append({'episode_id':ep,'group':grp(ep),'timestamp':o['time_iso'],
      'low_seq(recent)':low_seq,'low_seq(prior)':low_seq2,'high_seq':high_seq,'polarity_is_LH':int(pol_is_LH),
      'sweep':int(sweep),'bos_down_recent':int(bos_down),'sl_origin_dist_atr':sl_dist,
      'leg10_atr':leg,'slope20_atr':slope20,
      'annot':rev.get(ep,{}).get('user_annotation','')[:42]})

with open(f"{D}/l2_bpt_swing_anatomy.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)

def show(g):
    sub=[r for r in rows if r['group']==g]
    def frac(key,val): return f"{sum(1 for r in sub if str(r[key])==str(val))}/{len(sub)}"
    def med(key):
        v=[r[key] for r in sub if isinstance(r[key],(int,float))]; return round(statistics.median(v),2) if v else None
    print(f"\n=== {g} (n={len(sub)}) ===")
    print(f"  low_seq recent: HL {frac('low_seq(recent)','HL')}  LL {frac('low_seq(recent)','LL')}")
    print(f"  high_seq: HH {frac('high_seq','HH')}  LH {frac('high_seq','LH')}")
    print(f"  polarity_is_LH: {frac('polarity_is_LH',1)} | sweep: {frac('sweep',1)} | bos_down_recent: {frac('bos_down_recent',1)}")
    print(f"  median sl_origin_dist_atr: {med('sl_origin_dist_atr')} | leg10: {med('leg10_atr')} | slope20: {med('slope20_atr')}")
for g in ['WIN','SLFIX','TRAP','PREM','REVIEW']: show(g)
print("\n=== per-episode (key cols) ===")
for r in rows:
    print(f"  {r['episode_id']:<4}{r['group']:<7} low:{r['low_seq(recent)']:<3} high:{r['high_seq']:<3} polLH:{r['polarity_is_LH']} sweep:{r['sweep']} bosD:{r['bos_down_recent']} slDist:{str(r['sl_origin_dist_atr']):<5} slope20:{str(r['slope20_atr']):<6} | {r['annot']}")
