import json, collections

rows=[json.loads(l) for l in open('entry_dataset.jsonl')]

def passes(r):
    return r['disp4_atr'] < -0.5 and r['atr_regime'] < 1.0

sel=[r for r in rows if passes(r)]
n=len(sel)
def stats(s):
    if not s: return (0,None,None)
    wr=100*sum(1 for r in s if r['R_reclaim']>0)/len(s)
    avgr=sum(r['R_reclaim'] for r in s)/len(s)
    return (len(s),round(wr,1),round(avgr,3))

print('=== FULL ===')
print('n,WR,avgR =', stats(sel))
print('sumR =', round(sum(r['R_reclaim'] for r in sel),1))

print('\n=== PER YEAR ===')
for y in sorted(set(r['yr'] for r in sel)):
    print(y, stats([r for r in sel if r['yr']==y]))

print('\n=== PER BLOCK ===')
blks=sorted(set(r['block'] for r in sel))
for b in blks:
    print(b, stats([r for r in sel if r['block']==b]))

print('\n=== LEAVE-ONE-BLOCK-OUT (avgR of remainder) ===')
worst=None
for b in blks:
    rem=[r for r in sel if r['block']!=b]
    a=sum(r['R_reclaim'] for r in rem)/len(rem)
    print('drop',b,'-> n',len(rem),'avgR',round(a,3))
    if worst is None or a<worst[1]: worst=(b,a)
print('WORST fold avgR =', worst[0], round(worst[1],3))

print('\n=== EX-TOP2 ===')
ssort=sorted(sel,key=lambda r:r['R_reclaim'],reverse=True)
print('top5 R =',[round(r['R_reclaim'],2) for r in ssort[:5]])
ex2=ssort[2:]
print('ex-top2 n,WR,avgR =', stats(ex2))

print('\n=== R distribution ===')
Rs=[r['R_reclaim'] for r in sel]
print('max',round(max(Rs),2),'min',round(min(Rs),2))
print('sumR',round(sum(Rs),1))
# contribution of top trades
tot=sum(Rs)
print('top1 share %', round(100*ssort[0]['R_reclaim']/tot,1))
print('top2 share %', round(100*(ssort[0]['R_reclaim']+ssort[1]['R_reclaim'])/tot,1))
print('top5 share %', round(100*sum(r['R_reclaim'] for r in ssort[:5])/tot,1))

print('\n=== sign of avgR per block (stationarity) ===')
print([1 if sum(r["R_reclaim"] for r in sel if r["block"]==b)/max(1,len([x for x in sel if x["block"]==b]))>0 else 0 for b in blks])
