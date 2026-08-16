#!/usr/bin/env python3
"""GS1 — MANIFEST-FIRST para labs XAU SHORT (Cris 2026-08-16, playbook Núcleo 6).
BLOQUEIA (exit 2) correr um script de lab SHORT (medição/scan/detetor/backtest) SEM um GATE MANIFEST declarado
no dir do lab (ou pai). Regra-mãe do XAU_15M_RESEARCH_EXECUTION_PROTOCOL_V1: 'no manifest = no lab' — força a
estrutura (raw_source + structural_buckets + claim_ledger) ANTES de qualquer medição. Fecha os erros mais caros
da construção: correr sem estrutura + overfit sem plano. Consome o protocolo (templates docs/templates/), não
duplica os check_xau_15m_*. Núcleo decide() puro = testável. py3 stdlib."""
import sys, json, re
from pathlib import Path

# scripts de lab SHORT (path/comando)
SHORT = re.compile(r"xau_short|xau_15m_short|short_lab|xau15m_short", re.I)
# só a MEDIÇÃO formal exige manifest (não readers/plots/utils exploratórios)
MEASURE = re.compile(r"backtest|census|scan|detector|detet|engine|metric|panel|expectanc|outcome|null|recall", re.I)
MANIFEST_GLOBS = ("*GATE_MANIFEST*.md", "*_MANIFEST*.md", "manifest.json")


def decide(cmd):
    """(ok, msg) puro."""
    low = (cmd or "").lower()
    if "lab_bootstrap" in low:                    # escape auditável (criar manifest / bootstrap)
        return True, ""
    m = re.search(r"python3?\s+(\S+\.py)", cmd or "")
    if not m:
        return True, ""
    script = m.group(1)
    if not (SHORT.search(script) or SHORT.search(low)):
        return True, ""
    # exime utilitários/exploração (não são a medição formal)
    if any(x in low for x in ("--selftest", "--show", "raw_reader", "plot_", "read_", "inv_", "/hooks/")):
        return True, ""
    if not MEASURE.search(script) and not MEASURE.search(low):
        return True, ""
    # há GATE MANIFEST no dir do script ou num pai (até 4 níveis)?
    p = Path(script)
    for d in [p.parent] + list(p.parents)[:4]:
        for g in MANIFEST_GLOBS:
            try:
                if any(d.glob(g)):
                    return True, ""
            except Exception:
                pass
    return False, (
        "🛑 GS1 — LAB SHORT SEM MANIFEST (Cris 2026-08-16, playbook)\n"
        f"  Estás a correr uma MEDIÇÃO de lab SHORT ({Path(script).name}) sem um GATE MANIFEST no dir do lab.\n"
        "  Regra-mãe do protocolo: SEM manifest (raw_source + structural_buckets + claim_ledger), NENHUM lab.\n"
        "  → cria o manifest a partir de docs/templates/XAU_15M_LAB_GATE_MANIFEST_TEMPLATE.md no dir do lab.\n"
        "  → bootstrap/criação do próprio manifest ou util exploratório: declara 'LAB_BOOTSTRAP: <razão>'.\n"
        "  (Bloqueio determinístico — força estrutura-primeiro, o erro mais caro da construção.)\n")


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0
    if data.get("tool_name") not in (None, "Bash"):
        return 0
    cmd = ((data.get("tool_input") or {}).get("command")) or ""
    ok, msg = decide(cmd)
    if ok:
        return 0
    try:
        import _guard_log; _guard_log.fire("gs1_short_manifest", "block", "lab SHORT sem manifest")
    except Exception:
        pass
    sys.stderr.write(msg)
    return 2


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        t = []
        # 1) backtest SHORT sem manifest (dir sem manifest) → BLOQUEIA
        ok, _ = decide("python3 research/xau_15m_short/short_backtest.py")
        t.append(("backtest SHORT sem manifest bloqueia", ok is False))
        # 2) escape LAB_BOOTSTRAP → passa
        ok, _ = decide("python3 research/xau_15m_short/short_backtest.py  # LAB_BOOTSTRAP: criar manifest")
        t.append(("LAB_BOOTSTRAP passa", ok is True))
        # 3) reader exploratório (--show) → passa (não é medição)
        ok, _ = decide("python3 research/xau_15m_short/reader_replay_v3.py --show")
        t.append(("reader --show passa", ok is True))
        # 4) script NÃO-short → passa
        ok, _ = decide("python3 research/xau_4h_long/cp_engine.py")
        t.append(("nao-short passa", ok is True))
        # 5) selftest de um script short → passa
        ok, _ = decide("python3 research/xau_15m_short/short_detector.py --selftest")
        t.append(("--selftest passa", ok is True))
        # 6) medição com manifest presente (usa /tmp com manifest) → passa
        import tempfile, os as _os
        d = tempfile.mkdtemp(prefix="xau_short_lab_")
        open(_os.path.join(d, "XAU_15M_SHORT_GATE_MANIFEST.md"), "w").write("{}")
        ok, _ = decide(f"python3 {d}/short_backtest.py")
        t.append(("com manifest no dir passa", ok is True))
        for lab, r in t:
            print("  [%s] %s" % ("OK" if r else "FAIL", lab))
        allok = all(r for _, r in t)
        print("selftest", "PASS" if allok else "FAIL")
        sys.exit(0 if allok else 1)
    sys.exit(main())
