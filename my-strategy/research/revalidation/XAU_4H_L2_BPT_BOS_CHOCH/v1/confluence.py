import json,csv,statistics
D="results"
frozen=[json.loads(l) for l in open('/tmp/raw_features_2020_2026.jsonl')]
N=len(frozen);H=[r['high'] for r in frozen];L=[r['low'] for r in frozen];C=[r['close'] for r in frozen];O=[r['open'] for r in frozen]
V=[r.get('volume') or 0 for r in frozen];RS=[r.get('rsi') for r in frozen]
geom={'E%d'%o['episode_id']:o for o in json.load(open('/tmp/plot_geometry.json'))}
matrix={int(r['candidate_id'][1:]):r for r in csv.DictReader(open(f"{D}/l2_bpt_v2_2_candidate_matrix.csv"))}
qual={r['candidate_id']:r for r in csv.DictReader(open(f"{D}/l2_bpt_v2_2_pruned_base_v2_demand_supply_quality.csv"))}
BUY={'plot_0','plot_2','plot_4'}; LARGE_BUY='plot_4'
def fl(x):
    try:return float(x)
    except:return None
# 1D-bear subset (from leg1d k=5): winners E1,E17 vs traps E6,E7,E11,E36,E37
SUBSET={'E1':'WIN','E17':'WIN','E6':'TRAP','E7':'TRAP','E11':'TRAP','E36':'TRAP','E37':'TRAP'}
def feats(i):
    # DEEP VOLUME
    avg20=sum(V[i-20:i])/20 if i>=20 else 1
    avg50=sum(V[i-50:i])/50 if i>=50 else 1
    vol_ratio=round(V[i]/avg20,2) if avg20 else None
    vol_climax_10=round(max(V[i-9:i+1])/avg50,2) if (i>=50 and avg50) else None  # panic spike recent vs avg50
    # was there a capitulation candle (huge vol + big bear range) in last 10 bars?
    cap=0
    for j in range(max(0,i-10),i+1):
        aj=sum(V[max(0,j-20):j])/20 if j>=20 else 1
        rng=H[j]-L[j]; atrj=None
        if V[j]>2.0*aj and C[j]<O[j]: cap+=1  # high-vol down candle = capitulation
    # RSI
    rsi=RS[i]; rsi_min_10=min([RS[j] for j in range(max(0,i-10),i+1) if RS[j] is not None] or [None])
    # bullish divergence: price made lower-low in last 12 but RSI higher-low
    seg=[(j,L[j],RS[j]) for j in range(max(0,i-12),i+1) if RS[j] is not None]
    bull_div=0
    if len(seg)>=6:
        mid=len(seg)//2; pr=min(seg[:mid],key=lambda x:x[1]); rc=min(seg[mid:],key=lambda x:x[1])
        if rc[1]<pr[1] and rc[2]>pr[2]: bull_div=1
    # BUBBLES (BUY)
    bubs=frozen[i].get('bubbles_recent') or []
    buy_recent=sum(1 for b in bubs if b.get('plot_id') in BUY and 0<=(b.get('bars_ago') or 99)<=10)
    large_buy=sum(1 for b in bubs if b.get('plot_id')==LARGE_BUY and 0<=(b.get('bars_ago') or 99)<=10)
    # NAS
    nas=frozen[i].get('nas_recent') or []
    nas_long_near=sum(1 for e in nas if (e.get('text') or '').upper()=='LONG' and (e.get('x',99))<=5)
    # Custom OB
    q=qual.get('C%d'%i,{}); inside_dem=q.get('inside_custom_ob_demand','0'); dem_cat=q.get('demand_category','')
    return dict(vol_ratio=vol_ratio,vol_climax_10=vol_climax_10,capit_candles=cap,rsi=round(rsi,0) if rsi else None,
        rsi_min_10=round(rsi_min_10,0) if rsi_min_10 else None,bull_div=bull_div,buy_bub=buy_recent,large_buy=large_buy,
        nas_long=nas_long_near,inside_dem=int(inside_dem=='1') if inside_dem else 0,dem_supp=int(dem_cat=='DEMAND_SUPPORTING_RETEST'))
print("=== 1D-BEAR SUBSET: confluence + deep volume (winners E1/E17 vs traps) ===")
print(f"{'ep':<5}{'grp':<6}{'volR':>5}{'volClmx':>8}{'capit':>6}{'rsi':>4}{'rsiMin':>7}{'bullDiv':>8}{'buyBub':>7}{'lgBuy':>6}{'nasL':>5}{'inDem':>6}{'demSup':>7}")
rowsub=[]
for ep,g in SUBSET.items():
    i=geom[ep]['bar_idx']; f=feats(i); rowsub.append((ep,g,f))
    print(f"{ep:<5}{g:<6}{str(f['vol_ratio']):>5}{str(f['vol_climax_10']):>8}{f['capit_candles']:>6}{str(f['rsi']):>4}{str(f['rsi_min_10']):>7}{f['bull_div']:>8}{f['buy_bub']:>7}{f['large_buy']:>6}{f['nas_long']:>5}{f['inside_dem']:>6}{f['dem_supp']:>7}")
# capitulation/confluence score
def score(f):
    s=0
    if f['vol_climax_10'] and f['vol_climax_10']>=2.5: s+=1
    if f['capit_candles']>=1: s+=1
    if f['rsi_min_10'] and f['rsi_min_10']<=35: s+=1
    if f['bull_div']: s+=1
    if f['large_buy']>=1 or f['buy_bub']>=3: s+=1
    return s
print("\n=== confluence score (capitulation) ===")
for ep,g,f in sorted(rowsub,key=lambda x:-score(x[2])):
    print(f"  {ep:<5}{g:<6} score={score(f)}")
