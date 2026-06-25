#!/usr/bin/env python3
"""DEVIL'S ADVOCATE — audit of l2_bpt_bearleg_surgical.py.
Does NOT modify surgical files. Tests whether the 'oversold-flush / clean-sky' signature
(rsi_min8<=35 OR drop20>=2 OR clean_sky) is STRUCTURAL (marks runners across the full 276 and
on non-bear-leg episodes) or OVERFIT to the 5 bear-leg runners.
Also: Fisher exact on the in-sample 60% vs 21% claim, and uncapped sumR economics of
blind-block vs refined-block vs no-block on the bear_leg universe.
Run from v1/ dir (same cwd convention as l2_bpt_bearleg_surgical.py): python3 results/_DA_bearleg_signature_generalization.py
Causal: rsi_min8/drop20 are packet features at bar i; clean_sky from decisions at bar i. No forward leak.
"""
import csv, json, math
D = "results"; RR = "repro_recovery"

pk = {int(json.loads(l)['bar_idx']): json.loads(l) for l in open(f"{RR}/qual_packets.jsonl")}
unc = {int(r['bar_idx']): r for r in csv.DictReader(open(f"{D}/l2_bpt_uncapped_or_proxy_outcomes_276.csv"))}
dec = {int(r['bar_idx']): r for r in csv.DictReader(open(f"{D}/l2_bpt_full276_macro_bear_v3_decisions.csv"))}


def fn(v):
    try:
        return float(v)
    except Exception:
        return None


EP = sorted(unc)
MFE = {b: fn(unc[b]['mfe_R']) for b in EP}
RUN = lambda b: MFE[b] >= 5
LOS = lambda b: MFE[b] < 2
MON = lambda b: MFE[b] >= 10

BL = [b for b in EP if dec.get(b, {}).get('macro_reader_leg') == 'MACRO_BEAR_LEG']
NONBL = [b for b in EP if b not in set(BL)]


# --- the signature, exactly as in the surgical script (runsig auto-selected there = these 3) ---
def sig_oversold(b):
    return (fn(pk.get(b, {}).get('rsi_min8')) or 99) <= 35


def sig_flush(b):
    return (fn(pk.get(b, {}).get('drop20_atr')) or 0) >= 2


def sig_cleansky(b):
    return dec.get(b, {}).get('clean_sky_flag') == 'True'


def sig_any(b):
    return sig_oversold(b) or sig_flush(b) or sig_cleansky(b)


def fisher_exact_2x2(a, b, c, d):
    """Two-sided Fisher exact p for table [[a,b],[c,d]]. Pure python."""
    def logC(n, k):
        return math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)
    n = a + b + c + d
    r1, r2 = a + b, c + d
    c1, c2 = a + c, b + d
    def p_table(x):
        # x = a; fix margins
        return math.exp(logC(r1, x) + logC(r2, c1 - x) - logC(n, c1))
    p_obs = p_table(a)
    lo = max(0, c1 - r2)
    hi = min(r1, c1)
    p = 0.0
    for x in range(lo, hi + 1):
        pt = p_table(x)
        if pt <= p_obs * 1.0000001:
            p += pt
    return min(1.0, p)


def runner_rate(group):
    if not group:
        return 0.0, 0, 0
    r = sum(1 for b in group if RUN(b))
    return r / len(group), r, len(group)


def lift_over_base(group, base):
    rr, _, _ = runner_rate(group)
    return rr / base if base > 0 else 0.0


print("=" * 88)
print("DA — BEAR_LEG OVERSOLD-FLUSH SIGNATURE: STRUCTURAL OR OVERFIT-TO-5?")
print("=" * 88)

base_run, nrun_all, _ = runner_rate(EP)
print(f"Base 276: runners(MFE>=5)={nrun_all} ({100*base_run:.1f}%) | bear_leg n={len(BL)} | non-bear_leg n={len(NONBL)}")

