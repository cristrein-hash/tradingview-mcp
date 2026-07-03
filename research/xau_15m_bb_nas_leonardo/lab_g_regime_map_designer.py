#!/usr/bin/env python3
"""LAB G — REGIME-MAP entry system designer (role: MAPA DE REGIME).

Status: EXPLORATORY_CALIBRATION. Materialized per systematic_error_guards hook.
Commit deliberately left to the parent session (no commits from here without authorization).
Adversarial critique (DA) = own inline synthesis by the author of this script, declared as such.

LEDGER (all outcome looks, in order):
  G1  v1 PRIMARY  (depth-first: RANGE k=2 / BULL k=3 / BEAR base, chain-cap3)  -> -23.1R, null pct 4.3% FAIL
  G2  v1 variant (BULL k=4)                                                    -> -11.8R FAIL
  G3  v1 variant (BEAR not-chasing)                                            -> -11.4R FAIL (BEAR cell +9.8R N=3)
  G4  null 1000x regime-freq-matched                                           -> med +24.6R (candidate pool is positive-drift)
  --- ONE declared thesis-level redesign: depth-first -> PROOF-OF-TURN ---
  G5  v2 PRIMARY (proof-of-turn map, day-cap2)                                 -> +51.3R WR48.2% r/DD 4.35 · null pct 84.9%
  G6  v2 nulls / sub-windows / jackknife                                       -> all 4 subwindows +, jackknife robust
  G7  v2-TIGHT (RANGE k=3 / BULL k=3, same core, pre-registered)               -> +7.5R null pct 53.5% REJECTED
      (jackknife minus-top3 negative; k=3 destroys edge -> k=2 retained, no further tuning)
FINAL: single system delivered = v2 PRIMARY. Total outcome looks: 8. BEAR cell = stand-aside recommended.

v2 THESIS: a capitulation flush only pays when the TURN is already proven at cj
(reclaim distance + displacement body + buyer sequence), routed by regime:
  RANGE -> proven turn NOT at box top, with HTF-value backing (mean-revert with proof)
  BULL  -> proven turn on a dip in a healthy nested up-leg (buy recovery of dip, not dip)
  BEAR  -> ONLY g_bear_pullback_ok (CHoCH-up 1H + 1H trend up + reclaim), knife-vetoed
Modulator: g_regime_flip5d==1 -> +1 lens (young regime, map unreliable).
Knife: allowed only with absorption evidence (g_rsi_div or sell_bub_w>=4) — declared.
Exposure governor (viability, frozen pre-outcome): max 2 entries per UTC day.
"""
import json, random, statistics, sys
from collections import Counter, defaultdict

PATH = "/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo/results/lab_g_candidates.jsonl"

def load():
    recs = [json.loads(l) for l in open(PATH)]
    recs.sort(key=lambda r: r["cj_t"])
    return recs

def nz(x, d=0.0): return d if x is None else x

def knife_ok(r):
    return r["g_knife"] == 0 or (r["g_rsi_div"] == 1 or r["sell_bub_w"] >= 4)

# ---------------- v2 frozen predicates ----------------
def proof_of_turn(r):
    """Core anchor: turn already proven at cj (causal, <=cj)."""
    return (r["reclaim_atr"] >= 1.35                      # reclaimed >= ~median ATRs off the flush low
            and (r["g_cj_body"] >= 0.40 or r["up_closes_pc"] >= 3))  # displacement body q75 OR buyer sequence

def conv_lenses(r):
    """Convergence lenses (orthogonal families: absorption / structure-trigger / value / speed)."""
    return [
        r["sell_bub_w"] >= 4 or r["g_rsi_div"] == 1,                        # absorption/divergence (known lift 1.60)
        r["h1n_choch_up_rec"] == 1 or r["nas_long_16"] >= 1,                # structure trigger recently fired
        (r["h1n_in_demand"] == 1) or (r["htf_demand_confluence"] == 1),     # HTF value backing
        r["g_rec_speed"] >= 0.65,                                           # fast recovery (q75)
    ]

def sig_RANGE(r, k=2):
    core = (proof_of_turn(r) and knife_ok(r)
            and r["g_box96"] <= 0.60                    # not at local box top (position as context, not depth-max)
            and r["downleg_eff"] <= 0.33)               # breakdown veto: no efficient one-way leg
    if not core: return False
    return sum(conv_lenses(r)) >= k + (1 if r["g_regime_flip5d"] else 0)

def sig_BULL(r, k=2):
    core = (proof_of_turn(r) and knife_ok(r)
            and r["h1n_trend"] == 1 and r["h4n_trend"] == 1                 # healthy nested up-leg
            and (r["g_ema21_dist"] <= 0.20 or r["in_demand"] == 1))         # dip context: at/below EMA21 or in demand
    if not core: return False
    return sum(conv_lenses(r)) >= k + (1 if r["g_regime_flip5d"] else 0)

def sig_BEAR(r):
    return r["g_bear_pullback_ok"] == 1 and knife_ok(r)

def select(recs, range_k=2, bull_k=2):
    out = []
    for r in recs:
        reg = r["g_v5h"]
        hit = sig_RANGE(r, range_k) if reg == "RANGE" else sig_BULL(r, bull_k) if reg == "BULL" else sig_BEAR(r)
        if hit: out.append(r)
    return out

def day_cap(picks, cap=2):
    out, per_day = [], Counter()
    for r in picks:
        d = r["cj_t"] // 86400
        if per_day[d] < cap:
            per_day[d] += 1
            out.append(r)
    return out

