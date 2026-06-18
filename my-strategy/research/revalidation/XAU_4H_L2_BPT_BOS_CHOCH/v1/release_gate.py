import json
from bisect import bisect_right,bisect_left
geom={'E%d'%o['episode_id']:o for o in json.load(open('/tmp/plot_geometry.json'))}
d1=[json.loads(l) for l in open('/tmp/XAU_1D_ohlc.jsonl')]; d1.sort(key=lambda b:b['time'])
T=[b['time'] for b in d1]; Hh=[b['high'] for b in d1]; Ll=[b['low'] for b in d1]; Cc=[b['close'] for b in d1]; n=len(d1)
sig=json.load(open('/tmp/d1_signals_v2.json')); nasd={int(k):v for k,v in sig['nas_long_days'].items()}; buyt=sig['buy_times']
WIN={'E1','E13','E17','E27','E30','E40','E21','E23','E5'}; BLOCK_TARGET={'E33','E6','E7','E36','E9','E8','E37','E11'}
def run(k):
    ph=[False]*n; pl=[False]*n
    for j in range(k,n-k):
        if Hh[j]>max(Hh[j-k:j]) and Hh[j]>max(Hh[j+1:j+k+1]): ph[j]=True
        if Ll[j]<min(Ll[j-k:j]) and Ll[j]<min(Ll[j+1:j+k+1]): pl[j]=True
    state=['bull']*n; bear_start=[None]*n
    cur='bull'; lsh=None; lsl=None; bs=None
    for t in range(n):
        j=t-k
        if j>=0:
            if ph[j]: lsh=Hh[j]
            if pl[j]: lsl=Ll[j]
        if cur=='bull' and lsl is not None and Cc[t]<lsl: cur='bear'; bs=t
        elif cur=='bear' and lsh is not None and Cc[t]>lsh: cur='bull'; bs=None
        state[t]=cur; bear_start[t]=bs
    return state,bear_start
def buy_in(a,b):  # buy bubble time in [a,b]
    i=bisect_left(buyt,a); return i<len(buyt) and buyt[i]<=b
def nas_in(a,b):
    return any(nasd.get(t,0) for t in T if a<=t<=b)
for k in [3,5]:
  st,bstart=run(k)
  for WIN_DAYS in [10,20,30]:
    def blocked(ep):
        ts=geom[ep]['time']; j=bisect_right(T,ts)-1
        while j>=0 and T[j]>=ts: j-=1
        if j<0 or st[j]!='bear': return False  # not in bear leg -> allowed
        bs=bstart[j]; 
        if bs is None: return False
        a=T[bs]; b=ts
        # release if a 1D bottom-confirmation (NAS LONG new + BUY bubble) appeared since bear start
        win=WIN_DAYS*86400
        released = any((nasd.get(T[x],0) and buy_in(T[x]-win,T[x]+win)) for x in range(bs,j+1))
        return not released  # blocked if NOT released
    wb=[e for e in WIN if blocked(e)]; tb=[e for e in BLOCK_TARGET if blocked(e)]
    print(f"k={k} win±{WIN_DAYS}d: recall_winners_blocked={sorted(wb,key=lambda e:int(e[1:])) or 'NONE✓'}  blocks {len(tb)}/8 {sorted(tb,key=lambda e:int(e[1:]))}  E10={'BLOCK' if blocked('E10') else 'ok'} E12={'block' if blocked('E12') else 'pass'}")
