import json, math
rows=[json.loads(l) for l in open('dataset_5atr.jsonl')]

def wr(rs): return 100*sum(r['win'] for r in rs)/len(rs) if rs else float('nan')
def streak(rs):
    m=c=0
    for r in rs:
        if r['win']==0: c+=1; m=max(m,c)
        else: c=0
    return m
def avgR(rs): return sum(r['R'] for r in rs)/len(rs) if rs else float('nan')
def keep(r,t1=0.78,t2=-0.28): return r['disp4_atr']>=t1 and r['dist_supply_atr']>=t2

base=rows
kept=[r for r in rows if keep(r)]
cut=[r for r in rows if not keep(r)]
base_w=sum(r['win'] for r in base); kept_w=sum(r['win'] for r in kept)
base_l=len(base)-base_w; kept_l=len(kept)-kept_w

print('=== TOTALS ===')
print('base n=%d WR=%.2f streak=%d avgR=%.3f winners=%d losers=%d'%(len(base),wr(base),streak(base),avgR(base),base_w,base_l))
print('keep n=%d WR=%.2f streak=%d avgR=%.3f'%(len(kept),wr(kept),streak(kept),avgR(kept)))
print('winners_kept_pct=%.2f'%(100*kept_w/base_w))
print('losers_cut_pct=%.2f'%(100*(base_l-kept_l)/base_l))

wk,nk=sum(r['win'] for r in kept),len(kept)
wc,nc=sum(r['win'] for r in cut),len(cut)
pk=wk/nk; pc=wc/nc; p=(wk+wc)/(nk+nc); se=math.sqrt(p*(1-p)*(1/nk+1/nc))
print('keep-vs-cut z=%.2f (keepWR %.2f vs cutWR %.2f)'%((pk-pc)/se,100*pk,100*pc))

print('\n=== PER YEAR ===')
veto_year=False
for y in sorted(set(r['yr'] for r in rows)):
    by=[r for r in base if r['yr']==y]; ky=[r for r in kept if r['yr']==y]
    bw=wr(by); kw=wr(ky); flag='WORSE' if kw<bw else 'ok'
    if kw<bw: veto_year=True
    print('%d base=%.2f(n%d) keep=%.2f(n%d) %s'%(y,bw,len(by),kw,len(ky),flag))

print('\n=== PER BLOCK ===')
worse_blocks=0
for b in sorted(set(r['block'] for r in rows)):
    bb=[r for r in base if r['block']==b]; kb=[r for r in kept if r['block']==b]
    bw=wr(bb); kw=wr(kb); flag=''
    if kw<bw: worse_blocks+=1; flag='WORSE'
    print('%s base=%.2f(n%d) keep=%.2f(n%d) %s'%(b,bw,len(bb),kw,len(kb),flag))
print('worse_blocks=%d/8'%worse_blocks)

print('\n=== NEIGHBORHOOD +-20% ===')
collapse=False
for t1 in [0.624,0.78,0.936]:
    for t2 in [-0.336,-0.28,-0.224]:
        kk=[r for r in rows if r['disp4_atr']>=t1 and r['dist_supply_atr']>=t2]
        kw=sum(r['win'] for r in kk)
        w=wr(kk)
        if w<60.49: collapse=True
        print('t1=%.3f t2=%.3f n=%d WR=%.2f wkept=%.1f'%(t1,t2,len(kk),w,100*kw/base_w))

print('\nveto_year=%s worse_blocks=%d neighborhood_collapse=%s'%(veto_year,worse_blocks,collapse))
