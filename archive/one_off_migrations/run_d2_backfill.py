#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, timezone
import argparse
import json
import subprocess
import time

BASE_DIR = Path.home() / "tradingview-mcp"
BRIDGE_DIR = BASE_DIR / "alert-bridge"
LOG_DIR = BRIDGE_DIR / "logs"
RUN_LOG = LOG_DIR / "d2_backfill_runs.jsonl"
EVALUATOR = BRIDGE_DIR / "evaluate_setup_outcomes.py"
STATUS_SCRIPT = BRIDGE_DIR / "research_status.py"

DEFAULT_ALERT_TYPES = "monitor_dynamic_bb_zone,monitor_dynamic_line,monitor_zone"
DEFAULT_TIMEFRAMES = "15,30,60"


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def append_run_log(record):
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with RUN_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def tail_text(text, n=3000):
    return (text or "")[-n:]


def run_command(cmd, timeout):
    started = time.time()
    try:
        result = subprocess.run(
            cmd,
            cwd=str(BASE_DIR),
            text=True,
            capture_output=True,
            timeout=timeout,
        )
        elapsed = round(time.time() - started, 2)
        return {
            "ok": result.returncode == 0,
            "timeout": False,
            "returncode": result.returncode,
            "elapsed_seconds": elapsed,
            "stdout": result.stdout or "",
            "stderr": result.stderr or "",
        }
    except subprocess.TimeoutExpired as exc:
        elapsed = round(time.time() - started, 2)
        return {
            "ok": False,
            "timeout": True,
            "returncode": None,
            "elapsed_seconds": elapsed,
            "stdout": exc.stdout or "",
            "stderr": exc.stderr or "",
        }


def build_eval_cmd(args):
    cmd = [
        "python3",
        str(EVALUATOR),
        "--limit",
        str(args.limit),
        "--since",
        args.since,
        "--timeframes",
        args.timeframes,
        "--alert-types",
        args.alert_types,
        "--horizons",
        args.horizons,
    ]

    if args.skip_partial_50:
        cmd.append("--skip-partial-50")

    if args.newest_first:
        cmd.append("--newest-first")

    return cmd


def main():
    parser = argparse.ArgumentParser(description="Operational D2 backfill runner")
    parser.add_argument("--iterations", type=int, default=5)
    parser.add_argument("--limit", type=int, default=1)
    parser.add_argument("--since", default="2026-05-04")
    parser.add_argument("--timeframes", default=DEFAULT_TIMEFRAMES)
    parser.add_argument("--alert-types", default=DEFAULT_ALERT_TYPES)
    parser.add_argument("--horizons", default="5,10,20,50")
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--sleep", type=int, default=10)
    parser.add_argument("--skip-partial-50", action="store_true", default=True)
    parser.add_argument("--include-partial-50", action="store_true")
    parser.add_argument("--newest-first", action="store_true")
    parser.add_argument("--stop-on-error", action="store_true")
    args = parser.parse_args()

    if args.include_partial_50:
        args.skip_partial_50 = False

    print("=== D2 Backfill Runner ===")
    print("iterations:", args.iterations)
    print("limit:", args.limit)
    print("since:", args.since)
    print("timeframes:", args.timeframes)
    print("alert_types:", args.alert_types)
    print("horizons:", args.horizons)
    print("timeout:", args.timeout)
    print("run_log:", RUN_LOG)
    print()

    for i in range(1, args.iterations + 1):
        cmd = build_eval_cmd(args)
        print(f"--- Cycle {i}/{args.iterations} ---")
        print("cmd:", " ".join(cmd))

        result = run_command(cmd, timeout=args.timeout)

        record = {
            "ran_at": now_iso(),
            "cycle": i,
            "iterations": args.iterations,
            "cmd": cmd,
            "ok": result["ok"],
            "timeout": result["timeout"],
            "returncode": result["returncode"],
            "elapsed_seconds": result["elapsed_seconds"],
            "stdout_tail": tail_text(result["stdout"]),
            "stderr_tail": tail_text(result["stderr"]),
        }
        append_run_log(record)

        print("ok:", result["ok"], "| timeout:", result["timeout"], "| elapsed:", result["elapsed_seconds"], "s")

        if result["stdout"]:
            print(result["stdout"].strip()[-1200:])
        if result["stderr"]:
            print("STDERR:", result["stderr"].strip()[-1200:])

        if not result["ok"] and args.stop_on_error:
            print("Stopping on error.")
            break

        if i < args.iterations:
            time.sleep(args.sleep)

    print()
    print("=== Final research status ===")
    status = run_command(["python3", str(STATUS_SCRIPT)], timeout=60)
    print((status["stdout"] or status["stderr"]).strip())


if __name__ == "__main__":
    main()
