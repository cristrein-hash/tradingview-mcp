import json,csv
from bisect import bisect_right
from datetime import datetime,timezone
D="results"
frozen=[json.loads(l) for l in open('/tmp/raw_features_2020_2026.jsonl')]
N=len(frozen);H=[r['high'] for r in frozen];L=[r['low'] for r in frozen];C=[r['close'] for r in frozen];RS=[r.get('rsi') for r in frozen];TS=[r['ts_epoch'] for r in frozen]
geom={'E%d'%o['episode_id']:o for o in json.load(open('/tmp/plot_geometry.json'))}
d1=[json.loads(l) for l in open('/tmp/XAU_1D_bars.jsonl')]; d1.sort(key=lambda b:b['time'])
dt=[b['time'] for b in d1]; dc=[b['close'] for b in d1]
def fmt(t): return datetime.fromtimestamp(t,tz=timezone.utc).strftime('%Y-%m-%d')
def sma(i,p): return sum(dc[i-p+1:i+1])/p if i>=p-1 else None
def rsi_bear_div(i,look=12):
    seg=[(j,H[j],RS[j]) for j in range(max(0,i-look),i+1) if RS[j] is not None]
    if len(seg)<6: return 0
    mid=len(seg)//2; pr=max(seg[:mid],key=lambda x:x[1]); rc=max(seg[mid:],key=lambda x:x[1])
    return 1 if (rc[1]>pr[1] and rc[2]<pr[2]) else 0
def legpos_ext(ts,p):
    j=bisect_right(dt,ts)-1
    if j<60: return None,None
    lo=min(dc[j-59:j+1]); hi=max(dc[j-59:j+1])
    return (round(100*(p-lo)/(hi-lo),1) if hi>lo else None, round(100*(p-lo)/lo,2))
# STRICT macro top: legpos>90 AND (rsi_bear_div OR ext>=18 OR rsi>=72)
def strict_top(i):
    lp,ext=legpos_ext(TS[i],C[i])
    if lp is None or lp<90: return False
    return rsi_bear_div(i)==1 or (ext and ext>=18) or (RS[i] and RS[i]>=72)
tops=[]
for i in range(80,N):
    if strict_top(i):
        if tops and i-tops[-1]<=10: continue
        tops.append(i)
# 1D-anchored bear window: from top until 1D close > top-level (the top's 4H high)
def d1_idx(ts): return bisect_right(dt,ts)-1
windows=[]
for i in tops:
    th=max(H[max(0,i-3):i+4])
    end=N-1
    for k in range(i+1,N):
        if C[k]>th: end=k; break
    windows.append((TS[i],TS[end],fmt(TS[i]),fmt(TS[end])))
def blocked(ts): return any(a<ts<b for (a,b,_,_) in windows)
BLOCK_TARGET={'E33','E6','E7','E36','E9','E8','E37','E11'}
WIN={'E1','E13','E17','E27','E30','E40','E21','E23','E5'}
print(f"STRICT tops: {len(tops)} | windows: {len(windows)}")
print("tops (date):",[fmt(TS[i]) for i in tops][:30])
print("E24 still a top?", any(abs(TS[i]-geom['E24']['time'])<6*3600 for i in tops))
bl={ep for ep in geom if blocked(geom[ep]['time'])}
print(f"\nBLOCK target: {len(BLOCK_TARGET&bl)}/8 -> {sorted(BLOCK_TARGET&bl,key=lambda e:int(e[1:]))}")
print(f"  missed: {sorted(BLOCK_TARGET-bl,key=lambda e:int(e[1:]))}")
print(f"E10 (don't block): {'BLOCKED' if 'E10' in bl else 'passed'}")
print(f"RECALL winners blocked (must be 0): {sorted(WIN&bl,key=lambda e:int(e[1:])) or 'NONE 9/9 OK'}")
