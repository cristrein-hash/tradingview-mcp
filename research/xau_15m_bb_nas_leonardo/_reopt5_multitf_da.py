"""_reopt5_multitf_da.py — Devil's Advocate on the MULTI-TF finalists.

Adversarial checks for the re-derived R2 (5ATR) filters:
  F1 = CUT h1_pos<=0.65            (single, 8/8 blocks)
  F2 = CUT h1_pos<=0.70 OR h1_dist<=1.85   (best robust WR)
  F3 = CUT dist_supply_atr<=-0.26  (orthogonal location, best streak)
  F4 = CUT h1_pos<=0.65 OR dist_supply_atr<=-0.26  (multi-TF + orthogonal stack)

Checks:
  1. Leave-one-block-out jackknife: recompute wr_keep dropping each block;
     does the lift over (that-subset base) hold every time? (no single-block carry)
  2. Threshold jitter +/-20%: knife-edge test.
  3. Winners cut audit: how many winners removed, are they monumental (R high)?
  4. Look-ahead note: all features = bars already closed (RAW-causal per spec).
PROIBIDO R/win/cj/low_idx as feature (R only used for outcome audit, not selection).
"""
from _reopt5_lib import load, metrics, BASE_WR

rows = load()


def keep_F1(r):
    return not (r["h1_pos"] is not None and r["h1_pos"] <= 0.65)


def keep_F2(r):
    return not ((r["h1_pos"] is not None and r["h1_pos"] <= 0.70) or
                (r["h1_dist"] is not None and r["h1_dist"] <= 1.85))


def keep_F3(r):
    return not (r["dist_supply_atr"] is not None and r["dist_supply_atr"] <= -0.26)


def keep_F4(r):
    return not ((r["h1_pos"] is not None and r["h1_pos"] <= 0.65) or
                (r["dist_supply_atr"] is not None and r["dist_supply_atr"] <= -0.26))


FILTERS = {"F1_h1pos65": keep_F1, "F2_h1pos70_or_dist": keep_F2,
           "F3_into_supply": keep_F3, "F4_h1pos_or_supply": keep_F4}

BLOCKS = sorted(set(r["block"] for r in rows))


def wr(rs):
    return 100.0 * sum(r["win"] for r in rs) / len(rs) if rs else 0.0


print(f"BASE_WR={BASE_WR}  N={len(rows)}\n")

for name, keep in FILTERS.items():
    print("=" * 66)
    print(name)
    full = [r for r in rows if keep(r)]
    m = metrics(full, rows)
    print(f"  full: wr_keep={m['wr_keep']} n={m['n_keep']} win%={m['winners_kept_pct']} "
          f"lcut%={m['losers_cut_pct']} streak={m['streak_base']}->{m['streak_keep']}")

    # 1) leave-one-block-out
    print("  -- leave-one-block-out jackknife (lift = keptWR - subsetBaseWR) --")
    min_lift = 99
    n_pos = 0
    for drop in BLOCKS:
        sub = [r for r in rows if r["block"] != drop]
        sub_base = wr(sub)
        sub_keep = [r for r in sub if keep(r)]
        lift = wr(sub_keep) - sub_base
        min_lift = min(min_lift, lift)
        if lift > 0:
            n_pos += 1
        print(f"     drop {drop}: keptWR={wr(sub_keep):.2f} subBase={sub_base:.2f} lift={lift:+.2f}")
    print(f"     -> min_lift={min_lift:+.2f}  positive_lift {n_pos}/8")

    # 3) winners cut audit (R distribution of removed winners)
    cut = [r for r in rows if not keep(r)]
    cut_winners = [r for r in cut if r["win"] == 1]
    if cut_winners:
        rs = sorted(r["R"] for r in cut_winners)
        big = sum(1 for x in rs if x >= 3.0)
        print(f"  -- winners cut: {len(cut_winners)} (avgR={sum(rs)/len(rs):.2f} "
              f"maxR={max(rs):.1f}  >=3R: {big})")


# 2) threshold jitter on F1 (the cleanest single)
print("\n" + "=" * 66)
print("THRESHOLD JITTER — F1 h1_pos cut, t in 0.55..0.80")
for t in [0.55, 0.60, 0.65, 0.70, 0.75, 0.80]:
    k = [r for r in rows if not (r["h1_pos"] is not None and r["h1_pos"] <= t)]
    m = metrics(k, rows)
    print(f"  t={t}: wr={m['wr_keep']} win%={m['winners_kept_pct']} "
          f"lcut%={m['losers_cut_pct']} blk={m['blocks_ok']}/8 streak->{m['streak_keep']} "
          f"yr={m['by_year']}")
