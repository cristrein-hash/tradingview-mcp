#!/usr/bin/env python3
"""Auditoria periódica dos bypasses SANITY_PROBE do G7 (#3, Cris 2026-08-15).
O bypass é auto-atestado — a razão é o que eu escrever. Este batch NÃO previne (impossível sem verificador
independente); DISSUADE por auditoria: sinaliza bypasses INCOERENTES — aqueles cuja razão declara "não é
análise / commit / selftest / infra" MAS o comando corre um script de análise NÃO-exemptado (i.e. o bypass
mentiu ou o G7 devia ter deixado passar por exemção, não por bypass). Determinístico, sem LLM. Só leitura.
Uso: python3 ~/.claude/hooks/audit_g7_bypasses.py    (lista os suspeitos). py3 stdlib."""
import json, re
from pathlib import Path

LOG = Path.home() / ".claude/hooks/logs/bypass_uses.log"
# frases que declaram "isto não é análise de mercado"
NAO_ANALISE = re.compile(r"não é análise|nao e analise|não é an[aá]lise de mercado|commit|selftest|self-test|infra|governan|seed|aplica", re.I)
# comando corre um .py que NÃO é dos exemptos (então devia ter sido exemção, não bypass — ou a razão é falsa)
EXEMPT = ("apply_memory_delta.py", "/scripts/supabase/", "/scripts/safety/", "check_no_invented",
          "check_slim_policy", "--selftest", "/hooks/", ".claude/hooks")
RUNS_PY = re.compile(r"python3?\s+(\S+\.py)")


def suspicious(entry):
    reason = entry.get("reason", "") or ""
    cmd = entry.get("cmd", "") or ""
    if not NAO_ANALISE.search(reason):
        return None                      # razão não alega "não é análise" → não avaliamos coerência aqui
    scripts = RUNS_PY.findall(cmd)
    if not scripts:
        return None                      # não corre .py → coerente (git puro etc.)
    non_exempt = [s for s in scripts if not any(e in (s + cmd) for e in EXEMPT)]
    if non_exempt:
        return non_exempt                # razão diz "não é análise" mas corre .py não-exemptado = INCOERENTE
    return None


def main():
    if not LOG.exists():
        print("sem bypass_uses.log — nada a auditar.")
        return
    total = 0
    flagged = []
    for l in LOG.read_text().splitlines():
        if not l.strip():
            continue
        try:
            e = json.loads(l)
        except Exception:
            continue
        total += 1
        s = suspicious(e)
        if s:
            flagged.append((e, s))
    print(f"bypasses totais: {total} · INCOERENTES (razão 'não é análise' mas corre .py não-exemptado): {len(flagged)}")
    for e, scripts in flagged:
        import datetime as dt
        ts = dt.datetime.utcfromtimestamp(e.get("ts", 0)).strftime("%m-%d %H:%M")
        print(f"  ⚠ {ts}  razão={e.get('reason','')[:70]!r}")
        print(f"        corre: {scripts}")
    if not flagged:
        print("  ✓ nenhum bypass incoerente — as razões batem com os comandos.")


if __name__ == "__main__":
    main()
