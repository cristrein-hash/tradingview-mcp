import json,csv,statistics
from bisect import bisect_right
D="results"
frozen=[json.loads(l) for l in open('/tmp/raw_features_2020_2026.jsonl')]
N=len(frozen);H=[r['high'] for r in frozen];L=[r['low'] for r in frozen];C=[r['close'] for r in frozen];RS=[r.get('rsi') for r in frozen]
TS=[r['ts_epoch'] for r in frozen]
geom={'E%d'%o['episode_id']:o for o in json.load(open('/tmp/plot_geometry.json'))}
matrix={int(r['candidate_id'][1:]):r for r in csv.DictReader(open(f"{D}/l2_bpt_v2_2_candidate_matrix.csv"))}
d1=[json.loads(l) for l in open('/tmp/XAU_1D_bars.jsonl')]; d1.sort(key=lambda b:b['time'])
dt=[b['time'] for b in d1]; dc=[b['close'] for b in d1]
from datetime import datetime,timezone
def fmt(t): return datetime.fromtimestamp(t,tz=timezone.utc).strftime('%Y-%m-%d')
def legpos_at(ts,p):
    j=bisect_right(dt,ts)-1
    if j<60: return None,None
    lo=min(dc[j-59:j+1]); hi=max(dc[j-59:j+1])
    return (round(100*(p-lo)/(hi-lo),1) if hi>lo else None, round(100*(p-lo)/lo,2))
def rsi_bear_div(i,look=12):
    seg=[(j,H[j],RS[j]) for j in range(max(0,i-look),i+1) if RS[j] is not None]
    if len(seg)<6: return 0
    mid=len(seg)//2; pr=max(seg[:mid],key=lambda x:x[1]); rc=max(seg[mid:],key=lambda x:x[1])
    return 1 if (rc[1]>pr[1] and rc[2]<pr[2]) else 0
# ---- MACRO TOP detector (causal): high legpos + exhaustion ----
def is_macro_top(i):
    lp,ext=legpos_at(TS[i],C[i])
    if lp is None or lp<85: return False
    return (RS[i] is not None and RS[i]>=68) or rsi_bear_div(i)==1 or (ext is not None and ext>=15)
tops=[i for i in range(80,N) if is_macro_top(i)]
# collapse consecutive tops into events, top_high = max high in +-3 bars
events=[]
for i in tops:
    if events and i-events[-1][0]<=5: continue
    th=max(H[max(0,i-3):i+4]); events.append((i,th))
# ---- BEAR-STATE windows: from a top until close reclaims above top_high ----
windows=[]
for (i,th) in events:
    end=N-1
    for k in range(i+1,N):
        if C[k]>th: end=k; break
    windows.append((TS[i],TS[end],th))
def in_bear_state(ts):
    return any(a<ts<b for (a,b,th) in windows)
# ---- evaluate episodes ----
BLOCK_TARGET={'E33','E6','E7','E36','E9','E8','E37','E11'}
EXCEPT={'E10'}; BORDER={'E12'}
WIN={'E1','E13','E17','E27','E30','E40','E21','E23','E5'}
rows=[]
for ep in sorted(geom,key=lambda e:int(e[1:])):
    o=geom[ep]; ts=o['time']; blocked=in_bear_state(ts)
    rows.append((ep,blocked,fmt(ts)))
print(f"macro-top events detected: {len(events)} | bear-state windows: {len(windows)}")
print("E24 fired as a top?", any(abs(TS[i]-geom['E24']['time'])<6*3600 for (i,th) in events))
print("\n=== block result vs Cris's target ===")
blocked_eps={ep for ep,b,_ in rows if b}
tb=BLOCK_TARGET & blocked_eps
print(f"BLOCK target (8): blocked {len(tb)}/8 -> {sorted(tb, key=lambda e:int(e[1:]))}")
print(f"  missed: {sorted(BLOCK_TARGET-blocked_eps,key=lambda e:int(e[1:]))}")
print(f"E10 (must NOT block): {'BLOCKED (bad)' if 'E10' in blocked_eps else 'passed OK'}")
print(f"E12 (ideally block): {'blocked' if 'E12' in blocked_eps else 'passed'}")
wb=WIN & blocked_eps
print(f"\nRECALL-GATE — winners blocked (must be 0): {sorted(wb,key=lambda e:int(e[1:])) or 'NONE — 9/9 preserved'}")
print("\n=== per-episode (Cris-target groups) ===")
for ep,b,d in rows:
    tag='BLOCK_TGT' if ep in BLOCK_TARGET else ('EXCEPT' if ep in EXCEPT else ('BORDER' if ep in BORDER else ('WIN' if ep in WIN else '')))
    if tag: print(f"  {ep:<4} {d}  blocked={int(b)}  [{tag}]")
