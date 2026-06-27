#!/usr/bin/env python3
"""
DA verification (recalibrated) of F2 5ATR filter.

RULE under test:
  CUT (skip) the trade when  h1_pos <= 0.70  OR  h1_dist <= 1.85
  KEEP otherwise.
  Rationale: loser = 15M entry with NO drive (price low in h1 swing-range
  and/or hugging h1 EMA). Carrier of multi-TF R2 = POSITION (h1_pos/h1_dist).

DA regua: do NOT veto for tail/WR-only/no-OOS. VETO only for:
  - look-ahead (feature uses future/outcome / unclosed HTF bar / bubbles known_at)
  - non-stationarity: WR-after by YEAR worse than YEAR-BASE, OR >2/8 blocks worse
  - cuts winners (winners_kept < 85%)
  - cherry-pick (neighborhood +/-20% collapses)

Outputs WR before/after total + per year + per block, streak, winners_kept.
"""
import json
from collections import Counter, defaultdict

ROWS = [json.loads(l) for l in open(
    "/Users/cristrein/tradingview-mcp/research/xau_15m_bb_nas_leonardo/dataset_5atr.jsonl")]

POS_THR = 0.70
DIST_THR = 1.85


def keep(r, pos=POS_THR, dist=DIST_THR):
    """KEEP = not cut. Cut if h1_pos<=pos OR h1_dist<=dist."""
    p = r.get("h1_pos")
    d = r.get("h1_dist")
    if p is None or d is None:
        # missing h1 -> cannot evaluate gate; treat as KEEP (gate inactive)
        return True
    cut = (p <= pos) or (d <= dist)
    return not cut


def wr(rows):
    if not rows:
        return None
    return 100.0 * sum(x["win"] for x in rows) / len(rows)


def max_win_streak(rows):
    """rows in chronological order; longest run of win==1."""
    best = cur = 0
    for r in rows:
        if r["win"] == 1:
            cur += 1
            best = max(best, cur)
        else:
            cur = 0
    return best


def main():
    rows = sorted(ROWS, key=lambda r: (r["block"], r["low_t"]))
    n = len(rows)

    kept = [r for r in rows if keep(r)]
    cut = [r for r in rows if not keep(r)]

    base_wr = wr(rows)
    keep_wr = wr(kept)

    print(f"=== TOTAL ===")
    print(f"n base={n}  WR base={base_wr:.2f}")
    print(f"n keep={len(kept)}  WR keep={keep_wr:.2f}  (delta {keep_wr-base_wr:+.2f}pp)")
    print(f"n cut={len(cut)}  WR cut={wr(cut):.2f}")

    # winners kept
    tot_winners = sum(r["win"] for r in rows)
    kept_winners = sum(r["win"] for r in kept)
    wkp = 100.0 * kept_winners / tot_winners
    print(f"winners total={tot_winners}  winners kept={kept_winners}  winners_kept%={wkp:.2f}")
    losers = n - tot_winners
    losers_cut = len([r for r in cut if r["win"] == 0])
    print(f"losers total={losers}  losers cut={losers_cut}  losers_cut%={100.0*losers_cut/losers:.2f}")

    # big winners >=3R cut
    big_cut = [r for r in cut if r["R"] >= 3.0]
    print(f"winners >=3R cut: {len(big_cut)}")

    # streak
    print(f"streak base={max_win_streak(rows)}  streak keep={max_win_streak(kept)}")

    # per year
    print("\n=== PER YEAR (base WR vs keep WR) ===")
    yrs = sorted(set(r["yr"] for r in rows))
    year_fail = 0
    for y in yrs:
        b = [r for r in rows if r["yr"] == y]
        k = [r for r in kept if r["yr"] == y]
        bw, kw = wr(b), wr(k)
        flag = "WORSE" if kw < bw else "ok"
        if kw < bw:
            year_fail += 1
        print(f"  {y}: base={bw:.2f} keep={kw:.2f} delta={kw-bw:+.2f} n_keep={len(k)} [{flag}]")

    # per block
    print("\n=== PER BLOCK (base WR vs keep WR) ===")
    blocks = sorted(set(r["block"] for r in rows))
    block_fail = 0
    for blk in blocks:
        b = [r for r in rows if r["block"] == blk]
        k = [r for r in kept if r["block"] == blk]
        bw, kw = wr(b), (wr(k) if k else float('nan'))
        worse = (k and kw < bw)
        if worse:
            block_fail += 1
        flag = "WORSE" if worse else "ok"
        print(f"  {blk}: base={bw:.2f} keep={kw:.2f} delta={(kw-bw) if k else float('nan'):+.2f} n_keep={len(k)} [{flag}]")
    print(f"\nyears worse: {year_fail}/{len(yrs)}   blocks worse: {block_fail}/{len(blocks)}")

    # neighborhood +/-20% (cherry-pick test)
    print("\n=== NEIGHBORHOOD +/-20% (cherry-pick) ===")
    base_kw = keep_wr
    nb = []
    for pf in (0.8, 0.9, 1.0, 1.1, 1.2):
        for df in (0.8, 0.9, 1.0, 1.1, 1.2):
            p = POS_THR * pf
            d = DIST_THR * df
            k = [r for r in rows if keep(r, p, d)]
            kw = wr(k)
            wkp_n = 100.0 * sum(r["win"] for r in k) / tot_winners
            nb.append((round(p, 3), round(d, 3), round(kw, 2), round(wkp_n, 1), len(k)))
    for p, d, kw, wkpn, nk in nb:
        marker = "<-- center" if (abs(p-POS_THR) < 1e-6 and abs(d-DIST_THR) < 1e-6) else ""
        print(f"  pos={p} dist={d}: WR={kw} winners_kept%={wkpn} n={nk} {marker}")
    kws = [x[2] for x in nb]
    print(f"neighborhood WR range: {min(kws):.2f} .. {max(kws):.2f}  (center {base_kw:.2f})")

    # jackknife per block (drop each block, recompute keep WR delta)
    print("\n=== JACKKNIFE (drop 1 block, keep-WR delta vs base-of-remaining) ===")
    jk_pos = 0
    for blk in blocks:
        sub = [r for r in rows if r["block"] != blk]
        k = [r for r in sub if keep(r)]
        d = wr(k) - wr(sub)
        if d > 0:
            jk_pos += 1
        print(f"  drop {blk}: delta={d:+.2f}pp")
    print(f"jackknife positive: {jk_pos}/{len(blocks)}")


if __name__ == "__main__":
    main()
