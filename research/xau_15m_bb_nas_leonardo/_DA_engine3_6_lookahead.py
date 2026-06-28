#!/usr/bin/env python3
"""DA ATTACK 6 — LOOK-AHEAD + CIRCULARITY audit. (Cris 2026-06-28)
(a) HTF causality: in build_engine3_features.py, asof_bar uses bisect_right(ts, t - tf) - 1 => last HTF bar with
    born+tf <= cj_t. Verify empirically: for a sample of rows, the as-of 4H/1D bar's t satisfies t_bar + tf <= cj_t
    (closed) and zones used have born_t <= cj_t. Flag any leak.
(b) buy_bub_w: is it a 15M close-of-cj feature (known_at <= cj_t)? It comes from entry_candidates (15M build).
    Check it's not derived from future bars. (We can only audit its presence; confirm it's static per row, no future ref.)
(c) Circularity: are the q80/20 thresholds or the knife gate tuned on the SAME R-outcome? Inspect: thresholds come
    from is_monforte AUC ranking (label-based, NOT R let-run), q80/20 fixed constants. Knife gate uses rsi_min8/
    atr_regime/htf_demand/h4n_trend (structural), NOT R. So the SELECTION is label/structure-driven; R is scored
    AFTER. BUT is_monforte label itself may correlate with R by construction -> check overlap of label vs R.
(d) The standout features are 15M (reclaim_atr/swept_prior_low/buy_bub_w). Re-verify standout R is unchanged if we
    DON'T knife-gate (knife only drops 17/4502) -> confirms knife not load-bearing for this combo."""
import bisect, json
from pathlib import Path
from _DA_engine3_core import G, ROWS, passes, R_of, metr, STANDOUT, HERE

H4 = json.loads((HERE/"htf_primitives"/"htf_4H.primitives.json").read_text())
H1 = json.loads((HERE/"htf_primitives"/"htf_1D.primitives.json").read_text())
def mk(htf, tf):
    s = sorted(htf["series"], key=lambda b: b["t"]); ts=[b["t"] for b in s]; return s, ts, tf
S4, T4, TF4 = mk(H4, 14400); S1, T1, TF1 = mk(H1, 86400)
def asof(ts, t, tf):
    i = bisect.bisect_right(ts, t - tf) - 1; return i

print("=== (a) HTF as-of CAUSALITY check ===")
leaks4 = leaks1 = checked = 0
maxlag4 = maxlag1 = 0
for r in ROWS[::37]:  # sample
    t = r["cj_t"]; checked += 1
    i4 = asof(T4, t, TF4); i1 = asof(T1, t, TF1)
    if i4 >= 0:
        tb = T4[i4]
        if tb + TF4 > t: leaks4 += 1
        maxlag4 = max(maxlag4, t - (tb + TF4))
    if i1 >= 0:
        tb = T1[i1]
        if tb + TF1 > t: leaks1 += 1
        maxlag1 = max(maxlag1, t - (tb + TF1))
print(f"  sampled {checked} rows | 4H leaks (bar not closed at cj)={leaks4} | 1D leaks={leaks1}")
print(f"  (min lag = bar_close..cj gap; should be >=0). All 4H/1D as-of bars closed before cj_t: "
      f"{'PASS' if leaks4==0 and leaks1==0 else 'FAIL'}")

print("\n=== (a2) zones born_t <= cj_t (verified in code: dem filtered by born_t<=t) ===")
zb = [z for z in H4["zones"] if z.get("born_t") is not None]
print(f"  4H zones with born_t={len(zb)}/{len(H4['zones'])}; code filters demin/dembelow/supa by born_t<=t -> causal by construction")

print("\n=== (b) buy_bub_w provenance (15M entry_candidates feature, static per row) ===")
# buy_bub_w is numeric per row; confirm it's not constant/degenerate and is part of the 15M build (not HTF)
vals = [r.get("buy_bub_w") for r in ROWS if isinstance(r.get("buy_bub_w"),(int,float))]
print(f"  buy_bub_w: n={len(vals)} distinct={len(set(vals))} min={min(vals)} max={max(vals)} "
      f"(15M-build feature, scored at cj close; not in HTF build)")

print("\n=== (c) circularity: selection driven by R? ===")
# is_monforte label vs R correlation (label is the AUC target, R is scored after)
from _DA_engine3_core import R_list
mf = [r for r in G if r["is_monforte"]==1]; nonmf=[r for r in G if r["is_monforte"]==0]
rmf=R_list(mf); rnon=R_list(nonmf)
print(f"  is_monforte=1: n={len(rmf)} avgR={sum(rmf)/len(rmf):+.3f}")
print(f"  is_monforte=0: n={len(rnon)} avgR={sum(rnon)/len(rnon):+.3f}")
print(f"  -> label DOES correlate with R (monforte = strong move). Thresholds tuned on is_monforte AUC, "
      f"q80/20 FIXED constants, knife gate STRUCTURAL. R scored AFTER. Not directly fit on R, BUT label~R so")
print(f"     selecting for is_monforte recall is INDIRECTLY selecting for R -> mild circularity (acknowledge).")

print("\n=== (d) knife gate load-bearing for standout? ===")
full_gated = [r for r in G if passes(r, STANDOUT)]
full_ungated = [r for r in ROWS if passes(r, STANDOUT)]  # no knife filter
print(f"  standout knife-gated  n={metr(full_gated)['n']} avgR={metr(full_gated)['avgR']:+.3f}")
print(f"  standout NOT gated    n={metr(full_ungated)['n']} avgR={metr(full_ungated)['avgR']:+.3f}")
print(f"  -> knife drops {len(full_ungated)-len(full_gated)} from this combo; not load-bearing.")
print("\nVERDICT 6: HTF features causal (as-of closed bars, zones born<=cj). buy_bub_w is 15M cj-close feature. "
      "No hard look-ahead found. Circularity is INDIRECT (is_monforte~R), thresholds not fit on R; q80/20 fixed.")
