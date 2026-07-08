#!/usr/bin/env python3
"""RUNNER unico do gate de labs XAU 15M (XAU_15M_RESEARCH_EXECUTION_PROTOCOL_V1 §Stage10).
Executa, em ordem: RAW lineage -> structural-first -> claims ledger -> safety report.
Sem 'XAU_15M_LAB_GATE_PASS' deste runner, NENHUM lab 15M pode ser declarado completo/aprovado.

Uso:
  python scripts/safety/run_xau_15m_lab_gate.py --manifest <m.md> --report <r.md> --ledger <l.csv> [--results a.csv b.csv]

Exit 0 = XAU_15M_LAB_GATE_PASS ; exit 1 = FAIL (lista qual etapa bloqueou)."""
import sys, os, subprocess, argparse

HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable

def run(desc, argv):
    print(f"\n=== {desc} ===")
    try:
        r = subprocess.run([PY] + argv, capture_output=True, text=True, timeout=300)
    except Exception as e:
        print(f"  ERRO ao executar: {e}"); return False, desc
    out = (r.stdout or "") + (r.stderr or "")
    print(out.rstrip())
    return r.returncode == 0, desc

def main():
    ap = argparse.ArgumentParser(description="RUNNER do gate canonico de labs XAU 15M (protocolo V1): lineage + structural-first + claims + safety.")
    ap.add_argument("--manifest", required=True, help="GATE MANIFEST do lab (.md com bloco json)")
    ap.add_argument("--report", required=True, help="relatorio do lab (.md)")
    ap.add_argument("--ledger", required=True, help="claims ledger (.csv)")
    ap.add_argument("--results", nargs="*", default=[], help="CSV(s) de output do lab (opcional; senao usa manifest.outputs)")
    ap.add_argument("--strict-existence", action="store_true", help="FAIL se RAW file /Volumes ausente")
    a = ap.parse_args()

    stages = []
    lin = [os.path.join(HERE, "check_xau_15m_raw_lineage.py"), "--manifest", a.manifest]
    if a.strict_existence: lin.append("--strict-existence")
    stages.append(("RAW lineage / source guard", lin))
    sf = [os.path.join(HERE, "check_xau_15m_structural_first.py"), "--manifest", a.manifest, "--report", a.report]
    if a.results: sf += ["--results"] + a.results
    stages.append(("Structural-first (regime+leg+family)", sf))
    stages.append(("Claims ledger", [os.path.join(HERE, "check_xau_15m_claims_ledger.py"), "--report", a.report, "--ledger", a.ledger]))
    safety = os.path.join(HERE, "run_safety_report.py")
    if os.path.exists(safety): stages.append(("Safety report", [safety]))

    results = [run(d, argv) for d, argv in stages]
    failed = [d for ok, d in results if not ok]
    print("\n" + "=" * 60)
    if failed:
        print("XAU_15M_LAB_GATE_FAIL")
        for d in failed: print(f"  BLOQUEADO em: {d}")
        print("  -> lab NAO pode ser declarado completo. Corrigir e re-correr.")
        return 1
    print("XAU_15M_LAB_GATE_PASS")
    print("  -> lineage + structural-first + claims + safety OK. Lab pode prosseguir p/ report/commit.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
