#!/usr/bin/env python3
"""
Visual audit helper for XAU_4H_DEMAND_BREAKOUT v2 — Patch 1 skeleton.

Status:
  - --dry-run is the default (and the only allowed mode in this patch).
  - Real execution (`--no-dry-run`) is REJECTED with exit code 2 here.
  - No MCP subprocess. No chart access. No screenshot. No log mutation.
  - The MCPClient class is intentionally NOT implemented yet; it lands in a
    later patch under explicit authorization for actual chart execution.

Replaces the legacy `alert-bridge/draw_demand_breakout_v2_trades.py` (removed
2026-05-28). Designed from current rules forward — not patched from old.

Architecture (when fully implemented in subsequent patches):
  - smoke-first, batch only after smoke PASS
  - PEPPERSTONE:XAUUSD hard gate (no OANDA, no bare ticker, no XAG/Silver)
  - timeframe 240 hard gate
  - chart_get_state validation AFTER every chart_set_*; abort on any drift
  - output dir is timestamped; never overwrites prior artifacts
  - manifest records every chart_state observation (pre + post)
  - 1 focused screenshot per trade (smoke = 1; batch = N)
  - chart_lock acquired via flock; orchestration of daemon pause is EXTERNAL

References:
  docs/architecture/INDICATOR_SIGNAL_POLICY.md   (provider whitelist)
  docs/architecture/SIGNAL_OUTCOME_LAB.md        (canonical-slim-first)
"""

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Hard-coded gates
# ---------------------------------------------------------------------------

REQUIRED_SYMBOL = "PEPPERSTONE:XAUUSD"
REQUIRED_PROVIDER = "PEPPERSTONE"
REQUIRED_BASE = "XAUUSD"
REQUIRED_TIMEFRAME = "240"
ACCEPTED_TF_FORMS = ("240", "4H", "4h")
FORBIDDEN_PROVIDERS = ("OANDA", "VANTAGE", "FOREXCOM", "FX", "FX_IDC")
FORBIDDEN_BASE_SUBSTRINGS = (
    "XAG", "Silver", "USOUSD", "ETHUSD", "EURUSD", "US500", "BTC",
)

EVALUATOR_VERSION = "v0.1.0"

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TRADES_FILE = (
    REPO_ROOT
    / "my-strategy/research/revalidation/XAU_4H_DEMAND_BREAKOUT/v2/trades.jsonl"
)
DEFAULT_OUTPUT_ROOT = REPO_ROOT / "screenshots"
PAUSE_FLAG = Path("/tmp/claude_recheck.paused")
CHART_LOCK = Path("/tmp/tradingview_chart.lock")


# ---------------------------------------------------------------------------
# Argument validation (hard gates — fire before any work)
# ---------------------------------------------------------------------------


def validate_symbol_and_timeframe_args(args):
    """Reject any deviation from PEPPERSTONE:XAUUSD / 240. Returns list of errors."""
    errs = []
    if args.symbol != REQUIRED_SYMBOL:
        errs.append(
            f"--symbol must be {REQUIRED_SYMBOL!r} (got {args.symbol!r})"
        )
    if args.timeframe != REQUIRED_TIMEFRAME:
        errs.append(
            f"--timeframe must be {REQUIRED_TIMEFRAME!r} (got {args.timeframe!r})"
        )
    return errs


def validate_chart_state(state):
    """Pure function. Given a dict from chart_get_state, return (ok, errors).

    NOT invoked in dry-run. Defined here so it is unit-testable and ready to
    be called by the future real-execution path (next patch).
    """
    if not isinstance(state, dict):
        return (False, ["chart_get_state returned non-dict"])
    errs = []
    symbol = state.get("symbol") or ""
    timeframe = str(state.get("resolution") or state.get("timeframe") or "")

    if symbol != REQUIRED_SYMBOL:
        errs.append(f"symbol mismatch: expected {REQUIRED_SYMBOL!r}, got {symbol!r}")
    if timeframe not in ACCEPTED_TF_FORMS:
        errs.append(
            f"timeframe mismatch: expected {REQUIRED_TIMEFRAME!r}, got {timeframe!r}"
        )
    for prov in FORBIDDEN_PROVIDERS:
        if symbol.startswith(prov + ":"):
            errs.append(f"forbidden provider prefix in symbol: {symbol!r}")
    for forbidden in FORBIDDEN_BASE_SUBSTRINGS:
        if forbidden in symbol:
            errs.append(
                f"forbidden base substring {forbidden!r} in symbol {symbol!r}"
            )
    return (len(errs) == 0, errs)


