#!/usr/bin/env python3
"""Loser-cut filter search for ALVO E3_shallowleg.
Members: macro_drop_atr<4 AND disp4_atr<-0.5. Outcome=R_reclaim.
Forbidden (target-def, no re-use): macro_drop_atr, disp4_atr.
Forbidden (look-ahead/outcome): R_reclaim, R_8atr, near_M8, held8, runner, reclaim_idx, low_idx.
Goal: cut max losers keeping >=90% winners, minimize max-losing-streak.
"""
import json, itertools

PATH = "/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo/entry_dataset.jsonl"

rows = [json.loads(l) for l in open(PATH) if l.strip()]

# membership
mem = [r for r in rows if r.get("macro_drop_atr", 99) < 4 and r.get("disp4_atr", 99) < -0.5]
mem.sort(key=lambda r: r["low_t"])

def is_win(r): return r["R_reclaim"] > 0

def maxstreak(rs):
    cur = mx = 0
    for r in rs:
        if not is_win(r):
            cur += 1; mx = max(mx, cur)
        else:
            cur = 0
    return mx

def stats(rs):
    n = len(rs); w = sum(is_win(r) for r in rs)
    wr = w / n if n else 0
    return n, w, n - w, round(100 * wr, 1), maxstreak(rs)

n0, w0, l0, wr0, ms0 = stats(mem)
print(f"BEFORE: n={n0} winners={w0} losers={l0} WR={wr0}% maxstreak={ms0}")

FORBIDDEN = {"macro_drop_atr", "disp4_atr", "R_reclaim", "R_8atr", "near_M8",
             "held8", "runner", "reclaim_idx", "low_idx", "low_t", "yr", "block", "yr"}

ALLOWED = ["rsi","rsi_low","rsi_head","dist_ema_atr","ema_slope_atr","macro_bull","macro_bear",
"macro_retr","sweep_depth_atr","reclaim_speed","disp8_atr","up_closes8","range_exp","leg_ext",
"room_atr","low_wick","low_closepos","atr_regime","hour","killzone","vol_low_vs_med",
"nas_long_16","nas_short_16","nas_long_48","nas_last_long","smc_choch","smc_bos",
"sell_S","sell_M","sell_L","buy_S","buy_M","buy_L","sell_w","buy_w","sell_pol","in_demand","in_supply"]

# ---- univariate separation: for each feature, find a threshold direction that cuts losers, keeps winners
winners = [r for r in mem if is_win(r)]
losers  = [r for r in mem if not is_win(r)]

def quantiles(vals):
    vals = sorted(vals)
    qs = []
    for q in [0.1,0.2,0.25,0.3,0.4,0.5,0.6,0.7,0.75,0.8,0.9]:
        i = int(q*(len(vals)-1))
        qs.append(vals[i])
    return sorted(set(qs))

# candidate atomic predicates: (desc, fn) that KEEP the trade
cands = []
for f in ALLOWED:
    vals = [r[f] for r in mem if f in r and r[f] is not None]
    if not vals: continue
    uniq = sorted(set(vals))
    if len(uniq) <= 6:
        thr_pts = uniq
    else:
        thr_pts = quantiles(vals)
    for t in thr_pts:
        # keep if feature >= t   (removes low side)
        cands.append((f">= {f}>={t}", lambda r,f=f,t=t: r.get(f,None) is not None and r[f] >= t))
        cands.append((f"<= {f}<={t}", lambda r,f=f,t=t: r.get(f,None) is not None and r[f] <= t))

def eval_keep(rs, keepfn):
    kept = [r for r in rs if keepfn(r)]
    return kept

# score atomic predicates: keep >=90% winners, maximize losers cut
WTOT = len(winners); LTOT = len(losers)
atomic = []
for desc, fn in cands:
    kept = eval_keep(mem, fn)
    kw = sum(is_win(r) for r in kept); kl = len(kept)-kw
    if WTOT==0: continue
    wkept = kw/WTOT
    lcut = (LTOT-kl)/LTOT if LTOT else 0
    if wkept >= 0.90 and lcut > 0:
        atomic.append((desc, fn, wkept, lcut, kw, kl))

atomic.sort(key=lambda x:(-x[3], -x[2]))
print("\nTop atomic predicates (wkept>=0.90):")
for desc,fn,wk,lc,kw,kl in atomic[:15]:
    print(f"  {desc:28s} wkept={wk*100:.1f}% lcut={lc*100:.1f}% kept_w={kw} kept_l={kl}")

