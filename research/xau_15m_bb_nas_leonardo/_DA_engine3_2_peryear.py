#!/usr/bin/env python3
"""DA ATTACK 2 — PER-YEAR breakdown of the standout combo. (Cris 2026-06-28)
Does reclaim_atr+swept_prior_low+buy_bub_w hold ALL years or is it 2024-2025 only? 2026 bear expected weak — quantify.
Also per-year for the second standout reclaim_atr+buy_bub_w (rank1) and take-all for reference."""
from _DA_engine3_core import G, passes, R_of, metr, STANDOUT

def year_breakdown(cc, label):
    print(f"\n=== {label}: {'+'.join(cc)} ===")
    print(f"{'year':>6}{'n':>5}{'mf':>4}{'WR':>7}{'sumR':>8}{'avgR':>8}{'maxDD':>8}")
    full = [r for r in G if passes(r, cc)]
    for y in (2024, 2025, 2026):
        sel = [r for r in full if r.get("yr") == y]
        m = metr(sel)
        mf = sum(r["is_monforte"] for r in sel)
        if m:
            print(f"{y:>6}{m['n']:>5}{mf:>4}{m['WR']:>7}{m['sumR']:>8}{m['avgR']:>8}{m['maxDD']:>8}")
        else:
            print(f"{y:>6}{'0':>5}")
    m = metr(full); mf = sum(r["is_monforte"] for r in full)
    print(f"{'ALL':>6}{m['n']:>5}{mf:>4}{m['WR']:>7}{m['sumR']:>8}{m['avgR']:>8}{m['maxDD']:>8}")

year_breakdown(STANDOUT, "STANDOUT (rank3)")
year_breakdown(("reclaim_atr", "buy_bub_w"), "reclaim_atr+buy_bub_w (rank1 avgR)")
# take-all per year for reference
print("\n=== TAKE-ALL (knife-gated) per year ===")
print(f"{'year':>6}{'n':>5}{'WR':>7}{'sumR':>8}{'avgR':>8}")
for y in (2024, 2025, 2026):
    sel = [r for r in G if r.get("yr") == y]; m = metr(sel)
    print(f"{y:>6}{m['n']:>5}{m['WR']:>7}{m['sumR']:>8}{m['avgR']:>8}")
print("\nVERDICT 2: combo is robust across years iff avgR>0 AND >= take-all-same-year in 2024,2025,2026.")
