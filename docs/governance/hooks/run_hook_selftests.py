#!/usr/bin/env python3
"""Meta-runner de selftests das guardas de comportamento (Cris 2026-08-15).
Prova DETERMINÍSTICA (sem esperar por disparo live) de que cada guarda bloqueia o que deve e passa o que deve.
Dois modos por guarda:
  (A) selftest NATIVO — corre `python3 hook.py --selftest`, exige 'PASS'.
  (B) BLACK-BOX — alimenta stdin (o mesmo JSON que o Claude Code envia) e exige o exit code certo.
G7 corre com G7_JUDGE=off para ser determinístico (regex-only; o juiz Haiku é não-determinístico e testado à parte).
Uso: python3 ~/.claude/hooks/run_hook_selftests.py    (exit 0 = tudo PASS; !=0 = alguma falhou). py3 stdlib."""
import subprocess, json, sys, os
from pathlib import Path

H = Path.home() / ".claude/hooks"
PY = "/usr/bin/python3"
results = []


def native(name):
    try:
        r = subprocess.run([PY, str(H / f"{name}.py"), "--selftest"], capture_output=True, text=True, timeout=30)
        ok = "PASS" in r.stdout and "FAIL" not in r.stdout.replace("PASS", "")
        results.append((f"{name} [native]", ok, (r.stdout.strip().splitlines() or [""])[-1]))
    except Exception as e:
        results.append((f"{name} [native]", False, f"ERRO {type(e).__name__}: {e}"))


def blackbox(name, stdin_obj, expect_exit, env=None, label=""):
    try:
        e = dict(os.environ)
        if env:
            e.update(env)
        r = subprocess.run([PY, str(H / f"{name}.py")], input=json.dumps(stdin_obj),
                           capture_output=True, text=True, timeout=40, env=e)
        ok = (r.returncode == expect_exit)
        results.append((f"{name} [{label}]", ok, f"exit={r.returncode} esperado={expect_exit}"))
    except Exception as ex:
        results.append((f"{name} [{label}]", False, f"ERRO {type(ex).__name__}: {ex}"))


# (A) selftests nativos das 6 guardas estruturadas
for n in ("pre_golive_da_guard", "stop_price_read_all_tf_guard", "pre_source_citation_guard",
          "pre_commit_checkers_guard", "pre_mcp_action_guard", "pre_daemon_reload_guard"):
    native(n)

# (B) black-box das guardas imperativas (determinístico)
JUDGE_OFF = {"G7_JUDGE": "off"}
# G7: comando exemptado (selftest) → passa
blackbox("pre_analysis_myopia_guard", {"tool_input": {"command": "python3 foo.py --selftest"}}, 0,
         env=JUDGE_OFF, label="G7 selftest passa")
# G7: análise de separação/estrutura (regex-only, judge off) → bloqueia
blackbox("pre_analysis_myopia_guard", {"tool_input": {"command": "python3 /tmp/_nao_existe_sep.py separa estrutura choch"}}, 2,
         env=JUDGE_OFF, label="G7 analise bloqueia")
# G7: aplicador de seed (governança) → passa (exemção (a))
blackbox("pre_analysis_myopia_guard",
         {"tool_input": {"command": "git add x.sql && python3 scripts/supabase/apply_memory_delta.py s.sql estrutura choch"}}, 0,
         env=JUDGE_OFF, label="G7 seed passa")
# pre_approval: promoção OFICIAL sem lookahead-audited → bloqueia
MEMF = "/Users/cristrein/.claude/projects/-Users-cristrein-tradingview-mcp/memory/_x.md"
blackbox("pre_approval_guard", {"tool_name": "Write", "tool_input": {"file_path": MEMF, "content": "status: OFICIAL — promovido a OFICIAL"}}, 2,
         label="promoção bloqueia")
# pre_approval: conteúdo normal → passa
blackbox("pre_approval_guard", {"tool_name": "Write", "tool_input": {"file_path": MEMF, "content": "nota qualquer sem promoção"}}, 0,
         label="normal passa")
# pre_mcp_action: screenshot sem flag → bloqueia
blackbox("pre_mcp_action_guard", {"tool_name": "mcp__tradingview__capture_screenshot", "tool_input": {}}, 2,
         label="screenshot bloqueia")

# ---- relatório ----
allok = all(ok for _, ok, _ in results)
for lab, ok, detail in results:
    print(f"  [{'OK' if ok else 'FAIL'}] {lab:52s} {detail}")
print("META-SELFTEST", "PASS" if allok else "FAIL", f"({sum(1 for _,o,_ in results if o)}/{len(results)})")
sys.exit(0 if allok else 1)
