#!/usr/bin/env python3
"""Loser-cut filter search for target E0_8atr (members = R_8atr != null)."""
import json, itertools

PATH = "/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo/entry_dataset.jsonl"

rows = []
with open(PATH) as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        d = json.loads(line)
        if d.get("R_8atr") is not None:   # member of E0_8atr
            rows.append(d)

# sort by low_t
rows.sort(key=lambda r: r["low_t"])

def is_win(r):  return r["R_8atr"] > 0
def is_loss(r): return r["R_8atr"] <= 0

def max_streak(seq):
    """max consecutive losers"""
    best = cur = 0
    for r in seq:
        if is_loss(r):
            cur += 1
            best = max(best, cur)
        else:
            cur = 0
    return best

def stats(seq):
    n = len(seq)
    w = sum(1 for r in seq if is_win(r))
    wr = round(100*w/n, 1) if n else 0
    return n, w, n-w, wr, max_streak(seq)

N0, W0, L0, WR0, ST0 = stats(rows)
print(f"BEFORE: n={N0} winners={W0} losers={L0} WR={WR0}% maxstreak={ST0}")

# ---- PROHIBITED (look-ahead / target / rule-defining) ----
# look-ahead: R_reclaim,R_8atr,near_M8,held8,runner,reclaim_idx,low_idx
# rule-defining (8ATR confirm) NOT to reuse — we treat disp8_atr/up_closes8 as part of
# the 8ATR-displacement regime that defines entry; keep them out to stay orthogonal.
RULE = {"disp8_atr","up_closes8","R_reclaim","R_8atr","near_M8","held8","runner",
        "reclaim_idx","low_idx"}

CAUSAL = ["rsi","rsi_low","rsi_head","dist_ema_atr","ema_slope_atr","macro_bull",
    "macro_bear","macro_drop_atr","macro_retr","sweep_depth_atr","reclaim_speed",
    "disp4_atr","range_exp","leg_ext","room_atr","low_wick","low_closepos",
    "atr_regime","hour","killzone","vol_low_vs_med","nas_long_16","nas_short_16",
    "nas_long_48","nas_last_long","smc_choch","smc_bos","sell_S","sell_M","sell_L",
    "buy_S","buy_M","buy_L","sell_w","buy_w","sell_pol","in_demand","in_supply"]

winners = [r for r in rows if is_win(r)]
losers  = [r for r in rows if is_loss(r)]

# ---- univariate separation diagnostic ----
import statistics as st
print("\n--- univariate winner vs loser means ---")
diag = []
for f in CAUSAL:
    wv = [r[f] for r in winners if r.get(f) is not None]
    lv = [r[f] for r in losers  if r.get(f) is not None]
    if not wv or not lv: continue
    mw, ml = st.mean(wv), st.mean(lv)
    # pooled std for effect size
    sd = st.pstdev(wv+lv) or 1e-9
    eff = (mw-ml)/sd
    diag.append((abs(eff), f, mw, ml, eff))
diag.sort(reverse=True)
for ae,f,mw,ml,eff in diag[:15]:
    print(f"  {f:16s} winM={mw:8.3f} losM={ml:8.3f} eff={eff:+.3f}")

# ---- candidate threshold predicates (KEEP condition = pass filter) ----
# A predicate keeps a row if condition True. We want to DROP losers, keep >=90% winners.
def quantiles(vals, qs):
    s=sorted(vals);
    return [s[min(len(s)-1,int(q*len(s)))] for q in qs]

cands = []  # (name, fn)
for f in CAUSAL:
    allv = [r[f] for r in rows if r.get(f) is not None]
    if not allv: continue
    uniq = sorted(set(allv))
    if len(uniq) <= 6:
        # categorical: keep != each value, and >=value, <=value
        for v in uniq:
            cands.append((f"{f}!={v}", (lambda r,f=f,v=v: r.get(f)!=v)))
            cands.append((f"{f}>={v}", (lambda r,f=f,v=v: r.get(f) is not None and r.get(f)>=v)))
            cands.append((f"{f}<={v}", (lambda r,f=f,v=v: r.get(f) is not None and r.get(f)<=v)))
    else:
        ths = quantiles(allv,[0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9])
        for t in sorted(set(round(x,4) for x in ths)):
            cands.append((f"{f}>={t}", (lambda r,f=f,t=t: r.get(f) is not None and r.get(f)>=t)))
            cands.append((f"{f}<={t}", (lambda r,f=f,t=t: r.get(f) is not None and r.get(f)<=t)))