# ---------------- measurement ----------------
def weeks_by_regime(recs):
    wk = defaultdict(Counter)
    for r in recs: wk[r["g_week"]][r["g_v5h"]] += 1
    return Counter({w: c.most_common(1)[0][0] for w, c in wk.items()}.values())

def stats(rs):
    n = len(rs)
    if n == 0: return None
    wr = sum(1 for x in rs if x > 0) / n
    s = sum(rs); avg = s / n
    cum = peak = dd = 0.0
    for x in rs:
        cum += x; peak = max(peak, cum); dd = max(dd, peak - cum)
    streak = worst = 0
    for x in rs:
        streak = streak + 1 if x <= 0 else 0
        worst = max(worst, streak)
    return n, wr, s, avg, dd, (s / dd if dd > 0 else float("inf")), worst

def panel(picks, label, nweeks, sb=0.80):
    Rs = [r["g_R"] for r in picks]
    Rn = [r["g_R"] - sb / max(r["g_risk"], 1e-9) for r in picks]
    n, wr, s, avg, dd, rdd, st = stats(Rs)
    print(f"\n== {label} == N={n} WR={wr:.1%} sumR={s:+.1f} avgR={avg:+.3f} maxDD={dd:.1f}R r/DD={rdd:.2f} streak={st}")
    n2, wr2, s2, avg2, dd2, rdd2, st2 = stats(Rn)
    print(f"   SB$0.80: WR={wr2:.1%} sumR={s2:+.1f} avgR={avg2:+.3f} maxDD={dd2:.1f} r/DD={rdd2:.2f} streak={st2}")
    for yr in sorted(set(r["yr"] for r in picks)):
        rs = [r["g_R"] for r in picks if r["yr"] == yr]
        print(f"   {yr}: N={len(rs)} WR={sum(1 for x in rs if x>0)/len(rs):.0%} sumR={sum(rs):+.1f}")
    for reg in ["RANGE", "BULL", "BEAR"]:
        sub = [r for r in picks if r["g_v5h"] == reg]
        if sub:
            rs = [r["g_R"] for r in sub]
            print(f"   {reg}: N={len(sub)} ({len(sub)/nweeks[reg]:.2f}/regime-wk) WR={sum(1 for x in rs if x>0)/len(rs):.0%} "
                  f"sumR={sum(rs):+.1f} avgR={sum(rs)/len(rs):+.3f}")
    wc = Counter(r["g_week"] for r in picks)
    print(f"   freq: {n/104:.2f}/wk overall · max/wk {max(wc.values())} · in_base435 overlap {sum(r['g_in_base435'] for r in picks)}")
    return Rs

def validate(recs, picks, Rs, tag):
    random.seed(11)
    byreg = defaultdict(list)
    for r in recs: byreg[r["g_v5h"]].append(r)
    nper = Counter(r["g_v5h"] for r in picks)
    sums, avgs = [], []
    for _ in range(1000):
        ps = []
        for reg, n in nper.items(): ps += random.sample(byreg[reg], n)
        ps.sort(key=lambda r: r["cj_t"]); ps = day_cap(ps, 2)
        rr = [p["g_R"] for p in ps]; sums.append(sum(rr)); avgs.append(sum(rr) / len(rr))
    sums.sort(); avgs.sort()
    import bisect
    ps_, pa_ = sum(Rs), sum(Rs) / len(Rs)
    print(f"\n[{tag}] NULL(1000 regime-freq-matched, day-cap2): sum med {statistics.median(sums):+.1f} p95 {sums[949]:+.1f} "
          f"| avg med {statistics.median(avgs):+.3f} p95 {avgs[949]:+.3f}")
    print(f"[{tag}] observed percentile: sumR {100*bisect.bisect_left(sums,ps_)/1000:.1f}% avgR {100*bisect.bisect_left(avgs,pa_)/1000:.1f}%")
    ts = sorted(r["cj_t"] for r in recs); qs = [ts[int(i*(len(ts)-1)/4)] for i in range(5)]
    for i in range(4):
        rs = [r["g_R"] for r in picks if qs[i] <= r["cj_t"] <= qs[i+1]]
        if rs: print(f"[{tag}] subwindow Q{i+1}: N={len(rs)} WR={sum(1 for x in rs if x>0)/len(rs):.0%} sumR={sum(rs):+.1f}")
    wkR = defaultdict(float)
    for r in picks: wkR[r["g_week"]] += r["g_R"]
    tot = sum(wkR.values()); top3 = sorted(wkR.values(), reverse=True)[:3]
    print(f"[{tag}] jackknife-week: total {tot:+.1f} · minus best {tot-top3[0]:+.1f} · minus top3 {tot-sum(top3):+.1f}")

if __name__ == "__main__":
    recs = load()
    nweeks = weeks_by_regime(recs)
    mode = sys.argv[1] if len(sys.argv) > 1 else "freq"
    if mode == "tight":
        picks = day_cap(select(recs, range_k=3, bull_k=3), 2)
        Rs = panel(picks, "v2-TIGHT (RANGE k=3 / BULL k=3 / BEAR base, day-cap2)", nweeks)
        validate(recs, picks, Rs, "v2-tight")
        sys.exit(0)
    raw = select(recs)
    picks = day_cap(raw, 2)
    if mode == "freq":
        c = Counter(r["g_v5h"] for r in picks)
        print("v2 frequency (day-cap2):", {k: (v, round(v / nweeks[k], 2)) for k, v in sorted(c.items())},
              "| total", len(picks), f"({len(picks)/104:.2f}/wk)")
    else:
        Rs = panel(picks, "v2 PRIMARY (proof-of-turn map, RANGE k=2 / BULL k=2 / BEAR base, day-cap2)", nweeks)
        validate(recs, picks, Rs, "v2")
