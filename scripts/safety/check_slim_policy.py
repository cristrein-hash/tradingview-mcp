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
# a .md that PRESCRIBES slim as validation/source (dangerous) vs merely describing it (allowed doc)
DANGEROUS_MD = re.compile(
    r"(use|usar|com)\s+slim.*(valid|gate|source)|slim.*(as|como)\s+(source of truth|validation|valida)", re.I)
# negation/forbidding context: the line STATES the policy (slim forbidden), it does not prescribe slim
NEG_MD = re.compile(r"proib|forbidden|nunca|never|n[aã]o\s+usar|not\s+use|do_not|n[aã]o\s+[ée]\s+valid|jamais|sem\s+slim", re.I)
# D1A RAW-in-memory: build_entry_anatomy etc. reuse the AUDITED interpreter on RAW (allowed; SLIM-file mode NOT used).
# Do NOT touch D1A/Breakout Continuation; classify as INFO via allowlist.
D1A_RAW_INMEM_PREFIX = "my-strategy/research/revalidation/XAU_4H_BREAKOUT_D1A/"
# Guardrail memory-card filename referenced as a string (e.g. memory seed generators listing
# feedback_never_use_slim_features.md): the card FORBIDS slim — the reference is not consumption.
# Per-LINE rule (not per-file): a guardrail filename never masks real consumption elsewhere in the file.
GUARDRAIL_CARD = re.compile(r"never_use_slim[a-z_]*\.md")


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
            or rel.startswith(D1A_RAW_INMEM_PREFIX)  # RAW-in-memory audited interpreter (allowed; do not touch D1A)
        )
        is_md = rel.endswith(".md")
        for i, line in enumerate(text.splitlines(), 1):
            if not CONSUME.search(line):
                continue
            if GUARDRAIL_CARD.search(line):
                findings.append({"severity": "INFO", "check": "slim_policy", "file": rel, "line": i,
                                 "pattern": "slim",
                                 "reason": "SLIM occurrence is a guardrail memory-card filename (card FORBIDS slim) — allowed",
                                 "action": "Reference to the no-slim guardrail card; keep scanning for real consumption."})
                continue  # do NOT break: guardrail reference must not mask real consumption below
            if historical:
                sev, reason = "INFO", "SLIM reference in authorized historical/guard/RAW-in-memory context (allowed)"
            elif is_md:
                if DANGEROUS_MD.search(line) and not NEG_MD.search(line):
                    sev, reason = "WARNING", "documentation appears to PRESCRIBE SLIM as validation/source — review"
                else:
                    sev, reason = "INFO", "SLIM described in documentation (non-executable)"
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
