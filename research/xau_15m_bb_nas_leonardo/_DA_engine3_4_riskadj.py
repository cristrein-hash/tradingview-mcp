#!/usr/bin/env python3
"""DA ATTACK 4 — RISK-ADJUSTED vs take-all AND vs random-same-n. (Cris 2026-06-28)
take-all avgR +0.105 DD-125 (n4482); combo avgR +0.206 DD-15.6 (n386). Compute return/DD and sumR/trade.
Is combo genuinely better risk-adjusted, or just smaller-n lower-DD trivially? Is sumR +79 meaningfully better
than 386 random (+~40)? Random-same-n null for sumR AND for maxDD (DD shrinks with n trivially).
CRITICAL marginal test: does adding swept_prior_low + buy_bub_w beat reclaim_atr ALONE? (is the confluence real?)"""
import random, statistics as stt
from _DA_engine3_core import G, passes, R_of, metr, R_list, STANDOUT, dirn, TH

Rall = R_list(G)
n_all = len(Rall)
full = [r for r in G if passes(r, STANDOUT)]
mc = metr(full); nc = mc["n"]

def maxdd(rs):
    eq = pk = dd = 0
    for x in rs: eq += x; pk = max(pk, eq); dd = min(dd, eq - pk)
    return dd

print("=== absolute risk metrics ===")
print(f"TAKE-ALL : n={n_all} sumR={sum(Rall):.1f} avgR={sum(Rall)/n_all:+.3f} "
      f"maxDD={maxdd(Rall):.1f} ret/DD={sum(Rall)/abs(maxdd(Rall)):.2f} sumR/trade={sum(Rall)/n_all:+.3f}")
print(f"COMBO    : n={nc} sumR={mc['sumR']:.1f} avgR={mc['avgR']:+.3f} "
      f"maxDD={mc['maxDD']:.1f} ret/DD={mc['sumR']/abs(mc['maxDD']):.2f} sumR/trade={mc['avgR']:+.3f}")

# random-same-n null for sumR, avgR, maxDD, ret/DD
K = 5000; random.seed(21)
s_sum=[]; s_avg=[]; s_dd=[]; s_rdd=[]
for _ in range(K):
    samp = random.sample(Rall, nc)
    s = sum(samp); d = maxdd(samp)
    s_sum.append(s); s_avg.append(s/nc); s_dd.append(d); s_rdd.append(s/abs(d) if d!=0 else 0)
def pct(arr, v, ge=True):
    return (sum(1 for x in arr if (x>=v if ge else x<=v)))/len(arr)
print(f"\n=== random-same-n (n={nc}) null over {K} draws ===")
print(f"sumR   : null mean={stt.mean(s_sum):+.1f} p95={sorted(s_sum)[int(.95*K)]:+.1f}  "
      f"P(random sumR >= {mc['sumR']:+.1f}) = {pct(s_sum,mc['sumR']):.4f}")
print(f"avgR   : null mean={stt.mean(s_avg):+.3f} p95={sorted(s_avg)[int(.95*K)]:+.3f}  "
      f"P(random avgR >= {mc['avgR']:+.3f}) = {pct(s_avg,mc['avgR']):.4f}")
print(f"maxDD  : null mean={stt.mean(s_dd):.1f}  combo maxDD={mc['maxDD']:.1f} "
      f"(combo BETTER iff shallower; P(random DD shallower than combo)={pct(s_dd, mc['maxDD']):.4f})")
print(f"ret/DD : null mean={stt.mean(s_rdd):+.2f}  combo ret/DD={mc['sumR']/abs(mc['maxDD']):+.2f}  "
      f"P(random ret/DD >= combo) = {pct(s_rdd, mc['sumR']/abs(mc['maxDD'])):.4f}")

# MARGINAL: reclaim_atr alone vs +swept vs +bub
print("\n=== marginal value of the confluence (does adding features beat reclaim_atr alone?) ===")
for cc in [("reclaim_atr",), ("reclaim_atr","swept_prior_low"), ("reclaim_atr","buy_bub_w"),
           ("reclaim_atr","swept_prior_low","buy_bub_w"), ("swept_prior_low",), ("buy_bub_w",),
           ("swept_prior_low","buy_bub_w")]:
    sel=[r for r in G if passes(r,cc)]; m=metr(sel)
    print(f"  {'+'.join(cc):<46} n={m['n']:>4} WR={m['WR']:>4} sumR={m['sumR']:+6.1f} avgR={m['avgR']:+.3f} DD={m['maxDD']:.1f}")
print("\nVERDICT 4: combo is genuinely risk-adj-better only if avgR/sumR beat random-same-n AND the extra features "
      "add value over reclaim_atr alone. Lower DD at smaller n is trivial (DD shrinks with sqrt(n)).")
