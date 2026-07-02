#!/usr/bin/env python3
"""check_slim_policy.py — REPORT-ONLY Agentic OS safety scanner.

Flags SLIM used as data/validation. Historical/authorized contexts are classified
INFO (not error): docs/cleanup, incident docs, files carrying the HISTORICAL_COMPATIBILITY
banner, and the _source_guard that FORBIDS slim. Read-only, exit 0.
"""
from __future__ import annotations
import re, subprocess, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SLIM = re.compile(r"slim_feature|slim_features|\bSLIM\b|\bslim\b")
# lines that consume slim as input/validation (the forbidden use)
CONSUME = re.compile(r"slim_features|SLIM_BASE|SLIM_ROOT|load_slim|slim_schema")


def tracked():
    out = subprocess.run(["git", "-C", str(REPO), "ls-files"], capture_output=True, text=True).stdout
    return [r for r in out.splitlines() if r.endswith((".py", ".md"))]


def run():
    findings = []
    for rel in tracked():
        if rel.startswith("scripts/safety/"):
            continue
        p = REPO / rel
        try:
            text = p.read_text(errors="replace")
        except OSError:
            continue
        if not SLIM.search(text):
            continue
        historical = (
            rel.startswith("docs/cleanup/") or "INCIDENT" in rel.upper()
            or "HISTORICAL_COMPATIBILITY" in text or "DO_NOT_USE_SLIM" in text
            or "SLIM_MODE_FORBIDDEN" in text or "_source_guard" in rel
            or "never_use_slim" in rel.lower()
        )
        for i, line in enumerate(text.splitlines(), 1):
            if not CONSUME.search(line):
                continue
            if historical:
                sev, reason = "INFO", "SLIM reference in authorized historical/guard context (allowed)"
            elif rel.startswith("docs/"):
                sev, reason = "INFO", "SLIM mentioned in documentation"
            else:
                sev, reason = "WARNING", "SLIM consumed as data/validation — forbidden as validation source"
            findings.append({"severity": sev, "check": "slim_policy", "file": rel, "line": i,
                             "pattern": "slim", "reason": reason,
                             "action": "SLIM never validates; use RAW/source. Historical=keep as INFO."})
            break  # one finding per file is enough for the report
    return findings


if __name__ == "__main__":
    fs = run()
    for f in fs:
        print(f"{f['severity']:8} {f['file']}:{f['line']} {f['reason']}")
    print(f"\n{len(fs)} finding(s). REPORT-ONLY (exit 0).")
    sys.exit(0)
