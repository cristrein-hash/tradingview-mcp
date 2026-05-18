#!/usr/bin/env python3
"""
report_indicator_edge.py — Relatório agregado de edge dos indicators alarmados.

Lê indicator_signals.jsonl + indicator_signals_outcomes.jsonl,
agrupa por (base_symbol × timeframe × indicator_name × signal_type × side),
computa stats (n, win_rate, expectancy R, profit factor) e aplica sample gate
institucional pra identificar candidatos a promoção/demoção de priority.

Sample gate (institucional 2026-05-15):
- n < 30:   FRAGILE         (não usar pra decisão)
- 30-49:    DIRECTIONAL     (sinal de direção)
- 50-99:    PRELIMINARY     (uso interim, ainda volátil)
- ≥ 100:    SOLID           (validado, decisão estável)

Promoção: tier ≥ PRELIMINARY AND expectancy ≥ 0.4 AND win_rate ≥ 55%
Demoção:  tier ≥ PRELIMINARY AND expectancy ≤ -0.2

Usage:
  python3 report_indicator_edge.py [--asset XAUUSD] [--tier PRELIMINARY] [--top 20]
  python3 report_indicator_edge.py --save  # also writes timestamped MD file
"""

from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
import argparse
import json
import math
import sys

BASE_DIR = Path.home() / "tradingview-mcp"
LOG_DIR = BASE_DIR / "alert-bridge" / "logs"
SIGNALS_LOG = LOG_DIR / "indicator_signals.jsonl"
OUTCOMES_LOG = LOG_DIR / "indicator_signals_outcomes.jsonl"
REPORTS_DIR = LOG_DIR / "indicator_edge_reports"

# Promotion / demotion thresholds
PROMO_EXPECTANCY_MIN = 0.4
PROMO_WIN_RATE_MIN = 0.55
DEMO_EXPECTANCY_MAX = -0.2

# Sample tier thresholds
TIER_DIRECTIONAL = 30
TIER_PRELIMINARY = 50
TIER_SOLID = 100


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def load_jsonl(path: Path):
    if not path.exists():
        return []
    out = []
    with path.open() as f:
        for line in f:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def sample_tier(n: int) -> str:
    if n < TIER_DIRECTIONAL:
        return "FRAGILE"
    if n < TIER_PRELIMINARY:
        return "DIRECTIONAL"
    if n < TIER_SOLID:
        return "PRELIMINARY"
    return "SOLID"


def load_matched():
    """Match signals with outcomes by signal_hash. Returns flat list of records."""
    signals = load_jsonl(SIGNALS_LOG)
    outcomes = load_jsonl(OUTCOMES_LOG)
    out_by_hash = {o.get("signal_hash"): o for o in outcomes if o.get("signal_hash")}

    matched = []
    for s in signals:
        h = s.get("signal_hash")
        if not h or h not in out_by_hash:
            continue
        o = out_by_hash[h]
        # Each outcome may have long_outcome, short_outcome, or both (for ambiguous)
        for side_key, side_label in [("long_outcome", "long"), ("short_outcome", "short")]:
            so = o.get(side_key)
            if so and so.get("outcome_R") is not None:
                matched.append({
                    "base_symbol": s.get("base_symbol"),
                    "timeframe": str(s.get("timeframe", "")),
                    "indicator_name": s.get("indicator_name"),
                    "signal_type": s.get("signal_type"),
                    "side": side_label,
                    "outcome_R": float(so["outcome_R"]),
                    "outcome_label": so.get("outcome_label"),
                    "max_favorable_R": so.get("max_favorable_R"),
                    "max_adverse_R": so.get("max_adverse_R"),
                    "ts_signal": s.get("ts_signal"),
                })
    return matched, len(signals), len(outcomes)


def aggregate(matched):
    """Group by (asset, tf, indicator, signal_type, side)."""
    groups = defaultdict(list)
    for m in matched:
        key = (
            m["base_symbol"],
            m["timeframe"],
            m["indicator_name"],
            m["signal_type"],
            m["side"],
        )
        groups[key].append(m)
    return groups


