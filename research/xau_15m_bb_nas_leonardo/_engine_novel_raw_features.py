#!/usr/bin/env python3
"""
_engine_novel_raw_features.py
INVENTOR lens: compute NOVEL causal features from RAW primitives/*.json (OHLC+rsi+atr+ema21)
and bubbles/*.jsonl (known_at filtered), aligned to the RECLAIM bar j (entry bar).

All features are as-of bar j (entry bar). For bubbles, only bubbles with known_at <= t[j] used.

Novel ideas tested:
  1. decel       : deceleration of the fall (drop in last 4 bars before low < drop in prior 4) -> momentum exhaustion
  2. rsi_div     : bullish RSI divergence (price low <= prior swing low BUT rsi at low > rsi at prior swing low)
  3. retest_lo   : reclaim low is a RETEST of an older swing low within tol (double-bottom)
  4. absorb      : a large SELL bubble printed near the low but price held (absorption)
  5. vbp_node    : distance of entry close to a volume-by-price node (high-volume price cluster) from RAW volume
  6. since_pivot : bars since last confirmed pivot (CHoCH/BOS) -- structural freshness
  7. demand_zone : entry inside / just above a RAW demand zone (born before low)
  8. sweep2      : sweep-of-the-sweep (the low took out a prior recent swing low = stop run)
  9. fast_choch  : a CHoCH printed shortly after the low (fast structural shift up)

Outputs an augmented jsonl with novel features merged, then single-feature scans.
"""
import json, os, glob, statistics as st, datetime as dt
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
DS = os.path.join(HERE, 'entry_dataset.jsonl')
PRIM = os.path.join(HERE, 'primitives')
BUB = os.path.join(HERE, 'bubbles')
OUT = os.path.join(HERE, 'entry_dataset_novel.jsonl')

# map block date -> primitives file & bubbles file
def find_prim(block):
    g = glob.glob(os.path.join(PRIM, '*%s*' % block)) + glob.glob(os.path.join(PRIM, '*replay_%s*' % block))
    g = [p for p in glob.glob(os.path.join(PRIM,'*.json')) if block in os.path.basename(p)]
    return g[0] if g else None

def find_bub(block):
    g = [p for p in glob.glob(os.path.join(BUB,'*.jsonl')) if block in os.path.basename(p)]
    return g[0] if g else None

def swlows(L, win=2):
    """indices of fractal swing lows: L[i] strictly lowest in +-win window."""
    out=[]
    for i in range(win, len(L)-win):
        seg=L[i-win:i+win+1]
        if L[i]==min(seg) and seg.count(L[i])==1:
            out.append(i)
    return out

def compute_novel(block):
    pf = find_prim(block); bf = find_bub(block)
    pr = json.load(open(pf))
    s = pr['series']
    n = len(s)
    L=[b['l'] for b in s]; H=[b['h'] for b in s]; C=[b['c'] for b in s]; V=[b['v'] for b in s]
    T=[b['t'] for b in s]
    t2idx = {b['t']: k for k,b in enumerate(s)}
    smc = sorted(pr['smc_events'], key=lambda e:e['t'])
    zones = pr['zones']
    # bubbles
    bubs=[]
    if bf:
        for line in open(bf):
            bubs.append(json.loads(line))
    bubs.sort(key=lambda b:b['known_at'])
    return dict(s=s,n=n,L=L,H=H,C=C,V=V,T=T,t2idx=t2idx,smc=smc,zones=zones,bubs=bubs)

CACHE={}
def get_block(block):
    if block not in CACHE:
        CACHE[block]=compute_novel(block)
    return CACHE[block]

