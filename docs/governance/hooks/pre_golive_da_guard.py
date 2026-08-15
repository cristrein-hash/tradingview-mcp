#!/usr/bin/env python3
"""G1 — PRE-GO-LIVE DEVIL'S-ADVOCATE GATE (Cris 2026-08-11).
BLOQUEIA (exit 2) um `git commit` que altera LÓGICA DE SINAL LIVE sem declarar um DA na mensagem do commit.
Fecha o erro-raiz S4 do catálogo: "construir/ligar live antes de validar" (commitei+liguei a
polaridade/FVG/anchor antes de o DA confirmar — 3× só no dia 10/08).

O hook do DA existente é PostToolUse (avisa DEPOIS). Este é PreToolUse: PARA o commit antes.

Passa se:
  - o commit NÃO toca ficheiros de lógica de sinal (docs/memória/research/estudos = livres), OU
  - a mensagem do commit contém `DA_OK` (DA feito e referido) ou `NO_DA_NEEDED:<razão>` (fix de ops/infra,
    escape AUDITÁVEL — obriga a declarar, não a esquecer).

LEDGER REMOVIDO (Cris 2026-08-15): o mecanismo de `da_ledger.jsonl` estava MORTO — nunca foi escrito (ledger
vazio); todos os go-lives passavam pelo token na mensagem de commit. Manter dois caminhos e usar só um = dívida.
Fica o token, que funciona e é auditável no histórico do git.
Núcleo `decide()` puro = testável. py3 stdlib."""
import sys, re, json, subprocess
from pathlib import Path

# ficheiros cuja alteração muda SINAL/DETEÇÃO live → exige DA
PROTECTED = [
    r"alert-bridge/(entry_validator|vela_no_nivel|candle_reader|ob_watch|polarity_tracker|price_sentinel|e1_detector|e2_quality|claude_recheck)\.py$",
    r"strategies/.*(runtime|_cycle|scanner|detector)\.py$",
    r"my-strategy/core/.*(price_shock|regime|entry_router|bar_store).*\.py$",
    r"a1_causal_entry\.py$",
]
# nunca exige DA (dados/estudos/docs/testes/memória)
EXEMPT = [r"/research/", r"/docs/", r"\.md$", r"_study", r"a1a2_fvg_lab", r"/tests?/", r"selftest",
          r"trader_map\.json$", r"/seeds/", r"\.jsonl$", r"__pycache__"]


def is_protected(path):
    if any(re.search(p, path) for p in EXEMPT):
        return False
    return any(re.search(p, path) for p in PROTECTED)


def decide(command, staged):
    """Devolve (ok: bool, msg: str). Puro — sem I/O."""
    # só age em git commit
    if not re.search(r"\bgit\s+commit\b", command):
        return True, ""
    prot = [f for f in staged if is_protected(f)]
    if not prot:
        return True, ""
    # escape auditável na mensagem do commit
    if re.search(r"\bDA_OK\b", command) or re.search(r"NO_DA_NEEDED\s*:", command):
        return True, ""
    lst = "\n  ".join(sorted({Path(f).name for f in prot}))
    return False, (
        "🛑 G1 — GO-LIVE SEM DEVIL'S-ADVOCATE (Cris 2026-08-11)\n"
        f"  Este commit altera LÓGICA DE SINAL LIVE sem declarar um DA:\n  {lst}\n"
        "  RAIZ S4: commitar/ligar live antes de validar (polaridade/FVG/anchor no dia 10/08).\n"
        "  → Corre um Devil's Advocate sobre a mudança e refere-o com a tag DA_OK na mensagem do commit.\n"
        "  → OU, se for fix de OPS/infra (não muda edge/sinal), declara na mensagem: NO_DA_NEEDED: <razão>\n"
        "  (Bloqueio determinístico — auto-disciplina de LLM não segura; ver RECURRING_ERROR_CATALOG.)\n")


def _staged_files():
    try:
        r = subprocess.run(["git", "diff", "--cached", "--name-only"], capture_output=True, text=True, timeout=10)
        return [l.strip() for l in r.stdout.splitlines() if l.strip()]
    except Exception:
        return []


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0
    if data.get("tool_name") not in (None, "Bash"):
        return 0
    cmd = ((data.get("tool_input") or {}).get("command")) or ""
    if not re.search(r"\bgit\s+commit\b", cmd):
        return 0
    ok, msg = decide(cmd, _staged_files())
    if ok:
        return 0
    try:
        import _guard_log; _guard_log.fire("pre_golive_da", "block", msg.split("\n")[0][:120])
    except Exception:
        pass
    sys.stderr.write(msg)
    return 2


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        t = []
        # 1) commit de sinal sem DA → BLOQUEIA
        ok, _ = decide('git commit -m "muda polarity"', ["alert-bridge/polarity_tracker.py"])
        t.append(("sinal sem DA bloqueia", ok is False))
        # 2) NO_DA_NEEDED escape → passa
        ok, _ = decide('git commit -m "fix cooldown NO_DA_NEEDED: ops anti-spam"', ["alert-bridge/entry_validator.py"])
        t.append(("NO_DA_NEEDED passa", ok is True))
        # 3) DA_OK tag → passa
        ok, _ = decide('git commit -m "polarity DA_OK verdicto refutado"', ["alert-bridge/polarity_tracker.py"])
        t.append(("DA_OK passa", ok is True))
        # 4) commit de doc/estudo → passa (não protegido)
        ok, _ = decide('git commit -m "doc"', ["docs/governance/x.md", "my-strategy/research/revalidation/a1a2_fvg_lab/study_v9.py"])
        t.append(("doc/estudo passa", ok is True))
        # 5) não é git commit → passa
        ok, _ = decide('git status', ["alert-bridge/polarity_tracker.py"])
        t.append(("nao-commit passa", ok is True))
        for lab, r in t:
            print(f"  [{'OK' if r else 'FAIL'}] {lab}")
        allok = all(r for _, r in t)
        print("selftest", "PASS" if allok else "FAIL")
        sys.exit(0 if allok else 1)
    sys.exit(main())