def eval_filter(keep_fn):
    kept = [r for r in rows if keep_fn(r)]
    kw = sum(1 for r in kept if is_win(r))
    kl = sum(1 for r in kept if is_loss(r))
    wk = round(100*kw/W0,1) if W0 else 0
    lc = round(100*(L0-kl)/L0,1) if L0 else 0
    return kept, kw, kl, wk, lc

# single-feature candidates meeting >=90% winners kept
print("\n--- single-feature candidates (>=90% winners kept, losers cut desc) ---")
singles = []
for name, fn in cands:
    kept, kw, kl, wk, lc = eval_filter(fn)
    if wk >= 90.0 and lc > 0:
        n,w,l,wr,stk = stats(kept)
        singles.append((lc, wk, stk, name, fn, n, wr))
singles.sort(key=lambda x:(-x[0], x[2], -x[1]))
for lc,wk,stk,name,fn,n,wr in singles[:20]:
    print(f"  cut={lc:5.1f}% keepW={wk:5.1f}% n={n:4d} WR={wr:5.1f}% streak={stk}  {name}")

# combos of 2 (AND) from top singles to push cut higher while keeping >=90% winners
print("\n--- 2-feature AND combos ---")
top = singles[:25]
combos = []
for (lc1,_,_,n1,f1,_,_),(lc2,_,_,n2,f2,_,_) in itertools.combinations(top,2):
    if n1.split(">")[0].split("<")[0].split("!")[0] == n2.split(">")[0].split("<")[0].split("!")[0]:
        continue  # skip same feature
    fn = lambda r,a=f1,b=f2: a(r) and b(r)
    kept, kw, kl, wk, lc = eval_filter(fn)
    if wk >= 90.0 and lc > 0:
        n,w,l,wr,stk = stats(kept)
        combos.append((lc, wk, stk, f"({n1}) AND ({n2})", fn, n, wr))
combos.sort(key=lambda x:(-x[0], x[2], -x[1]))
for lc,wk,stk,name,fn,n,wr in combos[:15]:
    print(f"  cut={lc:5.1f}% keepW={wk:5.1f}% n={n:4d} WR={wr:5.1f}% streak={stk}  {name}")

# choose best: maximize losers cut, tie-break lower streak then higher winners kept
pool = []
for lc,wk,stk,name,fn,n,wr in singles:
    pool.append((lc,wk,stk,name,fn,n,wr,1))
for lc,wk,stk,name,fn,n,wr in combos:
    pool.append((lc,wk,stk,name,fn,n,wr,2))

if pool:
    # prefer simplest (fewest features) among near-best cut: rank by cut, then streak, then keepW, then simplicity
    pool.sort(key=lambda x:(-x[0], x[2], -x[1], x[7]))
    best = pool[0]
    lc,wk,stk,name,fn,n,wr,k = best
    kept = [r for r in rows if fn(r)]
    yr = {2024:[0,0],2025:[0,0],2026:[0,0]}
    for r in kept:
        y=r["yr"]
        if y in yr:
            yr[y][1]+=1
            if is_win(r): yr[y][0]+=1
    def ywr(y):
        w,t=yr[y][0],yr[y][1]
        return round(100*w/t,1) if t else None
    print("\n===== CHOSEN FILTER =====")
    print(f"desc: {name}")
    print(f"AFTER: n={n} WR={wr}% maxstreak={stk}")
    print(f"winners_kept_pct={wk} losers_cut_pct={lc}")
    print(f"y24={ywr(2024)} (n={yr[2024][1]})  y25={ywr(2025)} (n={yr[2025][1]})  y26={ywr(2026)} (n={yr[2026][1]})")
    print("RESULT_JSON", json.dumps({
        "before":{"n":N0,"wr":WR0,"maxstreak":ST0},
        "filter":{"desc":name,"n_after":n,"wr_after":wr,"maxstreak_after":stk,
                  "winners_kept_pct":wk,"losers_cut_pct":lc,
                  "y24":ywr(2024),"y25":ywr(2025),"y26":ywr(2026)}}))
else:
    print("\nNENHUM filtro corta loser mantendo >=90% winners")