# Q1 — in-sample Fisher: 60% (3/5) oversold-runner vs 21% (4/19) oversold-loser  within bear_leg
bl_run = [b for b in BL if RUN(b)]
bl_los = [b for b in BL if LOS(b)]
for name, fnc in [("rsi_min8<=35", sig_oversold), ("drop20>=2", sig_flush), ("clean_sky", sig_cleansky)]:
    a = sum(1 for b in bl_run if fnc(b))      # runners with sig
    bb = len(bl_run) - a                       # runners without
    c = sum(1 for b in bl_los if fnc(b))       # losers with sig
    dd = len(bl_los) - c                        # losers without
    rr = a / len(bl_run) if bl_run else 0
    lr = c / len(bl_los) if bl_los else 0
    p = fisher_exact_2x2(a, bb, c, dd)
    print(f"  IN-SAMPLE {name:14}: runner {a}/{len(bl_run)}={100*rr:.0f}%  loser {c}/{len(bl_los)}={100*lr:.0f}%  Fisher p={p:.3f}")

# Q3 — STRUCTURAL TEST: does the same signature lift runner-rate on the FULL 276 and on NON-bear-leg?
print("\nQ3 — SIGNATURE GENERALIZATION (runner-lift outside the 5 fitted points):")
for label, group in [("FULL 276", EP), ("non-bear_leg", NONBL), ("bear_leg", BL)]:
    sig_grp = [b for b in group if sig_any(b)]
    nosig_grp = [b for b in group if not sig_any(b)]
    rr_sig, ns, ts = runner_rate(sig_grp)
    rr_no, nn, tn = runner_rate(nosig_grp)
    lift = rr_sig / base_run if base_run > 0 else 0
    # 2x2 sig vs runner within this group
    a = sum(1 for b in sig_grp if RUN(b)); bb = len(sig_grp) - a
    c = sum(1 for b in nosig_grp if RUN(b)); dd = len(nosig_grp) - c
    p = fisher_exact_2x2(a, bb, c, dd) if (sig_grp and nosig_grp) else 1.0
    print(f"  {label:14}: sig-grp runner {ns}/{ts}={100*rr_sig:.0f}% (lift vs base {lift:.2f})  |  no-sig {nn}/{tn}={100*rr_no:.0f}%  Fisher p={p:.4f}")

# per-component generalization on full 276
print("\n  per-component runner-lift on FULL 276:")
for name, fnc in [("rsi_min8<=35", sig_oversold), ("drop20>=2", sig_flush), ("clean_sky", sig_cleansky)]:
    g = [b for b in EP if fnc(b)]
    rr, nr, tr = runner_rate(g)
    print(f"    {name:14}: {nr}/{tr}={100*rr:.0f}%  lift {rr/base_run:.2f}")

# Q4 — economics: uncapped let-run sumR on bear_leg universe under 3 policies.
# Proxy for 'realized if taken': use mfe_R is wrong (it's max favorable, not realized).
# Use realized_letrun_120 if present else realized_letrun_60 else max_run_R as uncapped let-run realized.
def letrun(b):
    r = unc[b]
    for k in ('realized_letrun_120', 'realized_letrun_60', 'max_run_R', 'mfe_R'):
        v = fn(r.get(k))
        if v is not None:
            return v
    return 0.0


bl_sumR = sum(letrun(b) for b in BL)
refined_taken = [b for b in BL if sig_any(b)]
refined_sumR = sum(letrun(b) for b in refined_taken)
print("\nQ4 — UNCAPPED let-run economics on bear_leg universe (realized_letrun proxy):")
print(f"  let-run field used = realized_letrun_120 (fallback chain). n bear_leg={len(BL)}")
print(f"  NO-BLOCK (take all bear_leg):     sumR={bl_sumR:+.1f}  over n={len(BL)}")
print(f"  BLIND-BLOCK (take none):          sumR=  +0.0  over n=0")
print(f"  REFINED-BLOCK (take {len(refined_taken)} legit): sumR={refined_sumR:+.1f}  over n={len(refined_taken)}")
print(f"  refined avg/trade = {refined_sumR/len(refined_taken) if refined_taken else 0:+.2f}R  | no-block avg = {bl_sumR/len(BL):+.2f}R")
# what the refined rule actually keeps vs drops
keep_run = sum(1 for b in BL if sig_any(b) and RUN(b))
keep_los = sum(1 for b in BL if sig_any(b) and LOS(b))
drop_run = sum(1 for b in BL if not sig_any(b) and RUN(b))
drop_los = sum(1 for b in BL if not sig_any(b) and LOS(b))
print(f"  refined keeps: runners={keep_run} losers={keep_los} | refined drops: runners={drop_run} losers={drop_los}")

print("\nDONE _DA_bearleg_signature_generalization.")
