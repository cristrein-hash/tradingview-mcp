#!/usr/bin/env python3
"""run_safety_report.py — REPORT-ONLY aggregator for the Agentic OS safety layer.

Runs check_forbidden_paths + check_slim_policy + check_hardcoded_product_paths and
prints a single severity table + summary. ALWAYS exit 0 (report-only; never blocks).
Usage: python scripts/safety/run_safety_report.py
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_forbidden_paths, check_slim_policy, check_hardcoded_product_paths  # noqa: E402

SEV_ORDER = {"BLOCKER": 0, "WARNING": 1, "INFO": 2, "ALLOWED_WITH_APPROVAL": 3}


def main():
    findings = []
    for mod in (check_forbidden_paths, check_slim_policy, check_hardcoded_product_paths):
        try:
            findings.extend(mod.run())
        except Exception as e:  # a scanner error must not break the report
            print(f"[scanner error in {mod.__name__}: {e}]")
    # AUDIT 19/08 (RC1): invariante "sender Telegram único" — regressão = BLOCKER no report
    try:
        import subprocess as _sp
        r = _sp.run([sys.executable, str(Path(__file__).resolve().parent / "check_single_telegram_sender.py")],
                    capture_output=True, text=True)
        if r.returncode != 0:
            for ln in r.stdout.splitlines():
                if ln.strip().startswith(("alert-bridge", "my-strategy", "external_factors", "copilot", " ")):
                    findings.append({"severity": "BLOCKER", "check": "single_telegram_sender",
                                     "file": ln.strip(), "reason": "sender fora do notify.py (allowlist)"})
    except Exception as e:
        print(f"[scanner error in check_single_telegram_sender: {e}]")
    # AUDIT 21/08: contrato SL-first (same-bar => LOSS em todas as implementações)
    try:
        import subprocess as _sp2
        r2 = _sp2.run([sys.executable, str(Path(__file__).resolve().parent / "check_sl_first_contract.py")],
                      capture_output=True, text=True)
        if r2.returncode != 0:
            findings.append({"severity": "BLOCKER", "check": "sl_first_contract",
                             "file": "ver check_sl_first_contract.py", "reason": r2.stdout.strip()[:120]})
    except Exception as e:
        print(f"[scanner error in check_sl_first_contract: {e}]")
    findings.sort(key=lambda f: (SEV_ORDER.get(f["severity"], 9), f["check"], f["file"], f.get("line", 0)))

    print("=" * 100)
    print("AGENTIC OS — SAFETY REPORT (report-only, exit 0)")
    print("=" * 100)
    print(f"{'SEVERITY':9} {'CHECK':24} {'FILE:LINE':52} REASON")
    print("-" * 100)
    for f in findings:
        loc = f"{f['file']}:{f.get('line','')}"
        print(f"{f['severity']:9} {f['check']:24} {loc:52.52} {f['reason']}")

    counts = {}
    for f in findings:
        counts[f["severity"]] = counts.get(f["severity"], 0) + 1
    print("-" * 100)
    print("SUMMARY:", ", ".join(f"{k}={counts.get(k,0)}" for k in ("BLOCKER", "WARNING", "INFO")) or "none",
          f"| total={len(findings)}")
    print("Mode: REPORT-ONLY. Nothing blocked. See docs/governance/SAFETY_LAYER_USAGE.md.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
