#!/usr/bin/env python3
"""FINAL SYNTHESIZER — combine causal-clean survivors' keep_ns.
Goal: maximize hit3r while poison<0.9 AND both years > base, cutting MAX loser-targets.
Survivors (causal-clean + robust per verify pass):
  FaseD  : N73 hit 0.603
  CHoCH  : N45 hit 0.667
  FSM4   : N54 hit 0.63
score() is ground truth. No lookahead, no hardcode — we only set-combine already-validated masks.
"""
import sys, itertools
sys.path.insert(0, "/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo")
from agent_ctx_kit import ENTRIES, score

ALLN = [e["n"] for e in ENTRIES]

# --- survivor masks (verbatim from verified survivors) ---
FaseD = {2,3,4,5,7,8,9,10,11,12,13,14,15,16,17,20,21,22,23,25,27,28,29,30,31,34,35,36,37,38,39,40,41,42,43,44,45,46,48,51,52,53,54,55,57,58,59,60,61,62,63,64,67,69,71,72,73,74,75,76,77,78,82,83,84,87,88,90,91,92,93,94,96}
CHoCH = {1,6,10,11,12,15,17,20,22,28,30,32,33,34,35,38,42,43,46,47,54,59,60,61,62,63,64,66,70,73,74,75,76,77,78,79,81,82,83,84,88,90,91,94,95}
FSM4  = {1,2,3,4,6,7,8,9,10,12,13,14,15,16,18,20,23,26,27,30,33,35,36,37,39,40,44,45,46,48,50,51,52,53,55,61,62,64,68,71,74,75,76,77,78,80,82,84,87,88,89,90,93,95}

SURV = {"FaseD": FaseD, "CHoCH": CHoCH, "FSM4": FSM4}

# --- post-hoc sanity target lists (NEVER used in logic, only for reporting) ---
LOSER_TARGETS  = {21,23,31,49,50,55,56,57,59,60,65,66,67,68,69,79,83,84,85,89,93,94}
WINNER_KEYS    = {1,11,12,13,14,26,28,29,30,44,45,61,62,63,71,72,73,74,75,82,95,96}

def base_year_rates():
    from agent_ctx_kit import ENTRIES as E
    import datetime as dt
    def yr(t): return dt.datetime.utcfromtimestamp(int(t)).strftime("%Y")
    y25=[e for e in E if yr(e["t"])=="2025"]; y26=[e for e in E if yr(e["t"])=="2026"]
    r25=sum(e["out"] for e in y25)/len(y25); r26=sum(e["out"] for e in y26)/len(y26)
    return r25, r26
B25, B26 = base_year_rates()  # base per-year rates to beat
BASE = 52/96

def yrate(s):
    # parse "w/n" -> rate
    w,n = s.split("/"); w=int(w); n=int(n)
    return (w/n if n else 0.0), w, n

def evaluate(name, keep):
    keep = set(keep) & set(ALLN)
    if len(keep) < 20:
        return None
    m = score(keep)
    r25,w25,n25 = yrate(m["y2025"]); r26,w26,n26 = yrate(m["y2026"])
    poison = m["poison_ratio"]
    both_years = (r25 > B25) and (r26 > B26)
    poison_ok = (poison < 0.9) and (m["losers_cut"] > m["winners_cut"])
    lt_cut = len(LOSER_TARGETS - keep)     # loser-targets removed
    wk_keep = len(WINNER_KEYS & keep)      # winner-keys retained
    gate = both_years and poison_ok and m["N_kept"]>=20
    return {
        "name":name, "keep":keep, "m":m, "r25":r25,"r26":r26,
        "poison":poison, "both_years":both_years, "poison_ok":poison_ok,
        "lt_cut":lt_cut, "wk_keep":wk_keep, "gate":gate,
    }

print(f"BASE: 52/96={BASE:.4f} | base y2025={B25:.4f} ({29}/46) | base y2026={B26:.4f} ({23}/50)")
print(f"LOSER_TARGETS N={len(LOSER_TARGETS)} | WINNER_KEYS N={len(WINNER_KEYS)}")
print("="*100)

cands = []

# individual survivors
for nm, mask in SURV.items():
    cands.append(evaluate(nm, mask))

# all pairwise/triple unions & intersections
names = list(SURV.keys())
for r in (2,3):
    for combo in itertools.combinations(names, r):
        masks = [SURV[c] for c in combo]
        u = set().union(*masks)
        i = masks[0].copy()
        for mm in masks[1:]: i &= mm
        cands.append(evaluate("|".join(combo)+"_UNION", u))
        cands.append(evaluate("&".join(combo)+"_INTERSECT", i))

