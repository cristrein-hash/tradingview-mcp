import json,csv,statistics
from bisect import bisect_right
D="results"
frozen=[json.loads(l) for l in open('/tmp/raw_features_2020_2026.jsonl')]
N=len(frozen);H=[r['high'] for r in frozen];L=[r['low'] for r in frozen];C=[r['close'] for r in frozen]
ATR=[None]*N;trs=[]
for i in range(1,N):
    trs.append(max(H[i]-L[i],abs(H[i]-C[i-1]),abs(L[i]-C[i-1])))
    if i>=14: ATR[i]=sum(trs[i-14:i])/14
TS=[r['ts_epoch'] for r in frozen]
svp={r['time']:r for r in (json.loads(l) for l in open('/tmp/svp_bars.jsonl'))}
svpT=sorted(svp)
geom={'E%d'%o['episode_id']:o for o in json.load(open('/tmp/plot_geometry.json'))}
matrix={int(r['candidate_id'][1:]):r for r in csv.DictReader(open(f"{D}/l2_bpt_v2_2_candidate_matrix.csv"))}
qual={r['candidate_id']:r for r in csv.DictReader(open(f"{D}/l2_bpt_v2_2_pruned_base_v2_demand_supply_quality.csv"))}
# 1D bear state
d1=[json.loads(l) for l in open('/tmp/XAU_1D_ohlc.jsonl')]; d1.sort(key=lambda b:b['time'])
T1=[b['time'] for b in d1];Hh=[b['high'] for b in d1];Ll=[b['low'] for b in d1];Cc=[b['close'] for b in d1];n1=len(d1)
k=5;ph=[False]*n1;pl=[False]*n1
for j in range(k,n1-k):
    if Hh[j]>max(Hh[j-k:j]) and Hh[j]>max(Hh[j+1:j+k+1]):ph[j]=True
    if Ll[j]<min(Ll[j-k:j]) and Ll[j]<min(Ll[j+1:j+k+1]):pl[j]=True
state=['bull']*n1;cur='bull';lsh=None;lsl=None
for t in range(n1):
    j=t-k
    if j>=0:
        if ph[j]:lsh=Hh[j]
        if pl[j]:lsl=Ll[j]
    if cur=='bull' and lsl is not None and Cc[t]<lsl:cur='bear'
    elif cur=='bear' and lsh is not None and Cc[t]>lsh:cur='bull'
    state[t]=cur
def d1bear(ts):
    j=bisect_right(T1,ts)-1
    while j>=0 and T1[j]>=ts:j-=1
    return j>=0 and state[j]=='bear'
def svp_at(ts):
    j=bisect_right(svpT,ts)-1
    return svp.get(svpT[j]) if j>=0 else None
def real_volclmx(i):
    # real volume from svp bars
    vols=[]
    for x in range(max(0,i-50),i+1):
        b=svp.get(TS[x]); vols.append(b.get('vol') or 0 if b else 0)
    if len(vols)<51 or sum(vols[:-10])<=0: return None
    a=sum(vols[:-10])/(len(vols)-10)
    return round(max(vols[-10:])/a,2) if a else None
def rsi_bull_div(i,look=18):
    # two most recent local price lows; bullish div = later low lower in price, higher in RSI
    rs=[]
    for x in range(max(0,i-look),i+1):
        b=svp.get(TS[x]); r=b.get('rsi') if b else None
        rs.append((x,L[x],r))
    lows=[(x,lo,r) for (x,lo,r) in rs if r is not None]
    if len(lows)<8: return 0
    # find 2 minima halves
    h=len(lows)//2; p1=min(lows[:h],key=lambda z:z[1]); p2=min(lows[h:],key=lambda z:z[1])
    return 1 if (p2[1]<p1[1] and p2[2]>p1[2]) else 0
WIN={'E1','E13','E17','E27','E30','E40','E21','E23','E5'}
rows=[]
for ep in sorted(geom,key=lambda e:int(e[1:])):
    o=geom[ep];i=o['bar_idx'];ts=o['time'];p=C[i];atr=ATR[i];q=qual.get(o['candidate_id'],{})
    vp=svp_at(ts); poc=vah=val=None
    if vp and vp.get('vp'): poc,vah,val=vp['vp']
    dist_val=round((p-val)/atr,2) if (val and atr) else None      # entry above VAL (support) by ATR
    dist_vah=round((vah-p)/atr,2) if (vah and atr) else None      # VAH above entry (resistance)
    inside_va=int(val<=p<=vah) if (val and vah) else None
    above_vah=int(p>vah) if vah else None                         # extended above value area
    rows.append({'episode_id':ep,'is_win':int(ep in WIN),'d1_bear':int(d1bear(ts)),
      'real_volclmx':real_volclmx(i),'rsi_bull_div':rsi_bull_div(i),
      'dist_above_VAL_atr':dist_val,'dist_below_VAH_atr':dist_vah,'inside_VA':inside_va,'above_VAH':above_vah,
      'nas_short10':matrix[i]['nas_short_10'],'demand_cat':q.get('demand_category','')})
with open(f"{D}/l2_bpt_deep_confluence.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
# REMAINING LOSERS the volume×1Dbear gate misses: E33,E8,E9 (1D-bull) + top-traps E15,E24,E34,E39
REM={'E33','E8','E9','E15','E24','E34','E39'}
def fl(x):
    try:return float(x)
    except:return None
print("=== feature values: WINNERS vs REMAINING LOSERS ===")
print(f"{'ep':<5}{'win':<4}{'d1b':<4}{'realVC':>7}{'bullDiv':>8}{'>VAL':>6}{'<VAH':>6}{'inVA':>5}{'>VAH':>5}{'nasS':>5}")
for r in rows:
    if r['episode_id'] in WIN or r['episode_id'] in REM:
        tag='W' if r['is_win'] else 'L'
        print(f"{r['episode_id']:<5}{tag:<4}{r['d1_bear']:<4}{str(r['real_volclmx']):>7}{r['rsi_bull_div']:>8}{str(r['dist_above_VAL_atr']):>6}{str(r['dist_below_VAH_atr']):>6}{str(r['inside_VA']):>5}{str(r['above_VAH']):>5}{str(r['nas_short10']):>5}")
# medians win vs remaining-loser for each numeric
print("\n=== medians ===")
for key in ['real_volclmx','dist_above_VAL_atr','dist_below_VAH_atr']:
    wv=[fl(r[key]) for r in rows if r['is_win'] and fl(r[key]) is not None]
    lv=[fl(r[key]) for r in rows if r['episode_id'] in REM and fl(r[key]) is not None]
    print(f"  {key:<22} WIN med {round(statistics.median(wv),2) if wv else '-'}  REM-LOSER med {round(statistics.median(lv),2) if lv else '-'}")
print("\n above_VAH: WIN", sum(1 for r in rows if r['is_win'] and r['above_VAH']==1),"/9  REM-LOSER",sum(1 for r in rows if r['episode_id'] in REM and r['above_VAH']==1),f"/{len(REM)}")
print(" inside_VA: WIN", sum(1 for r in rows if r['is_win'] and r['inside_VA']==1),"/9  REM-LOSER",sum(1 for r in rows if r['episode_id'] in REM and r['inside_VA']==1),f"/{len(REM)}")
