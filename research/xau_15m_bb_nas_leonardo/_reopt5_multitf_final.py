"""_reopt5_multitf_final.py — canonical metric dump for the MULTI-TF finalists.
Emits exact fields for the structured deliverable. RAW-causal.
win=R>0 selection only (R not a feature). Multi-TF R2 axis re-derived for 5ATR.
"""
from _reopt5_lib import load, metrics, is_robust

rows = load()


def dump(name, desc, keep):
    kept = [r for r in rows if keep(r)]
    m = metrics(kept, rows)
    rob = is_robust(m)
    print(f"{name} | {desc}")
    print(f"  n_keep={m['n_keep']} wr_keep={m['wr_keep']} streak_keep={m['streak_keep']} "
          f"(base streak {m['streak_base']})")
    print(f"  winners_kept_pct={m['winners_kept_pct']} losers_cut_pct={m['losers_cut_pct']}")
    print(f"  y24={m['by_year'][2024]} y25={m['by_year'][2025]} y26={m['by_year'][2026]} "
          f"blocks_ok={m['blocks_ok']}/8 robust={rob}")
    print()


dump("F1_h1pos65", "CUT h1_pos<=0.65 (weak 15M structure / low in h1 swing)",
     lambda r: not (r["h1_pos"] is not None and r["h1_pos"] <= 0.65))
dump("F2_h1pos70_or_h1dist185",
     "CUT h1_pos<=0.70 OR h1_dist<=1.85 (no thrust: low in swing or hugging h1 EMA)",
     lambda r: not ((r["h1_pos"] is not None and r["h1_pos"] <= 0.70) or
                    (r["h1_dist"] is not None and r["h1_dist"] <= 1.85)))
dump("F3_into_supply", "CUT dist_supply_atr<=-0.26 (closing into overhead supply)",
     lambda r: not (r["dist_supply_atr"] is not None and r["dist_supply_atr"] <= -0.26))
dump("F4_h1pos65_or_supply", "STACK CUT h1_pos<=0.65 OR dist_supply<=-0.26 (multi-TF + location)",
     lambda r: not ((r["h1_pos"] is not None and r["h1_pos"] <= 0.65) or
                    (r["dist_supply_atr"] is not None and r["dist_supply_atr"] <= -0.26)))
