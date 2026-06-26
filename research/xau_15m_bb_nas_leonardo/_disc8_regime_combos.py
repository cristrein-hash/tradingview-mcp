"""Regime/localization-lens COMBO search for 8ATR loser-cut.
Hypothesis: losers cluster at specific leg/regime locations:
 - counter-trend (h1_trend=-1, macro_bear) entries
 - entries INTO/above supply (dist_supply small/negative)
 - fast pure-impulse legs (bars_to_8atr low, path_eff high)
 - mid daily-range (hd_pos mid), shallow retrace of deep leg
We CUT trades matching a loser-pocket; KEEP = not(cut).
Target: WR up >66%, streak down, >=85% winners kept, robust across 3yrs+8blocks.
RAW-causal. win=R>0.
"""
import sys, itertools
sys.path.insert(0, '/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo')
from _disc8_lib import load, max_losing_streak

rows = load()
N = len(rows)
BASE = sum(r['win'] for r in rows)/N
TOTW = sum(r['win'] for r in rows)
TOTL = N - TOTW
BASE_STREAK = max_losing_streak(rows)

def g(r,k):
    return r.get(k)

# ---- atomic CUT predicates (each marks a candidate loser-pocket) ----
# Use None-safe: if feature null, predicate is False (don't cut on missing info)
ATOMS = {
  'h1_down':       lambda r: g(r,'h1_trend')==-1,
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
  'lo_atr_exp':    lambda r: g(r,'atr_expand') is not None and g(r,'atr_expand')>1.30,
  'h1_range':      lambda r: g(r,'h1_trend')==0,
  'h4_range':      lambda r: g(r,'h4_trend')==0,
  'rsi_hot':       lambda r: g(r,'rsi') is not None and g(r,'rsi')>72.6,
}

def metrics(keep_pred, desc):
    kept=[r for r in rows if keep_pred(r)]
    cut=[r for r in rows if not keep_pred(r)]
    if not kept: return None
    wk=sum(r['win'] for r in kept); nk=len(kept)
    wr=wk/nk
    streak=max_losing_streak(kept)
    win_kept_pct=100*wk/TOTW
    loss_cut=(len(cut)-sum(r['win'] for r in cut))
    losers_cut_pct=100*loss_cut/TOTL
    yb={}
    for y in (2024,2025,2026):
        ky=[r for r in kept if r['yr']==y]
        yb[y]=(sum(x['win'] for x in ky)/len(ky), len(ky)) if ky else (0,0)
    # block robustness
    blk={}
    for b in sorted(set(r['block'] for r in rows)):
        kb=[r for r in kept if r['block']==b]
        blk[b]=(sum(x['win'] for x in kb)/len(kb), len(kb)) if kb else (0,0)
    nb_ge=sum(1 for w,c in blk.values() if c>=15 and w>=BASE)
    nb_have=sum(1 for w,c in blk.values() if c>=15)
    wr_up = wr>BASE
    all_yr = all(yb[y][0]>=BASE for y in (2024,2025,2026))
    enough_yr = all(yb[y][1]>=30 for y in (2024,2025,2026))
    robust = bool(wr_up and all_yr and enough_yr and nb_ge>=6)
    return dict(desc=desc,n_keep=nk,wr_keep=round(wr,4),streak_keep=streak,
                winners_kept_pct=round(win_kept_pct,1),losers_cut_pct=round(losers_cut_pct,1),
                y24=round(yb[2024][0],4),y24n=yb[2024][1],
                y25=round(yb[2025][0],4),y25n=yb[2025][1],
                y26=round(yb[2026][0],4),y26n=yb[2026][1],
                nb_ge=nb_ge,nb_have=nb_have,wr_up=wr_up,all_yr=all_yr,robust=robust,
                streak_base=BASE_STREAK)

def show(m):
    if not m: print("  EMPTY"); return
    print(f"  [{ 'ROBUST' if m['robust'] else 'no' }] {m['desc']}")
    print(f"    n_keep={m['n_keep']} wr={m['wr_keep']} (base{round(BASE,4)}) streak {m['streak_base']}->{m['streak_keep']}"
          f"  Wkept={m['winners_kept_pct']}% Lcut={m['losers_cut_pct']}%")
    print(f"    y24={m['y24']}(n{m['y24n']}) y25={m['y25']}(n{m['y25n']}) y26={m['y26']}(n{m['y26n']}) "
          f"blocks>=base {m['nb_ge']}/{m['nb_have']}  wr_up={m['wr_up']} allyr={m['all_yr']}")

print(f"BASE WR={BASE:.4f} streak={BASE_STREAK} totW={TOTW} totL={TOTL}\n")

print("=== SINGLE-ATOM cuts (keep = not atom) ===")
single=[]
for name,fn in ATOMS.items():
    m=metrics(lambda r,fn=fn: not fn(r), f"CUT {name}")
    single.append(m)
for m in sorted(single,key=lambda x:-x['wr_keep']):
    show(m)

print("\n=== 2-ATOM UNION cuts (cut if A OR B) — broader loser net ===")
names=list(ATOMS.keys())
res2=[]
for a,b in itertools.combinations(names,2):
    fa,fb=ATOMS[a],ATOMS[b]
    m=metrics(lambda r,fa=fa,fb=fb: not(fa(r) or fb(r)), f"CUT {a} OR {b}")
    if m and m['winners_kept_pct']>=85 and m['wr_up']:
        res2.append(m)
for m in sorted(res2,key=lambda x:(-x['robust'],-x['wr_keep']))[:15]:
    show(m)

print("\n=== 3-ATOM UNION cuts (cut if A OR B OR C) ===")
res3=[]
for a,b,c in itertools.combinations(names,3):
    fa,fb,fc=ATOMS[a],ATOMS[b],ATOMS[c]
    m=metrics(lambda r,fa=fa,fb=fb,fc=fc: not(fa(r) or fb(r) or fc(r)), f"CUT {a} OR {b} OR {c}")
    if m and m['winners_kept_pct']>=85 and m['robust']:
        res3.append(m)
for m in sorted(res3,key=lambda x:(-x['wr_keep']))[:15]:
    show(m)
print(f"\n(robust 3-atom union count with Wkept>=85%: {len(res3)})")
