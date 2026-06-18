import json,csv,statistics
from bisect import bisect_right
frozen=[json.loads(l) for l in open('/tmp/raw_features_2020_2026.jsonl')]
N=len(frozen);H=[r['high'] for r in frozen];L=[r['low'] for r in frozen];C=[r['close'] for r in frozen];TS=[r['ts_epoch'] for r in frozen]
ATR=[None]*N;trs=[]
for i in range(1,N):
    trs.append(max(H[i]-L[i],abs(H[i]-C[i-1]),abs(L[i]-C[i-1])))
    if i>=14: ATR[i]=sum(trs[i-14:i])/14
d1=[json.loads(l) for l in open('/tmp/XAU_1D_ohlc.jsonl')]; d1.sort(key=lambda b:b['time'])
T=[b['time'] for b in d1];dc=[b['close'] for b in d1]
def legpos(i):
    j=bisect_right(T,TS[i])-1
    if j<60: return None
    lo=min(dc[j-59:j+1]); hi=max(dc[j-59:j+1]); return 100*(C[i]-lo)/(hi-lo) if hi>lo else None
KP=5; plf=[False]*N
for j in range(KP,N-KP):
    if L[j]<min(L[j-KP:j]) and L[j]<min(L[j+1:j+KP+1]): plf[j]=True
def risk_of(i):
    p=C[i];atr=ATR[i]
    if not atr: return None
    cands=[L[j] for j in range(KP,i-KP+1) if plf[j] and L[j]<p]
    lo=cands[-1] if cands else min(L[max(0,i-6):i+1]); return max(p-(lo-0.1*atr),0.3*atr)
MAXHOLD=60;tR=3.0;COST=0.10
def sim(i):
    risk=risk_of(i)
    if risk is None: return None
    p=C[i];tgt=p+tR*risk;end=min(i+MAXHOLD,N-1)
    for j in range(i+1,end+1):
        if L[j]<=p-risk: return -1.0-COST
        if H[j]>=tgt: return tR-COST
    return (C[end]-p)/risk-COST
# L2/BPT episodes
base=sorted(int(r['candidate_id'][1:]) for r in csv.DictReader(open("results/l2_bpt_v2_2_pruned_base_v2.csv")))
matrix={int(r['candidate_id'][1:]):r for r in csv.DictReader(open("results/l2_bpt_v2_2_candidate_matrix.csv"))}
eps=[];cur=[base[0]]
for a,b in zip(base,base[1:]):
    if b-a<=6: cur.append(b)
    else: eps.append(cur);cur=[b]
eps.append(cur)
l2_idx=[e[0] for e in eps]
def stats(idxs):
    rs=[sim(i) for i in idxs]; rs=[r for r in rs if r is not None]
    return len(rs),100*sum(1 for x in rs if x>0)/len(rs),sum(rs)/len(rs),sum(rs)
def inbucket(i,lo,hi): lp=legpos(i); return lp is not None and lo<=lp<hi
print("=== ATRIBUIÇÃO: L2/BPT vs LONG ALEATÓRIO (mesma mecânica, custo) ===")
for lo,hi in [(0,101),(75,101),(55,75),(30,55)]:
    l2=[i for i in l2_idx if inbucket(i,lo,hi)]
    rnd=[i for i in range(2*14,N-MAXHOLD,3) if inbucket(i,lo,hi)]
    n1,w1,a1,s1=stats(l2); n2,w2,a2,s2=stats(rnd)
    tag='TODOS' if (lo,hi)==(0,101) else f'legpos[{lo},{hi})'
    print(f"  {tag:<16} L2/BPT: n={n1:<4} WR={w1:.0f}% avgR={a1:+.2f}   | RANDOM-long: n={n2:<5} WR={w2:.0f}% avgR={a2:+.2f}   | delta avgR={a1-a2:+.2f}")