# ---------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------


def load_trades(trades_file):
    """Load all trade records from JSONL. Returns list of dicts."""
    if not trades_file.exists():
        raise FileNotFoundError(f"trades file missing: {trades_file}")
    trades = []
    with open(trades_file, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                trades.append(json.loads(line))
            except json.JSONDecodeError:
                # silent skip — these would also be flagged in a stricter run
                continue
    return trades


def select_smoke_trade(trades, signal_bar=None):
    """Pick exactly one trade for the smoke screenshot.

    Default: the smallest-R winning trade (a clear, non-edge-case win — not
    best_MFE, not worst_MAE, not ambiguous).

    Returns (trade_or_None, reason_str).
    """
    if signal_bar is not None:
        for t in trades:
            if t.get("signal_bar") == signal_bar:
                return (t, f"--signal-bar={signal_bar}")
        return (None, f"signal_bar {signal_bar} not present in trades")

    wins = [t for t in trades if (t.get("R_multiple") or 0) > 0]
    if not wins:
        return (None, "no winning trades found in input")
    wins.sort(key=lambda t: t.get("R_multiple") or 0)
    chosen = wins[0]
    return (chosen, f"first WIN by R ascending (R={chosen.get('R_multiple')})")


# ---------------------------------------------------------------------------
# Output planning
# ---------------------------------------------------------------------------


def build_output_paths(args):
    """Compute timestamped output dir + subdirs.

    Does NOT create any directory or file. The whole point of the timestamped
    default is that re-runs never collide.
    """
    if args.output_dir:
        out_root = Path(args.output_dir)
    else:
        utc = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
        out_root = DEFAULT_OUTPUT_ROOT / f"dbk_v2_clean_{utc}"
    return {
        "output_dir":            out_root,
        "smoke_dir":             out_root / "smoke",
        "batch_dir":             out_root / "batch",
        "smoke_manifest":        out_root / "smoke" / "smoke_manifest.json",
        "batch_manifest":        out_root / "batch" / "batch_manifest.json",
        "chart_state_validation": out_root / "chart_state_validation.json",
        "audit_log":             out_root / "audit_log.jsonl",
    }


def planned_manifest(args, trade, paths, mode):
    """Build the manifest dict that WOULD be written. Does NOT write."""
    return {
        "run_id": (
            f"dbk_v2_audit_"
            f"{dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H-%M-%SZ')}"
        ),
        "mode": mode,
        "evaluator_version": EVALUATOR_VERSION,
        "created_at_planned": dt.datetime.now(dt.timezone.utc).isoformat(),
        "dry_run": args.dry_run,
        "input": {
            "trades_file": str(args.trades_file),
            "smoke_signal_bar": (trade or {}).get("signal_bar") if trade else None,
        },
        "required_chart_state": {
            "symbol": REQUIRED_SYMBOL,
            "timeframe": REQUIRED_TIMEFRAME,
        },
        "forbidden_providers": list(FORBIDDEN_PROVIDERS),
        "forbidden_base_substrings": list(FORBIDDEN_BASE_SUBSTRINGS),
        "external_orchestration_required_for_no_dry_run": {
            "pause_flag_must_exist": str(PAUSE_FLAG),
            "monitor_daemon_must_be_paused": "com.cristrein.xau-4h-monitor-daemon",
            "chart_lock_to_acquire": str(CHART_LOCK),
        },
        "output_paths_planned": {k: str(v) for k, v in paths.items()},
        "trade_drawn_planned": trade,
    }


# ---------------------------------------------------------------------------
# Dry-run reporters per mode
# ---------------------------------------------------------------------------


def dry_run_smoke(args):
    print("== dry-run smoke ==")
    trades_file = Path(args.trades_file)
    print(f"  trades_file: {trades_file}")
    if not trades_file.exists():
        print(f"  ERROR: trades_file not found", file=sys.stderr)
        return 1

    trades = load_trades(trades_file)
    print(f"  trades loaded: {len(trades)}")

    trade, reason = select_smoke_trade(trades, signal_bar=args.signal_bar)
    if trade is None:
        print(f"  ERROR: no smoke trade selectable ({reason})", file=sys.stderr)
        return 1

    print(
        f"  smoke trade:    signal_bar={trade.get('signal_bar')}  "
        f"R={trade.get('R_multiple')}  exit={trade.get('exit_reason')}  "
        f"regime={trade.get('regime')}"
    )
    print(f"  selection_reason: {reason}")

    paths = build_output_paths(args)
    print(f"  planned output paths (none of these are created in dry-run):")
    for k, v in paths.items():
        existed = "EXISTS_ALREADY" if v.exists() else "would-be-created"
        print(f"    {k:32s} -> {v}  [{existed}]")

    manifest = planned_manifest(args, trade, paths, mode="smoke")
    if args.verbose:
        print("\n  full planned manifest:")
        print(json.dumps(manifest, indent=2, default=str))
    else:
        print("\n  planned manifest (key fields):")
        print(json.dumps(
            {
                "run_id": manifest["run_id"],
                "mode": manifest["mode"],
                "dry_run": manifest["dry_run"],
                "required_chart_state": manifest["required_chart_state"],
                "external_orchestration_required_for_no_dry_run":
                    manifest["external_orchestration_required_for_no_dry_run"],
            },
            indent=2, default=str,
        ))

    print("\n  status: SMOKE_PLAN_READY  (no MCP, no chart, no writes performed)")
    return 0


def dry_run_batch(args):
    print("== dry-run batch ==")
    print(
        "  status: BATCH_MODE_PLANNED_BUT_NOT_IMPLEMENTED_IN_THIS_PATCH"
    )
    print(
        "  precondition: a prior smoke run with smoke_status=PASS will be "
        "required (in a future patch) before batch execution is unlocked."
    )
    print(
        "  this patch only wires the smoke planning skeleton; batch is a "
        "placeholder that produces this plan summary and exits cleanly."
    )

    trades_file = Path(args.trades_file)
    if trades_file.exists():
        trades = load_trades(trades_file)
        print(f"  trades loaded (informational): {len(trades)}")
    else:
        print(f"  trades_file missing: {trades_file}")

    paths = build_output_paths(args)
    print(f"  planned output_dir: {paths['output_dir']}")
    print(f"  planned batch_dir:  {paths['batch_dir']}")
    print(f"  planned batch_manifest: {paths['batch_manifest']}")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_argparser():
    p = argparse.ArgumentParser(
        prog="visual_audit_demand_breakout_v2",
        description=(
            "Visual audit helper for XAU_4H_DEMAND_BREAKOUT v2 "
            "(Patch 1 skeleton; dry-run default; real execution NOT yet wired)."
        ),
    )
    p.add_argument(
        "--mode", required=True, choices=["smoke", "batch"],
    )
    p.add_argument(
        "--symbol", default=REQUIRED_SYMBOL,
        help=f"Hard-gated to {REQUIRED_SYMBOL!r}; anything else exits with code 2.",
    )
    p.add_argument(
        "--timeframe", default=REQUIRED_TIMEFRAME,
        help=f"Hard-gated to {REQUIRED_TIMEFRAME!r}; anything else exits with code 2.",
    )
    p.add_argument("--trades-file", default=str(DEFAULT_TRADES_FILE))
    p.add_argument(
        "--output-dir", default=None,
        help="If omitted, a timestamped dir under screenshots/ is planned.",
    )
    p.add_argument(
        "--signal-bar", type=int, default=None,
        help="Smoke mode only: pick this exact trade by signal_bar.",
    )
    p.add_argument("--verbose", action="store_true")
    p.add_argument(
        "--dry-run", action="store_true", default=False,
        help="(default) Plan-only. Explicit alias for clarity.",
    )
    p.add_argument(
        "--no-dry-run", action="store_true", default=False,
        help="(NOT IMPLEMENTED in this skeleton.) Triggers a clean exit with code 2.",
    )
    return p


def main(argv=None):
    parser = build_argparser()
    args = parser.parse_args(argv)
    args.dry_run = not args.no_dry_run

    # Hard gate: argument validation before anything else.
    arg_errs = validate_symbol_and_timeframe_args(args)
    if arg_errs:
        for e in arg_errs:
            print(f"ERROR: {e}", file=sys.stderr)
        return 2

    # Reject real execution in this skeleton patch.
    if not args.dry_run:
        print(
            "ERROR: real execution (--no-dry-run) is NOT implemented in this "
            "skeleton patch. The smoke/batch chart-touching paths land in a "
            "subsequent authorized patch. Run with --dry-run (default).",
            file=sys.stderr,
        )
        return 2

    if args.mode == "smoke":
        return dry_run_smoke(args)
    if args.mode == "batch":
        return dry_run_batch(args)
    return 2


if __name__ == "__main__":
    sys.exit(main())