def feats_for(rec):
    blk = get_block(rec['block'])
    s=blk['s']; n=blk['n']; L=blk['L']; H=blk['H']; C=blk['C']; V=blk['V']; T=blk['T']
    i=rec['low_idx']; j=rec['reclaim_idx']
    atr = s[j]['atr'] or s[i]['atr'] or 1.0
    tj = T[j]
    lowp = s[i]['l']
    f={}

    # 1. deceleration of the fall: drop magnitude last 4 bars into low vs prior 4
    if i>=8:
        drop_recent = s[i-4]['h']-s[i]['l'] if (s[i-4]['h']-s[i]['l'])>0 else 0
        drop_prior  = s[i-8]['h']-s[i-4]['l'] if (s[i-8]['h']-s[i-4]['l'])>0 else 0
        # deceleration ratio: recent/prior < 1 means the fall is slowing
        f['decel_ratio'] = drop_recent/drop_prior if drop_prior>0 else 1.0
    else:
        f['decel_ratio']=1.0

    # 2. bullish RSI divergence at the low: compare to prior swing low within lookback 60 bars
    rsi_i = s[i]['rsi']
    div=0
    if rsi_i is not None:
        lo=max(0,i-60)
        prev_lows=[k for k in swlows(L[lo:i], win=2)]
        prev_lows=[k+lo for k in prev_lows]
        if prev_lows:
            pk=prev_lows[-1]
            rsi_pk=s[pk]['rsi']
            if rsi_pk is not None and L[i] <= L[pk] and rsi_i > rsi_pk + 1.0:
                div=1
    f['rsi_div']=div

    # 3. retest of older swing low (double bottom): low within 0.5ATR of a swing low 10-120 bars earlier
    retest=0
    lo=max(0,i-120); hi=max(0,i-10)
    cand=[k for k in swlows(L[:i],win=2) if lo<=k<=hi]
    for k in cand:
        if abs(L[i]-L[k]) <= 0.5*atr:
            retest=1; break
    f['retest_lo']=retest

    # 4. absorption: a SELL bubble (any size) printed in [i-3, j] near the low but price reclaimed
    absorb=0; absorbL=0
    for b in blk['bubs']:
        if b['known_at'] > tj: break
        bt=b['t']
        if b.get('side')=='SELL' and T[max(0,i-3)] <= bt <= tj:
            absorb=1
            if b.get('size')=='L': absorbL=1
    f['absorb_sell']=absorb; f['absorb_sellL']=absorbL

    # 5. volume-by-price node distance: build VBP over last 192 bars (causal up to j), find POC bin
    lo=max(0,j-192)
    seg=s[lo:j+1]
    binw=0.5*atr
    if binw<=0: binw=1.0
    vbp=defaultdict(float)
    for b in seg:
        mid=(b['h']+b['l'])/2.0
        binid=round(mid/binw)
        vbp[binid]+=b['v']
    if vbp:
        poc_bin=max(vbp, key=vbp.get)
        poc_price=poc_bin*binw
        f['dist_vbp_atr']=(s[j]['c']-poc_price)/atr
    else:
        f['dist_vbp_atr']=0.0

    # 6. bars since last confirmed pivot (CHoCH or BOS) before j
    since=999
    for e in reversed(blk['smc']):
        if e['t'] <= tj and e['t']<=T[i]:
            since=(tj-e['t'])//900
            break
    f['since_pivot']=min(since,999)

    # 7. entry inside/just above a RAW demand zone born before the low
    in_demand=0; dz_dist=99.0
    for z in blk['zones']:
        if z.get('text')!='DEMAND': continue
        if z.get('born_t',1e18) > T[i]: continue   # zone must pre-exist the low (causal)
        zl=z['low']; zh=z['high']
        # entry close within or just above zone (within 0.5ATR above zone high)
        c=s[j]['c']
        if zl-0.25*atr <= s[i]['l'] <= zh+0.25*atr:
            in_demand=1
        d=abs(c-(zh+zl)/2.0)/atr
        if d<dz_dist: dz_dist=d
    f['in_demand']=in_demand
    f['dz_dist_atr']=round(min(dz_dist,99.0),3)

    # 8. sweep-of-sweep: low took out the most recent swing low (stop run) within last 40 bars
    sweep2=0
    lo=max(0,i-40)
    recent=[k for k in swlows(L[:i],win=2) if lo<=k<i]
    if recent:
        last_sl=L[recent[-1]]
        if L[i] < last_sl:   # took it out
            sweep2=1
    f['sweep2']=sweep2

    # 9. fast CHoCH: a CHoCH printed between low and j+? (causal: only events with t<=tj)
    fast_choch=0
    for e in blk['smc']:
        if 'CHoCH' in e.get('text','') and T[i] < e['t'] <= tj:
            fast_choch=1; break
    f['fast_choch']=fast_choch

    return f

if __name__=='__main__':
    rows=[json.loads(l) for l in open(DS)]
    out=[]
    for idx,rec in enumerate(rows):
        try:
            nf=feats_for(rec)
        except Exception as ex:
            nf={}
        rec.update(nf)
        out.append(rec)
        if idx%500==0:
            print('...',idx)
    with open(OUT,'w') as fo:
        for r in out:
            fo.write(json.dumps(r)+'\n')
    print('wrote', OUT, len(out))
