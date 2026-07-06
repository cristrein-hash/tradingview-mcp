import json,bisect
from pathlib import Path
HERE=Path(__file__).resolve().parent
exec((HERE/'macro_leg_position_veto_20260705.py').read_text().split('VETOS = {')[0])
HI=[b['h'] for b in S];LO=[b['l'] for b in S];CL=[b['c'] for b in S];OP=[b.get('o',b['c']) for b in S]
CACHE={r['cj_t'] for r in (json.loads(l) for l in open(HERE/'results'/'raw_feature_cache_20260706.jsonl'))}
UNIV=sorted([u for u in U if u['cj_t'] in R3 and u['cj_t'] in CACHE],key=lambda u:u['cj_t'])
for u in UNIV: u['_flo']=u['g_sl']+0.1*(u.get('g_atr') or 5.0); u['_a']=u.get('g_atr') or 5.0
EV=[];cur=[]
for u in UNIV:
    if cur and u['cj_t']-cur[-1]['cj_t']<=48*3600 and abs(u['_flo']-cur[-1]['_flo'])<=3*u['_a']: cur.append(u)
    else:
        if cur: EV.append(cur)
        cur=[u]
if cur: EV.append(cur)
for ev in EV:
    mn=1e18
    for pos,u in enumerate(ev,1):
        ci=bisect.bisect_right(TS,u['cj_t'])-1;pm=mn
        u['_pl']=int(pos>1 and u['_flo']>pm+0.05*u['_a']);mn=min(mn,u['_flo'])
        rng=max(1e-9,HI[ci]-LO[ci])
        u['_rec']=int(ci>=1 and CL[ci]>HI[ci-1]);u['_bu']=int(CL[ci]>OP[ci]);u['_cir']=(CL[ci]-LO[ci])/rng
def base(u): return u['_pl']==1 and u['_rec']==1 and u['_bu']==1 and u['_cir']>=0.5
def h(rs): return sum(1 for r in rs if R3[r['cj_t']]['R3']>=3)/len(rs)
prod=[ev for ev in EV if any(base(u) for u in ev)]
allc=[u for ev in prod for u in ev]
print(f'eventos-com-reclaim {len(prod)} | TODOS candidatos nesses eventos: N{len(allc)} hit={h(allc):.4f}')
print(f'reclaim-pool nesses eventos: N{sum(1 for u in allc if base(u))} hit={h([u for u in allc if base(u)]):.4f}')
print(f'NAO-reclaim nesses eventos: hit={h([u for u in allc if not base(u)]):.4f}')
print(f'universo inteiro: {h(UNIV):.4f}')
