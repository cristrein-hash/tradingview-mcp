"""Validate top regime-lens candidates rigorously:
 leave-one-block-out stability, per-block detail, refinements.
RAW-causal. win=R>0.
"""
import sys
sys.path.insert(0,'/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo')
from _disc8_lib import load, max_losing_streak

rows=load(); N=len(rows)
BASE=sum(r['win'] for r in rows)/N
TOTW=sum(r['win'] for r in rows); TOTL=N-TOTW
BSTREAK=max_losing_streak(rows)
def g(r,k): return r.get(k)

CANDS={
 # cut predicate (True=cut). keep=not cut.
 'A: h1_notup & lo_h4_eff':
    lambda r: g(r,'h1_trend')!=1 and g(r,'h4_eff') is not None and g(r,'h4_eff')<=0.24,
 'B: lo_h4_eff (single)':
    lambda r: g(r,'h4_eff') is not None and g(r,'h4_eff')<=0.24,
 'C: h1_notup & lo_h4_eff & into_supply_s':
    lambda r: g(r,'h1_trend')!=1 and g(r,'h4_eff') is not None and g(r,'h4_eff')<=0.24 and g(r,'dist_supply_atr') is not None and g(r,'dist_supply_atr')<=0.5,
 'D: h1_notup & (lo_h4_eff OR into_supply_s)':
    lambda r: g(r,'h1_trend')!=1 and ((g(r,'h4_eff') is not None and g(r,'h4_eff')<=0.24) or (g(r,'dist_supply_atr') is not None and g(r,'dist_supply_atr')<=0.5)),
 'E: h1_notup & lo_h4_eff & not_deep_retr (macro_retr<=1.18)':
    lambda r: g(r,'h1_trend')!=1 and g(r,'h4_eff') is not None and g(r,'h4_eff')<=0.24 and g(r,'macro_retr') is not None and g(r,'macro_retr')<=1.18,
}

def full(cut_pred,desc):
    kept=[r for r in rows if not cut_pred(r)]
    cut=[r for r in rows if cut_pred(r)]
    wk=sum(r['win'] for r in kept); nk=len(kept); wr=wk/nk
    streak=max_losing_streak(kept)
    loss_cut=len(cut)-sum(r['win'] for r in cut)
    yb={y:( (lambda s:(sum(x['win'] for x in s)/len(s),len(s)) if s else (0,0))([r for r in kept if r['yr']==y]) ) for y in (2024,2025,2026)}
    blk={}
    for b in sorted(set(r['block'] for r in rows)):
        kb=[r for r in kept if r['block']==b]
        ab=[r for r in rows if r['block']==b]
        blk[b]=(round(sum(x['win'] for x in kb)/len(kb),3) if kb else None,len(kb),round(sum(x['win'] for x in ab)/len(ab),3))
    nb_ge=sum(1 for v in blk.values() if v[1]>=15 and v[0]>=BASE)
    nb_have=sum(1 for v in blk.values() if v[1]>=15)
    # leave-one-block-out: recompute kept-WR excluding each block; check still > base
    lobo=[]
    for b in blk:
        sub=[r for r in rows if r['block']!=b]
        ks=[r for r in sub if not cut_pred(r)]
        lobo.append((b,round(sum(x['win'] for x in ks)/len(ks),4)))
    lobo_min=min(w for _,w in lobo)
    all_yr=all(yb[y][0]>=BASE for y in (2024,2025,2026))
    enough=all(yb[y][1]>=30 for y in (2024,2025,2026))
    robust=bool(wr>BASE and all_yr and enough and nb_ge>=6 and lobo_min>BASE)
    print(f"\n[{ 'ROBUST' if robust else '  no  ' }] {desc}")
    print(f"  keep={nk} wr={wr:.4f}(base{BASE:.4f}) cut={len(cut)} cutWR={sum(r['win'] for r in cut)/len(cut):.3f} streak {BSTREAK}->{streak}")
    print(f"  Wkept={100*wk/TOTW:.1f}%  Lcut={100*loss_cut/TOTL:.1f}%")
    print(f"  y24={yb[2024][0]:.4f}(n{yb[2024][1]}) y25={yb[2025][0]:.4f}(n{yb[2025][1]}) y26={yb[2026][0]:.4f}(n{yb[2026][1]})  all_yr_ge_base={all_yr}")
    print(f"  blocks>=base {nb_ge}/{nb_have}: "+" ".join(f"{b[5:]}:{v[0]}/{v[2]}(n{v[1]})" for b,v in blk.items()))
    print(f"  LOBO kept-WR min={lobo_min:.4f} (all {[round(w,3) for _,w in lobo]})  not_carried_by_one_block={lobo_min>BASE}")
    return dict(desc=desc,n_keep=nk,wr_keep=round(wr,4),streak_keep=streak,
        winners_kept_pct=round(100*wk/TOTW,1),losers_cut_pct=round(100*loss_cut/TOTL,1),
        y24=round(yb[2024][0],4),y25=round(yb[2025][0],4),y26=round(yb[2026][0],4),robust=robust)

print(f"BASE WR={BASE:.4f} streak={BSTREAK} totW={TOTW} totL={TOTL}")
out={}
for k,fn in CANDS.items():
    out[k]=full(fn,k)
