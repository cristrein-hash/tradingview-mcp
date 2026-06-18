import json,csv
from bisect import bisect_right
from datetime import datetime,timezone
D="results"
geom={'E%d'%o['episode_id']:o for o in json.load(open('/tmp/plot_geometry.json'))}
d1=[json.loads(l) for l in open('/tmp/XAU_1D_ohlc.jsonl')]; d1.sort(key=lambda b:b['time'])
T=[b['time'] for b in d1]; Hh=[b['high'] for b in d1]; Ll=[b['low'] for b in d1]; Cc=[b['close'] for b in d1]
n=len(d1)
def fmt(t): return datetime.fromtimestamp(t,tz=timezone.utc).strftime('%Y-%m-%d')
def run_state(k):
    ph=[False]*n; pl=[False]*n
    for j in range(k,n-k):
        if Hh[j]>max(Hh[j-k:j]) and Hh[j]>max(Hh[j+1:j+k+1]): ph[j]=True
        if Ll[j]<min(Ll[j-k:j]) and Ll[j]<min(Ll[j+1:j+k+1]): pl[j]=True
    # causal state machine: pivot confirmed at j+k
    state=['neutral']*n
    cur='bull'; last_sh=None; last_sl=None
    confH=[]; confL=[]
    for t in range(n):
        # confirm pivots whose j = t-k
        j=t-k
        if j>=0:
            if ph[j]: confH.append((j,Hh[j])); last_sh=Hh[j]
            if pl[j]: confL.append((j,Ll[j])); last_sl=Ll[j]
        # transitions on close (use last confirmed swing levels)
        if cur=='bull' and last_sl is not None and Cc[t]<last_sl: cur='bear'
        elif cur=='bear' and last_sh is not None and Cc[t]>last_sh: cur='bull'
        state[t]=cur
    return state
WIN={'E1','E13','E17','E27','E30','E40','E21','E23','E5'}
BLOCK_TARGET={'E33','E6','E7','E36','E9','E8','E37','E11'}
EXCEPT={'E10'}; BORDER={'E12'}
def d1state_at(ts,state,k):
    j=bisect_right(T,ts)-1  # last daily bar; but bar j is "closed" only after its session; causal: use j-? assume daily close known if bar time<ts
    # ensure causal: only bars fully before ts
    while j>=0 and T[j]>=ts: j-=1
    return state[j] if j>=0 else 'neutral'
for k in [3,5,7]:
    st=run_state(k)
    res={ep:d1state_at(geom[ep]['time'],st,k) for ep in geom}
    win_blocked=[e for e in WIN if res[e]=='bear']
    tgt_blocked=[e for e in BLOCK_TARGET if res[e]=='bear']
    print(f"\n=== 1D pivot k={k} ===")
    print(f"  RECALL: winners in BEAR (must be 0): {sorted(win_blocked,key=lambda e:int(e[1:])) or 'NONE 9/9 OK'}")
    print(f"  BLOCK target in BEAR: {len(tgt_blocked)}/8 -> {sorted(tgt_blocked,key=lambda e:int(e[1:]))}")
    print(f"  E10 (must be BULL): {res['E10']}  | E12: {res['E12']}")
