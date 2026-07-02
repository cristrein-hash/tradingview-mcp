#!/usr/bin/env python3
"""check_hardcoded_product_paths.py — REPORT-ONLY Agentic OS safety scanner.

Flags personal/external hardcoded paths (/Users/cristrein, /Volumes, persistent /tmp)
ONLY inside PRODUCT-CORE dirs. Research/private are NOT flagged (they may stay hardcoded).
The resolver defaults (config/paths.py, .env.example) are INFO by design. Read-only, exit 0.
"""
from __future__ import annotations
import re, subprocess, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

PRODUCT_DIRS = (
    "src/", "config/", "skills/", "tests/",
    "external_factors_v2/collectors/", "external_factors_v2/config/", "external_factors_v2/agents/",
)
# resolver/whitelist files that legitimately contain the default literals
WHITELIST = {"config/paths.py", ".env.example", "tests/test_paths_resolution.py"}
HARDCODE = re.compile(r"/Users/cristrein|/Volumes/|(['\"])/tmp/")


def tracked():
    out = subprocess.run(["git", "-C", str(REPO), "ls-files"], capture_output=True, text=True).stdout
    return [r for r in out.splitlines() if r.endswith((".py", ".js", ".sh"))]


def run():
    findings = []
    for rel in tracked():
        if not rel.startswith(PRODUCT_DIRS) or rel.startswith("scripts/safety/"):
            continue
        p = REPO / rel
        try:
            lines = p.read_text(errors="replace").splitlines()
        except OSError:
            continue
        for i, line in enumerate(lines, 1):
            m = HARDCODE.search(line)
            if not m:
                continue
            if rel in WHITELIST:
                sev, reason = "INFO", "hardcode is a by-design resolver default / test"
            else:
                sev = "WARNING"
                reason = "personal/external hardcoded path in product-core; migrate to config.paths"
            findings.append({"severity": sev, "check": "hardcoded_product_paths", "file": rel,
                             "line": i, "pattern": m.group(0), "reason": reason,
                             "action": "use CP.repo()/CP.raw()/CP.private()/CP.tmp() for product portability"})
    return findings


if __name__ == "__main__":
    fs = run()
    for f in fs:
        print(f"{f['severity']:8} {f['file']}:{f['line']} [{f['pattern']}] {f['reason']}")
    print(f"\n{len(fs)} finding(s). REPORT-ONLY (exit 0).")
    sys.exit(0)