def compute_stats(records):
    n = len(records)
    if n == 0:
        return None
    r_values = [r["outcome_R"] for r in records if r["outcome_R"] is not None]
    if not r_values:
        return None

    wins = [r for r in r_values if r > 0.01]
    losses = [r for r in r_values if r < -0.01]
    breakevens = [r for r in r_values if -0.01 <= r <= 0.01]

    win_rate = len(wins) / n if n else 0.0
    expectancy = sum(r_values) / n
    sum_wins = sum(wins)
    sum_losses = abs(sum(losses)) if losses else 0.0
    profit_factor = (sum_wins / sum_losses) if sum_losses > 0 else (float("inf") if sum_wins > 0 else 0.0)

    # MFE/MAE averages (where present)
    mfes = [r.get("max_favorable_R") for r in records if r.get("max_favorable_R") is not None]
    maes = [r.get("max_adverse_R") for r in records if r.get("max_adverse_R") is not None]
    avg_mfe = sum(mfes) / len(mfes) if mfes else None
    avg_mae = sum(maes) / len(maes) if maes else None

    return {
        "n": n,
        "wins": len(wins),
        "losses": len(losses),
        "breakevens": len(breakevens),
        "win_rate": win_rate,
        "expectancy": expectancy,
        "profit_factor": profit_factor,
        "avg_mfe_R": avg_mfe,
        "avg_mae_R": avg_mae,
        "tier": sample_tier(n),
        "score": expectancy * math.sqrt(n),  # risk-adjusted ranking
    }


def format_group_line(key, stats):
    sym, tf, ind, st, side = key
    pf_str = f"{stats['profit_factor']:.2f}" if stats['profit_factor'] != float("inf") else "∞"
    return (
        f"  - **{sym} TF{tf} | {ind} | {st} ({side})**: "
        f"n={stats['n']} (W{stats['wins']}/L{stats['losses']}/BE{stats['breakevens']}) | "
        f"win%={stats['win_rate']*100:.1f} | "
        f"exp={stats['expectancy']:+.3f}R | "
        f"PF={pf_str}"
    )