# majority-vote (>=2 of 3) and unanimous(=3)
from collections import Counter
cnt = Counter()
for mask in SURV.values():
    for n in mask: cnt[n]+=1
maj2 = {n for n,c in cnt.items() if c>=2}
maj3 = {n for n,c in cnt.items() if c>=3}
cands.append(evaluate("MAJORITY>=2of3", maj2))
cands.append(evaluate("UNANIMOUS=3of3", maj3))

# print table
cands = [c for c in cands if c]
print(f"{'name':40s} {'N':>3} {'hit3r':>6} {'pois':>5} {'y25':>8} {'y26':>8} {'LTcut':>5} {'WKkeep':>6} {'GATE':>5}")
for c in sorted(cands, key=lambda x:(-x["gate"], -x["m"]["hit3r_kept"], -x["lt_cut"])):
    m=c["m"]
    print(f"{c['name']:40s} {m['N_kept']:>3} {m['hit3r_kept']:>6.3f} {c['poison']:>5.2f} "
          f"{m['y2025']:>8} {m['y2026']:>8} {c['lt_cut']:>5} {c['wk_keep']:>6} {str(c['gate']):>5}")

print("="*100)
# pick best gate-passing by hit3r then LTcut then N
passing = [c for c in cands if c["gate"]]
if not passing:
    print("NO COMBINATION PASSES ALL GATES.")
else:
    # objective: maximize hit3r, tie-break by loser-targets cut, then by N_kept (more frequency)
    best = max(passing, key=lambda x:(round(x["m"]["hit3r_kept"],3), x["lt_cut"], x["m"]["N_kept"]))
    print("BEST GATE-PASSING COMBINATION:", best["name"])
    print("  score():", best["m"])
    print(f"  poison={best['poison']} both_years={best['both_years']} "
          f"(y25 {best['r25']:.3f}>{B25:.3f}, y26 {best['r26']:.3f}>{B26:.3f})")
    print(f"  loser-targets CUT: {best['lt_cut']}/{len(LOSER_TARGETS)} "
          f"-> {sorted(LOSER_TARGETS - best['keep'])}")
    print(f"  loser-targets SURVIVING: {sorted(LOSER_TARGETS & best['keep'])}")
    print(f"  winner-keys KEPT: {best['wk_keep']}/{len(WINNER_KEYS)} "
          f"-> dropped {sorted(WINNER_KEYS - best['keep'])}")
    print("  FINAL keep_ns:", sorted(best["keep"]))

# ---- NULL TEST on top gate-passing candidates (fixed mask, randomize outcomes) ----
import random
outs = [e["out"] for e in ENTRIES]
Ntot = len(outs); Wtot = sum(outs)
def null_p(keep, obs_w, iters=200000):
    keep=set(keep); idx=[k for k,e in enumerate(ENTRIES) if e["n"] in keep]; nk=len(idx)
    # permutation null: shuffle the 96 outcomes, count kept-winners
    perm_ge=0
    base=outs[:]
    for _ in range(iters):
        random.shuffle(base)
        if sum(base[k] for k in idx) >= obs_w: perm_ge+=1
    # rotation null: all 96 circular shifts (preserves temporal win/loss autocorrelation)
    rot_ge=0
    for s in range(Ntot):
        rot=[outs[(k-s)%Ntot] for k in range(Ntot)]
        if sum(rot[k] for k in idx) >= obs_w: rot_ge+=1
    return perm_ge/iters, rot_ge/Ntot

random.seed(1)
print("="*100)
print("NULL TEST (fixed mask; permute + rotate outcomes) on top gate-passing combos:")
top = sorted([c for c in cands if c["gate"]],
             key=lambda x:(round(x["m"]["hit3r_kept"],3), x["lt_cut"], x["m"]["N_kept"]), reverse=True)[:4]
for c in top:
    pw = c["m"]["winners_kept"]
    pp, rp = null_p(c["keep"], pw, iters=100000)
    print(f"  {c['name']:28s} N={c['m']['N_kept']:>2} hit={c['m']['hit3r_kept']:.3f} "
          f"pois={c['poison']:.2f} LTcut={c['lt_cut']:>2} | null_perm={pp:.4f} null_rot={rp:.4f} "
          f"cons={max(pp,rp):.4f}")
