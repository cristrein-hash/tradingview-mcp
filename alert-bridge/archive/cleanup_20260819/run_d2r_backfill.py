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
EVALUATOR = BRIDGE_DIR / "evaluate_r_outcomes.py"
STATUS_SCRIPT = BRIDGE_DIR / "research_status.py"


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def load_config():
    if not CONFIG_PATH.exists():
        raise SystemExit(f"Config não encontrado: {CONFIG_PATH}")
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def append_jsonl(path: Path, record: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
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


def build_cmd(args, config):
    d2r = config["d2r"]

    since = args.since or config["analysis_window"]["default_since"]

    if args.candidate_only:
        classifications = ",".join(config["classifications"]["candidate_only"])
    else:
        classifications = ",".join(config["classifications"]["primary_focus"])

    cmd = [
        "python3",
        str(EVALUATOR),
        "--limit",
        str(args.limit or d2r["batch_limit"]),
        "--since",
        since,
        "--classifications",
        classifications,
        "--timeout",
        str(args.timeout or d2r["timeout_seconds"]),
    ]

    if args.newest_first:
        cmd.append("--newest-first")

    return cmd


def count_jsonl(path: Path):
    if not path.exists():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8", errors="replace").splitlines() if line.strip())


def main():
    config = load_config()
    d2r = config["d2r"]
    logs = config["logs"]

    parser = argparse.ArgumentParser(description="Operational D2R backfill runner")
    parser.add_argument("--iterations", type=int, default=d2r["iterations_default"])
    parser.add_argument("--limit", type=int, default=d2r["batch_limit"])
    parser.add_argument("--since", default=config["analysis_window"]["default_since"])
    parser.add_argument("--timeout", type=int, default=d2r["timeout_seconds"])
    parser.add_argument("--sleep", type=int, default=d2r["sleep_seconds"])
    parser.add_argument("--candidate-only", action="store_true", help="Only evaluate SETUP_CANDIDATO_FORTE")
    parser.add_argument("--newest-first", action="store_true")
    parser.add_argument("--stop-on-error", action="store_true")
    args = parser.parse_args()

    run_log = Path(logs["d2r_backfill_runs"])
    r_log = Path(logs["setup_r_outcome_log"])

    print("=== D2R Backfill Runner ===")
    print("config:", CONFIG_PATH)
    print("iterations:", args.iterations)
    print("limit:", args.limit)
    print("since:", args.since)
    print("candidate_only:", args.candidate_only)
    print("timeout:", args.timeout)
    print("sleep:", args.sleep)
    print("run_log:", run_log)
    print("current D2R events:", count_jsonl(r_log))
    print()

    for i in range(1, args.iterations + 1):
        before_count = count_jsonl(r_log)
        cmd = build_cmd(args, config)

        print(f"--- D2R cycle {i}/{args.iterations} ---")
        print("cmd:", " ".join(cmd))

        result = run_command(cmd, timeout=args.timeout)
        after_count = count_jsonl(r_log)

        record = {
            "ran_at": now_iso(),
            "cycle": i,
            "iterations": args.iterations,
            "cmd": cmd,
            "ok": result["ok"],
            "timeout": result["timeout"],
            "returncode": result["returncode"],
            "elapsed_seconds": result["elapsed_seconds"],
            "d2r_count_before": before_count,
            "d2r_count_after": after_count,
            "new_records": after_count - before_count,
            "stdout_tail": tail_text(result["stdout"]),
            "stderr_tail": tail_text(result["stderr"]),
        }

        append_jsonl(run_log, record)

        print("ok:", result["ok"], "| timeout:", result["timeout"], "| elapsed:", result["elapsed_seconds"], "s")
        print("new D2R records:", after_count - before_count)

        if result["stdout"]:
            print(result["stdout"].strip()[-1200:])

        if result["stderr"]:
            print("STDERR:", result["stderr"].strip()[-1200:])

        if not result["ok"] and args.stop_on_error:
            print("Stopping on error.")
            break

        if after_count == before_count:
            print("Nenhum novo D2R salvo neste ciclo.")

        if i < args.iterations:
            time.sleep(args.sleep)

    print()
    print("=== Final D2R count ===")
    print(count_jsonl(r_log))

    print()
    print("=== Research status ===")
    status = run_command(["python3", str(STATUS_SCRIPT)], timeout=60)
    print((status["stdout"] or status["stderr"]).strip())


if __name__ == "__main__":
    main()