def build_report(matched, signals_total, outcomes_total, args):
    groups = aggregate(matched)
    if not groups:
        return "# Indicator Edge Report\n\n_No matched signal-outcome pairs._\n"

    # Compute stats per group
    group_stats = []
    for key, records in groups.items():
        stats = compute_stats(records)
        if stats is None:
            continue
        # Filters
        sym, tf, ind, st, side = key
        if args.asset and sym != args.asset:
            continue
        if args.indicator and ind != args.indicator:
            continue
        if args.tier and stats["tier"] != args.tier:
            continue
        group_stats.append((key, stats))

    if not group_stats:
        return "# Indicator Edge Report\n\n_No groups matched filters._\n"

    lines = []
    lines.append("# Indicator Edge Report")
    lines.append("")
    lines.append(f"Generated: {now_iso()}")
    lines.append(f"")
    lines.append(f"**Data scope:**")
    lines.append(f"- Total signals collected: {signals_total}")
    lines.append(f"- Total outcomes enriched: {outcomes_total}")
    lines.append(f"- Matched signal-outcome records (counting both sides for ambiguous): {len(matched)}")
    lines.append(f"- Unique groups (asset × TF × indicator × signal_type × side): {len(group_stats)}")
    if args.asset or args.indicator or args.tier:
        filt = []
        if args.asset: filt.append(f"asset={args.asset}")
        if args.indicator: filt.append(f"indicator={args.indicator}")
        if args.tier: filt.append(f"tier={args.tier}")
        lines.append(f"- Filters applied: {', '.join(filt)}")
    lines.append("")
    lines.append("**Sample gate (institutional):**")
    lines.append(f"- FRAGILE: n<{TIER_DIRECTIONAL} — não usar pra decisão")
    lines.append(f"- DIRECTIONAL: {TIER_DIRECTIONAL}≤n<{TIER_PRELIMINARY} — sinal de direção")
    lines.append(f"- PRELIMINARY: {TIER_PRELIMINARY}≤n<{TIER_SOLID} — interim uso")
    lines.append(f"- SOLID: n≥{TIER_SOLID} — validado")
    lines.append("")

    # Group by tier, sort by score within tier
    by_tier = defaultdict(list)
    for key, stats in group_stats:
        by_tier[stats["tier"]].append((key, stats))

    for tier in ["SOLID", "PRELIMINARY", "DIRECTIONAL", "FRAGILE"]:
        tier_list = by_tier.get(tier, [])
        if not tier_list:
            continue
        tier_list.sort(key=lambda x: x[1]["score"], reverse=True)
        top_n = args.top if args.top else len(tier_list)
        lines.append(f"## Tier: {tier} ({len(tier_list)} groups; showing top {min(top_n, len(tier_list))})")
        lines.append("")
        for key, stats in tier_list[:top_n]:
            lines.append(format_group_line(key, stats))
        lines.append("")

    # Promotion candidates (tier ≥ PRELIMINARY, expectancy ≥ 0.4, win_rate ≥ 55%)
    promotions = [
        (k, s) for k, s in group_stats
        if s["tier"] in ("PRELIMINARY", "SOLID")
        and s["expectancy"] >= PROMO_EXPECTANCY_MIN
        and s["win_rate"] >= PROMO_WIN_RATE_MIN
    ]
    promotions.sort(key=lambda x: x[1]["score"], reverse=True)

    lines.append(f"## Promotion candidates (n≥{TIER_PRELIMINARY}, expectancy≥{PROMO_EXPECTANCY_MIN}, win%≥{PROMO_WIN_RATE_MIN*100:.0f})")
    lines.append("")
    if promotions:
        for key, stats in promotions:
            lines.append(format_group_line(key, stats))
    else:
        lines.append("_Nenhum candidato ainda. Aguardando mais data._")
    lines.append("")

    # Demotion candidates (tier ≥ PRELIMINARY, expectancy ≤ -0.2)
    demotions = [
        (k, s) for k, s in group_stats
        if s["tier"] in ("PRELIMINARY", "SOLID")
        and s["expectancy"] <= DEMO_EXPECTANCY_MAX
    ]
    demotions.sort(key=lambda x: x[1]["expectancy"])  # most negative first

    lines.append(f"## Demotion candidates (n≥{TIER_PRELIMINARY}, expectancy≤{DEMO_EXPECTANCY_MAX})")
    lines.append("")
    if demotions:
        for key, stats in demotions:
            lines.append(format_group_line(key, stats))
    else:
        lines.append("_Nenhum candidato._")
    lines.append("")

    # Top global ranking
    all_sorted = sorted(group_stats, key=lambda x: x[1]["score"], reverse=True)
    lines.append("## Top 10 global (score = expectancy × √n)")
    lines.append("")
    for key, stats in all_sorted[:10]:
        lines.append(format_group_line(key, stats))
    lines.append("")

    return "\n".join(lines)


def main():
    p = argparse.ArgumentParser(description="Indicator edge report")
    p.add_argument("--asset", help="Filter por base_symbol (XAUUSD, EURUSD, etc)")
    p.add_argument("--indicator", help="Filter por indicator_name")
    p.add_argument("--tier", choices=["FRAGILE", "DIRECTIONAL", "PRELIMINARY", "SOLID"])
    p.add_argument("--top", type=int, default=20, help="Top N por tier (default 20)")
    p.add_argument("--save", action="store_true", help="Salva report em arquivo MD timestamped")
    args = p.parse_args()

    matched, signals_total, outcomes_total = load_matched()
    report = build_report(matched, signals_total, outcomes_total, args)
    print(report)

    if args.save:
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        fname = f"edge_report_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.md"
        path = REPORTS_DIR / fname
        path.write_text(report)
        print(f"\n_Saved: {path}_")

    return 0


if __name__ == "__main__":
    sys.exit(main())
