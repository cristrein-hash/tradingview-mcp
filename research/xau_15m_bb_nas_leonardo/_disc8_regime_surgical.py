"""Surgical INTERSECTION cuts: cut only where MULTIPLE loser-pocket conditions
co-occur (contextual reading), to preserve >=85% winners while raising WR.
Lens: counter-trend INTO supply; fast impulse at range-top; deep-leg shallow-retr.
Also union-of-intersections. RAW-causal. win=R>0.
"""
import sys, itertools
sys.path.insert(0,'/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo')
from _disc8_lib import load, max_losing_streak

rows=load(); N=len(rows)
BASE=sum(r['win'] for r in rows)/N
TOTW=sum(r['win'] for r in rows); TOTL=N-TOTW
BSTREAK=max_losing_streak(rows)
def g(r,k): return r.get(k)

ATOMS={
  'h1_down':       lambda r: g(r,'h1_trend')==-1,
  'h1_notup':      lambda r: g(r,'h1_trend')!=1,
  'macro_bear':    lambda r: g(r,'macro_bear')==1,
  'into_supply':   lambda r: g(r,'dist_supply_atr') is not None and g(r,'dist_supply_atr')<=0.0,
  'into_supply_s': lambda r: g(r,'dist_supply_atr') is not None and g(r,'dist_supply_atr')<=0.5,
  'fast8':         lambda r: g(r,'bars_to_8atr') is not None and g(r,'bars_to_8atr')<=51,
  'hi_path_eff':   lambda r: g(r,'path_eff') is not None and g(r,'path_eff')>0.34,
  'shallow_retr':  lambda r: g(r,'macro_retr') is not None and g(r,'macro_retr')<=0.90,
  'hd_pos_mid':    lambda r: g(r,'hd_pos') is not None and 0.61<g(r,'hd_pos')<=0.98,
  'hd_pos_hi':     lambda r: g(r,'hd_pos') is not None and g(r,'hd_pos')>0.98,
  'h4_dist_hi':    lambda r: g(r,'h4_dist') is not None and g(r,'h4_dist')>8.21,
  'lo_h4_eff':     lambda r: g(r,'h4_eff') is not None and g(r,'h4_eff')<=0.24,
  'rsi_hot':       lambda r: g(r,'rsi') is not None and g(r,'rsi')>72.6,
  'h4_range':      lambda r: g(r,'h4_trend')==0,
  'lo_atr_exp':    lambda r: g(r,'atr_expand') is not None and g(r,'atr_expand')>1.30,
}

def metrics(cut_pred, desc):
    kept=[r for r in rows if not cut_pred(r)]
    cut=[r for r in rows if cut_pred(r)]
    if not kept or not cut: return None
    wk=sum(r['win'] for r in kept); nk=len(kept); wr=wk/nk
    streak=max_losing_streak(kept)
    win_kept_pct=100*wk/TOTW
    loss_cut=len(cut)-sum(r['win'] for r in cut)
    losers_cut_pct=100*loss_cut/TOTL
    cut_wr=sum(r['win'] for r in cut)/len(cut)
    yb={}
    for y in (2024,2025,2026):
        ky=[r for r in kept if r['yr']==y]
        yb[y]=(sum(x['win'] for x in ky)/len(ky),len(ky)) if ky else (0,0)
    blk={}
    for b in sorted(set(r['block'] for r in rows)):
        kb=[r for r in kept if r['block']==b]
        blk[b]=(sum(x['win'] for x in kb)/len(kb),len(kb)) if kb else (0,0)
    nb_ge=sum(1 for w,c in blk.values() if c>=15 and w>=BASE)
    nb_have=sum(1 for w,c in blk.values() if c>=15)
    wr_up=wr>BASE
    all_yr=all(yb[y][0]>=BASE for y in (2024,2025,2026))
    enough=all(yb[y][1]>=30 for y in (2024,2025,2026))
    robust=bool(wr_up and all_yr and enough and nb_ge>=6)
    return dict(desc=desc,n_keep=nk,n_cut=len(cut),cut_wr=round(cut_wr,3),
        wr_keep=round(wr,4),streak_keep=streak,streak_base=BSTREAK,
        winners_kept_pct=round(win_kept_pct,1),losers_cut_pct=round(losers_cut_pct,1),
        y24=round(yb[2024][0],4),y24n=yb[2024][1],y25=round(yb[2025][0],4),y25n=yb[2025][1],
        y26=round(yb[2026][0],4),y26n=yb[2026][1],nb_ge=nb_ge,nb_have=nb_have,
        wr_up=wr_up,all_yr=all_yr,robust=robust)

def show(m):
    if not m: return
    print(f"  [{ 'ROBUST' if m['robust'] else '  no  ' }] {m['desc']}")
    print(f"    keep={m['n_keep']} wr={m['wr_keep']}  cut={m['n_cut']}(cutWR{m['cut_wr']}) streak {m['streak_base']}->{m['streak_keep']}"
          f"  Wkept={m['winners_kept_pct']}% Lcut={m['losers_cut_pct']}%")
    print(f"    y24={m['y24']}(n{m['y24n']}) y25={m['y25']}(n{m['y25n']}) y26={m['y26']}(n{m['y26n']}) blk>=base {m['nb_ge']}/{m['nb_have']}")

print(f"BASE WR={BASE:.4f} streak={BSTREAK}\n")

# pairwise INTERSECTION cuts: cut where A AND B both true
print("=== 2-ATOM INTERSECTION cuts (cut if A AND B) — surgical loser pockets ===")
names=list(ATOMS.keys())
allm=[]
for a,b in itertools.combinations(names,2):
    fa,fb=ATOMS[a],ATOMS[b]
    m=metrics(lambda r,fa=fa,fb=fb: fa(r) and fb(r), f"CUT {a} & {b}")
    if m and m['n_cut']>=20 and m['cut_wr']<=0.50:
        allm.append(m)
for m in sorted(allm,key=lambda x:(x['cut_wr'],-x['n_cut']))[:20]:
    show(m)

# 3-atom intersections (very surgical)
print("\n=== 3-ATOM INTERSECTION cuts (cut if A&B&C) ===")
allm3=[]
for a,b,c in itertools.combinations(names,3):
    fa,fb,fc=ATOMS[a],ATOMS[b],ATOMS[c]
    m=metrics(lambda r,fa=fa,fb=fb,fc=fc: fa(r) and fb(r) and fc(r), f"CUT {a}&{b}&{c}")
    if m and m['n_cut']>=20 and m['cut_wr']<=0.45 and m['winners_kept_pct']>=90:
        allm3.append(m)
for m in sorted(allm3,key=lambda x:(x['cut_wr'],-x['n_cut']))[:20]:
    show(m)