# ---- combos of up to 3 atomic predicates (AND) from distinct base features
def basefeat(desc): return desc.split()[1].split(">")[0].split("<")[0]

best = None
pool = atomic[:40]
combos = []
for k in [1,2,3]:
    for combo in itertools.combinations(pool, k):
        feats = set(basefeat(c[0]) for c in combo)
        if len(feats) != k:  # require orthogonal distinct features
            continue
        keepfn = lambda r, cs=combo: all(c[1](r) for c in cs)
        kept = eval_keep(mem, keepfn)
        kw = sum(is_win(r) for r in kept); kl=len(kept)-kw
        wkept = kw/WTOT; lcut=(LTOT-kl)/LTOT if LTOT else 0
        if wkept>=0.90:
            ms = maxstreak(kept)
            combos.append((lcut, -ms, wkept, combo, kept, kw, kl, ms))

combos.sort(key=lambda x:(-x[0], x[1], -x[2]))
print("\nTop combos (wkept>=0.90), ranked by losers_cut then min streak:")
for lcut,negms,wkept,combo,kept,kw,kl,ms in combos[:12]:
    descs = " AND ".join(c[0].split(' ',1)[1] for c in combo)
    print(f"  lcut={lcut*100:.1f}% wkept={wkept*100:.1f}% streak={ms} n={len(kept)} | {descs}")

# ---- DEVIL'S ADVOCATE OVERRIDE: rank by streak (stated objective) then losers_cut.
# The raw-lcut leader (sweep_depth_atr>=-2.552 ...) RAISED streak 7->9 and used a
# bare quantile cut on geometry co-lineage with the regime def. Rejected.
# Locked filter: orthogonal, causal, streak-reducing, no year collapses.
def keep_locked(r):
    return (r.get("low_wick") is not None and r["low_wick"] >= 0.155
            and r.get("sell_pol") is not None and r["sell_pol"] <= 0.5)
LOCKED_DESC = "low_wick>=0.155 AND sell_pol<=0.5"
kept_locked = [r for r in mem if keep_locked(r)]

def yr_wr(rs, y):
    sub=[r for r in rs if r["yr"]==y]
    return round(100*sum(is_win(r) for r in sub)/len(sub),1) if sub else None
nL,wL,lL,wrL,msL = stats(kept_locked)
kwL = sum(is_win(r) for r in kept_locked); klL = len(kept_locked)-kwL
print("\n=== LOCKED FILTER (DA-selected) ===")
print("desc:", LOCKED_DESC)
print(f"AFTER n={nL} WR={wrL}% maxstreak={msL}")
print(f"winners_kept={kwL}/{WTOT} ({100*kwL/WTOT:.1f}%) losers_cut={LTOT-klL}/{LTOT} ({100*(LTOT-klL)/LTOT:.1f}%)")
print("y24",yr_wr(kept_locked,2024),"y25",yr_wr(kept_locked,2025),"y26",yr_wr(kept_locked,2026))

if combos:
    lcut,negms,wkept,combo,kept,kw,kl,ms = combos[0]
    descs = " AND ".join(c[0].split(' ',1)[1] for c in combo)
    na,wa,la,wra,msa = stats(kept)
    # WR by year
    def yr_wr(rs,y):
        sub=[r for r in rs if r["yr"]==y]
        if not sub: return None
        return round(100*sum(is_win(r) for r in sub)/len(sub),1)
    print("\n=== BEST FILTER ===")
    print("desc:", descs)
    print(f"AFTER n={na} WR={wra}% maxstreak={msa}")
    print(f"winners_kept={kw}/{WTOT} ({100*kw/WTOT:.1f}%) losers_cut={LTOT-kl}/{LTOT} ({100*(LTOT-kl)/LTOT:.1f}%)")
    print("y24",yr_wr(kept,2024),"y25",yr_wr(kept,2025),"y26",yr_wr(kept,2026))
    # also report year counts before
    for y in [2024,2025,2026]:
        sub=[r for r in mem if r["yr"]==y]
        ka=[r for r in kept if r["yr"]==y]
        print(f"  yr{y}: before n={len(sub)} WR={yr_wr(mem,y)} | after n={len(ka)} WR={yr_wr(kept,y)}")
else:
    print("\nNO combo cuts losers while keeping >=90% winners -> desc='nenhum'")
