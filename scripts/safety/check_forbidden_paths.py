#!/usr/bin/env python3
"""check_forbidden_paths.py — REPORT-ONLY Agentic OS safety scanner.

Flags tracked code that WRITES to / deletes forbidden (production/runtime/RAW) paths.
Read-only: opens files read-only, prints findings, exit code always 0.
See docs/architecture/AGENTIC_OS_HOOKS_CI_SAFETY_PLAN.md + docs/governance/SAFETY_LAYER_USAGE.md.
"""
from __future__ import annotations
import re, subprocess, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

# tokens that mark a forbidden production/runtime/RAW target
FORBIDDEN_TOKENS = [
    "strategy_rules", "catalog", "receiver", "telegram", "launchctl", ".plist",
    "raw_replay", "/Volumes/GUTS", "alert-bridge/logs", "external_factors_v2/runtime",
    "monitor_", ".venv-agents",
]
# write/destructive operations
WRITE_OPS = re.compile(
    r"open\([^)]*,\s*['\"][wa]|\.write\(|json\.dump\(|shutil\.(rmtree|move|copy)"
    r"|os\.(remove|unlink|rename|replace)|rm\s+-rf|git\s+clean|launchctl\s+(un)?load"
)


def tracked_text_files():
    out = subprocess.run(["git", "-C", str(REPO), "ls-files"], capture_output=True, text=True).stdout
    for rel in out.splitlines():
        if rel.endswith((".py", ".sh")):
            yield rel


def run():
    findings = []
    for rel in tracked_text_files():
        # skip the safety scanners themselves + the resolver (contains default literals by design)
        if rel.startswith("scripts/safety/") or rel in ("config/paths.py",):
            continue
        p = REPO / rel
        try:
            lines = p.read_text(errors="replace").splitlines()
        except OSError:
            continue
        for i, line in enumerate(lines, 1):
            if not WRITE_OPS.search(line):
                continue
            for tok in FORBIDDEN_TOKENS:
                if tok in line:
                    sev = "BLOCKER" if tok in ("strategy_rules", "catalog", "receiver", "telegram", ".plist", "launchctl") else "WARNING"
                    findings.append({
                        "severity": sev, "check": "forbidden_paths", "file": rel, "line": i,
                        "pattern": tok, "reason": f"write/destructive op referencing forbidden target '{tok}'",
                        "action": "verify not touching production/runtime/RAW; gate behind explicit approval",
                    })
                    break
    return findings


if __name__ == "__main__":
    fs = run()
    for f in fs:
        print(f"{f['severity']:8} {f['file']}:{f['line']} [{f['pattern']}] {f['reason']}")
    print(f"\n{len(fs)} finding(s). REPORT-ONLY (exit 0).")
    sys.exit(0)
