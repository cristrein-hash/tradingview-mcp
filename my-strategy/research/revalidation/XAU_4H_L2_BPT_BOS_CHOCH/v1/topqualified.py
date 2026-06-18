import json
from bisect import bisect_right
from datetime import datetime,timezone
geom={'E%d'%o['episode_id']:o for o in json.load(open('/tmp/plot_geometry.json'))}
frozen=[json.loads(l) for l in open('/tmp/raw_features_2020_2026.jsonl')]
N=len(frozen);H4=[r['high'] for r in frozen];C4=[r['close'] for r in frozen];RS4=[r.get('rsi') for r in frozen];TS4=[r['ts_epoch'] for r in frozen]
d1=[json.loads(l) for l in open('/tmp/XAU_1D_ohlc.jsonl')]; d1.sort(key=lambda b:b['time'])
T=[b['time'] for b in d1]; Hh=[b['high'] for b in d1]; Ll=[b['low'] for b in d1]; Cc=[b['close'] for b in d1]; n=len(d1)
dc=[b['close'] for b in d1]
def f(t): return datetime.fromtimestamp(t,tz=timezone.utc).strftime('%Y-%m-%d')
def legpos_ext(ts):
    i4=bisect_right(TS4,ts)-1; p=C4[i4]
    j=bisect_right(T,ts)-1
    if j<60: return None,None
    lo=min(dc[j-59:j+1]); hi=max(dc[j-59:j+1])
    return (round(100*(p-lo)/(hi-lo),1) if hi>lo else None, round(100*(p-lo)/lo,2))
def rsi_div4(i,look=12):
    seg=[(j,H4[j],RS4[j]) for j in range(max(0,i-look),i+1) if RS4[j] is not None]
    if len(seg)<6: return 0
    mid=len(seg)//2; pr=max(seg[:mid],key=lambda x:x[1]); rc=max(seg[mid:],key=lambda x:x[1])
    return 1 if (rc[1]>pr[1] and rc[2]<pr[2]) else 0
# macro exhaustion top on 4H: legpos>88 AND (rsi>=68 OR div OR ext>=15)
def is_top(ts):
    lp,ext=legpos_ext(ts)
    if lp is None or lp<88: return False
    i4=bisect_right(TS4,ts)-1
    return (RS4[i4] and RS4[i4]>=68) or rsi_div4(i4) or (ext and ext>=15)
# 1D state machine (k=5)
k=5; ph=[False]*n; pl=[False]*n
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
WIN={'E1','E13','E17','E27','E30','E40','E21','E23','E5'}; BLOCK_TARGET={'E33','E6','E7','E36','E9','E8','E37','E11'}
# bear leg qualified if an exhaustion top occurred in the LOOKBACK days before bear_start
for LB in [20,30,45]:
    def blocked(ep):
        ts=geom[ep]['time']; j=bisect_right(T,ts)-1
        while j>=0 and T[j]>=ts: j-=1
        if j<0 or state[j]!='bear': return False
        bs=bstart[j]
        if bs is None: return False
        # was there an exhaustion top in [bear_start - LB days, bear_start + a few]? scan 4H bars
        a=T[bs]-LB*86400; b=T[bs]+5*86400
        topped=any(is_top(TS4[x]) for x in range(N) if a<=TS4[x]<=b)
        return topped  # block only if bear leg born from exhaustion top
    wb=[e for e in WIN if blocked(e)]; tb=[e for e in BLOCK_TARGET if blocked(e)]
    print(f"LB={LB}d: recall_winners_blocked={sorted(wb,key=lambda e:int(e[1:])) or 'NONE✓'}  blocks {len(tb)}/8 {sorted(tb,key=lambda e:int(e[1:]))}  E10={'BLOCK' if blocked('E10') else 'ok'} E12={'block' if blocked('E12') else 'pass'}")
# debug: was there an exhaustion top before COVID bear (2020-03-12) vs Aug bear (2020-09-21)?
for d,lab in [('2020-03-12','COVID bear start'),('2020-09-21','Aug-corr bear start')]:
    ts0=int(datetime.strptime(d,'%Y-%m-%d').replace(tzinfo=timezone.utc).timestamp())
    tops=[f(TS4[x]) for x in range(N) if ts0-45*86400<=TS4[x]<=ts0+5*86400 and is_top(TS4[x])]
    print(f"  exhaustion tops in 45d before {lab}: {len(tops)} {tops[:5]}")
