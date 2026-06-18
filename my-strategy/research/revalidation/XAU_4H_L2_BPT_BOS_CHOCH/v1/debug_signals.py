import json
from bisect import bisect_right,bisect_left
from datetime import datetime,timezone
geom={'E%d'%o['episode_id']:o for o in json.load(open('/tmp/plot_geometry.json'))}
d1=[json.loads(l) for l in open('/tmp/XAU_1D_ohlc.jsonl')]; d1.sort(key=lambda b:b['time'])
T=[b['time'] for b in d1]; Hh=[b['high'] for b in d1]; Ll=[b['low'] for b in d1]; Cc=[b['close'] for b in d1]; n=len(d1)
sig=json.load(open('/tmp/d1_signals_v2.json')); nasd={int(k):v for k,v in sig['nas_long_days'].items()}; buyt=sig['buy_times']
def f(t): return datetime.fromtimestamp(t,tz=timezone.utc).strftime('%Y-%m-%d')
k=5
ph=[False]*n; pl=[False]*n
for j in range(k,n-k):
    if Hh[j]>max(Hh[j-k:j]) and Hh[j]>max(Hh[j+1:j+k+1]): ph[j]=True
    if Ll[j]<min(Ll[j-k:j]) and Ll[j]<min(Ll[j+1:j+k+1]): pl[j]=True
state=['bull']*n; bstart=[None]*n; cur='bull'; lsh=None;lsl=None;bs=None
for t in range(n):
    j=t-k
    if j>=0:
        if ph[j]: lsh=Hh[j]
        if pl[j]: lsl=Ll[j]
    if cur=='bull' and lsl is not None and Cc[t]<lsl: cur='bear'; bs=t
    elif cur=='bear' and lsh is not None and Cc[t]>lsh: cur='bull'; bs=None
    state[t]=cur; bstart[t]=bs
for ep in ['E1','E17','E6','E7','E11','E10','E27','E30','E40']:
    ts=geom[ep]['time']; j=bisect_right(T,ts)-1
    while j>=0 and T[j]>=ts: j-=1
    s=state[j]; bs=bstart[j]
    nl_days=[f(T[x]) for x in range(bs if bs else j,j+1) if nasd.get(T[x],0)] if bs else []
    # buy bubbles in bear window
    bb=[f(t) for t in buyt if (bs and T[bs]<=t<=ts)]
    print(f"{ep:<4} entry {f(ts)}  1Dstate={s:<5} bear_start={f(T[bs]) if bs else '-'}  NAS_LONG_days_in_bear={nl_days}  BUY_bub_in_bear={len(bb)} {bb[:4]}")
