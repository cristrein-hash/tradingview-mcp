#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, timezone
import argparse
import json
import subprocess
import time

BASE_DIR = Path.home() / "tradingview-mcp"
BRIDGE_DIR = BASE_DIR / "alert-bridge"
STRATEGY_DIR = BASE_DIR / "my-strategy"

CONFIG_PATH = STRATEGY_DIR / "research/research_pipeline_config.json"

D2R_RUNNER = BRIDGE_DIR / "run_d2r_backfill.py"
D2R_SUMMARY = BRIDGE_DIR / "generate_d2r_summary.py"
STATUS_SCRIPT = BRIDGE_DIR / "research_status.py"

CYCLE_LOG = BRIDGE_DIR / "logs/research_cycle_runs.jsonl"


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def load_config():
    if not CONFIG_PATH.exists():
        raise SystemExit(f"Config não encontrado: {CONFIG_PATH}")
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def append_log(record):
    CYCLE_LOG.parent.mkdir(parents=True, exist_ok=True)
    with CYCLE_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


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
        return {
            "ok": result.returncode == 0,
            "timeout": False,
            "returncode": result.returncode,
            "elapsed_seconds": round(time.time() - started, 2),
            "stdout": result.stdout or "",
            "stderr": result.stderr or "",
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "ok": False,
            "timeout": True,
            "returncode": None,
            "elapsed_seconds": round(time.time() - started, 2),
            "stdout": exc.stdout or "",
            "stderr": exc.stderr or "",
        }


def print_block(title, result):
    print()
    print(f"=== {title} ===")
    print("ok:", result["ok"], "| timeout:", result["timeout"], "| elapsed:", result["elapsed_seconds"], "s")
    if result["stdout"]:
        print(result["stdout"].strip()[-3000:])
    if result["stderr"]:
        print("STDERR:")
        print(result["stderr"].strip()[-3000:])


def main():
    config = load_config()
    d2r_cfg = config["d2r"]

    parser = argparse.ArgumentParser(description="Run operational research cycle")
    parser.add_argument("--d2r", action="store_true", help="Run D2R backfill")
    parser.add_argument("--summary", action="store_true", help="Generate D2R summary")
    parser.add_argument("--status", action="store_true", help="Show research status")
    parser.add_argument("--all", action="store_true", help="Run D2R + summary + status")
    parser.add_argument("--iterations", type=int, default=d2r_cfg["iterations_default"])
    parser.add_argument("--limit", type=int, default=d2r_cfg["batch_limit"])
    parser.add_argument("--since", default=config["analysis_window"]["default_since"])
    parser.add_argument("--candidate-only", action="store_true", default=True)
    parser.add_argument("--timeout", type=int, default=d2r_cfg["timeout_seconds"])
    parser.add_argument("--sleep", type=int, default=d2r_cfg["sleep_seconds"])
    args = parser.parse_args()

    if args.all:
        args.d2r = True
        args.summary = True
        args.status = True

    if not (args.d2r or args.summary or args.status):
        args.all = True
        args.d2r = True
        args.summary = True
        args.status = True

    cycle = {
        "started_at": now_iso(),
        "args": vars(args),
        "steps": []
    }

    print("=== Research Cycle ===")
    print("config:", CONFIG_PATH)
    print("cycle_log:", CYCLE_LOG)
    print("d2r:", args.d2r)
    print("summary:", args.summary)
    print("status:", args.status)

    if args.d2r:
        cmd = [
            "python3",
            str(D2R_RUNNER),
            "--iterations",
            str(args.iterations),
            "--limit",
            str(args.limit),
            "--since",
            args.since,
            "--timeout",
            str(args.timeout),
            "--sleep",
            str(args.sleep),
        ]

        if args.candidate_only:
            cmd.append("--candidate-only")

        result = run_command(cmd, timeout=(args.timeout + args.sleep + 60) * args.iterations)
        print_block("D2R BACKFILL", result)
        cycle["steps"].append({
            "name": "d2r_backfill",
            "cmd": cmd,
            "ok": result["ok"],
            "timeout": result["timeout"],
            "elapsed_seconds": result["elapsed_seconds"],
            "stdout_tail": result["stdout"][-3000:],
            "stderr_tail": result["stderr"][-3000:]
        })

    if args.summary:
        cmd = ["python3", str(D2R_SUMMARY)]
        result = run_command(cmd, timeout=120)
        print_block("D2R SUMMARY", result)
        cycle["steps"].append({
            "name": "d2r_summary",
            "cmd": cmd,
            "ok": result["ok"],
            "timeout": result["timeout"],
            "elapsed_seconds": result["elapsed_seconds"],
            "stdout_tail": result["stdout"][-3000:],
            "stderr_tail": result["stderr"][-3000:]
        })

    if args.status:
        cmd = ["python3", str(STATUS_SCRIPT)]
        result = run_command(cmd, timeout=120)
        print_block("RESEARCH STATUS", result)
        cycle["steps"].append({
            "name": "research_status",
            "cmd": cmd,
            "ok": result["ok"],
            "timeout": result["timeout"],
            "elapsed_seconds": result["elapsed_seconds"],
            "stdout_tail": result["stdout"][-3000:],
            "stderr_tail": result["stderr"][-3000:]
        })

    cycle["finished_at"] = now_iso()
    append_log(cycle)

    print()
    print("=== Cycle complete ===")
    print("Log:", CYCLE_LOG)


if __name__ == "__main__":
    main()
