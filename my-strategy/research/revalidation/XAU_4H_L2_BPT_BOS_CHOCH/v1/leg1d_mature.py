import json
from bisect import bisect_right
from datetime import datetime,timezone
geom={'E%d'%o['episode_id']:o for o in json.load(open('/tmp/plot_geometry.json'))}
d1=[json.loads(l) for l in open('/tmp/XAU_1D_ohlc.jsonl')]; d1.sort(key=lambda b:b['time'])
T=[b['time'] for b in d1]; Hh=[b['high'] for b in d1]; Ll=[b['low'] for b in d1]; Cc=[b['close'] for b in d1]; n=len(d1)
WIN={'E1','E13','E17','E27','E30','E40','E21','E23','E5'}
BLOCK_TARGET={'E33','E6','E7','E36','E9','E8','E37','E11'}
def fmt(t): return datetime.fromtimestamp(t,tz=timezone.utc).strftime('%Y-%m-%d')
def run(k):
    ph=[False]*n; pl=[False]*n
    for j in range(k,n-k):
        if Hh[j]>max(Hh[j-k:j]) and Hh[j]>max(Hh[j+1:j+k+1]): ph[j]=True
        if Ll[j]<min(Ll[j-k:j]) and Ll[j]<min(Ll[j+1:j+k+1]): pl[j]=True
    state=['neutral']*n; bear_age=[0]*n; lh_count=[0]*n
    cur='bull'; last_sh=None; last_sl=None; bear_start=None; lhc=0; prev_sh=None
    for t in range(n):
        j=t-k
        if j>=0:
            if ph[j]:
                if cur=='bear' and prev_sh is not None and Hh[j]<prev_sh: lhc+=1  # lower-high during bear = real down-leg
                prev_sh=Hh[j]; last_sh=Hh[j]
            if pl[j]: last_sl=Ll[j]
        if cur=='bull' and last_sl is not None and Cc[t]<last_sl: cur='bear'; bear_start=t; lhc=0
        elif cur=='bear' and last_sh is not None and Cc[t]>last_sh: cur='bull'; bear_start=None; lhc=0
        state[t]=cur; bear_age[t]=(t-bear_start) if (cur=='bear' and bear_start is not None) else 0; lh_count[t]=lhc
    return state,bear_age,lh_count
def at(ts,arr):
    j=bisect_right(T,ts)-1
    while j>=0 and T[j]>=ts: j-=1
    return arr[j] if j>=0 else (0 if isinstance(arr[0],int) else 'neutral')
for k in [3,5]:
  st,ba,lh=run(k)
  for MINAGE,MINLH in [(15,1),(20,1),(20,2),(30,2)]:
    def blocked(ep):
        ts=geom[ep]['time']; s=at(ts,st); age=at(ts,ba); l=at(ts,lh)
        return s=='bear' and age>=MINAGE and l>=MINLH
    wb=[e for e in WIN if blocked(e)]; tb=[e for e in BLOCK_TARGET if blocked(e)]
    print(f"k={k} MINAGE={MINAGE} MINLH={MINLH}: recall_winners_blocked={sorted(wb,key=lambda e:int(e[1:])) or 'NONE✓'}  blocks {len(tb)}/8 {sorted(tb,key=lambda e:int(e[1:]))}  E10={'BLOCK' if blocked('E10') else 'ok'} E12={'block' if blocked('E12') else 'pass'}")
