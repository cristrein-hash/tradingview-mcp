import json
from bisect import bisect_right
geom={'E%d'%o['episode_id']:o for o in json.load(open('/tmp/plot_geometry.json'))}
frozen=[json.loads(l) for l in open('/tmp/raw_features_2020_2026.jsonl')]
N=len(frozen);V=[r.get('volume') or 0 for r in frozen]
d1=[json.loads(l) for l in open('/tmp/XAU_1D_ohlc.jsonl')]; d1.sort(key=lambda b:b['time'])
T=[b['time'] for b in d1];Hh=[b['high'] for b in d1];Ll=[b['low'] for b in d1];Cc=[b['close'] for b in d1];n=len(d1)
def volclmx(i):
    a=sum(V[i-50:i])/50 if i>=50 and sum(V[i-50:i])>0 else None
    return max(V[i-9:i+1])/a if a else None
k=5; ph=[False]*n; pl=[False]*n
for j in range(k,n-k):
    if Hh[j]>max(Hh[j-k:j]) and Hh[j]>max(Hh[j+1:j+k+1]): ph[j]=True
    if Ll[j]<min(Ll[j-k:j]) and Ll[j]<min(Ll[j+1:j+k+1]): pl[j]=True
state=['bull']*n; cur='bull';lsh=None;lsl=None
for t in range(n):
    j=t-k
    if j>=0:
        if ph[j]: lsh=Hh[j]
        if pl[j]: lsl=Ll[j]
    if cur=='bull' and lsl is not None and Cc[t]<lsl: cur='bear'
    elif cur=='bear' and lsh is not None and Cc[t]>lsh: cur='bull'
    state[t]=cur
def d1bear(ts):
    j=bisect_right(T,ts)-1
    while j>=0 and T[j]>=ts: j-=1
    return j>=0 and state[j]=='bear'
WIN={'E1','E13','E17','E27','E30','E40','E21','E23','E5'}; BLOCK_TARGET={'E33','E6','E7','E36','E9','E8','E37','E11'}
for THR in [1.55,1.6,1.65]:
    def blocked(ep):
        i=geom[ep]['bar_idx']; vc=volclmx(i)
        return d1bear(geom[ep]['time']) and vc is not None and vc>=THR
    wb=[e for e in WIN if blocked(e)]; tb=[e for e in BLOCK_TARGET if blocked(e)]
    print(f"THR={THR}: recall_winners_blocked={sorted(wb,key=lambda e:int(e[1:])) or 'NONE 9/9✓'}  blocks {len(tb)}/8 {sorted(tb,key=lambda e:int(e[1:]))}  E10={'BLOCK' if blocked('E10') else 'ok'} E12={'block' if blocked('E12') else 'pass'}")
