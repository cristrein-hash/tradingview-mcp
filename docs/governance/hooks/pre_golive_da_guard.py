#!/usr/bin/env python3
"""G1 — PRE-GO-LIVE DEVIL'S-ADVOCATE GATE (Cris 2026-08-11).
BLOQUEIA (exit 2) um `git commit` que altera LÓGICA DE SINAL LIVE sem um DA registado no ledger para essa
mudança. Fecha o erro-raiz S4 do catálogo: "construir/ligar live antes de validar" (commitei+liguei a
polaridade/FVG/anchor antes de o DA confirmar — 3× só no dia 10/08).

O hook do DA existente é PostToolUse (avisa DEPOIS). Este é PreToolUse: PARA o commit antes.

Passa se:
  - o commit NÃO toca ficheiros de lógica de sinal (docs/memória/research/estudos = livres), OU
  - a mensagem do commit contém `DA_OK` (DA feito e referido) ou `NO_DA_NEEDED:<razão>` (fix de ops/infra,
    escape AUDITÁVEL — obriga a declarar, não a esquecer), OU
  - há entrada fresca (<6h) no DA ledger (~/.claude/da_ledger.jsonl) cobrindo um dos ficheiros de sinal do commit.
Núcleo `decide()` puro = testável. py3 stdlib."""
import sys, os, re, json, time, subprocess
from pathlib import Path

LEDGER = Path.home() / ".claude" / "da_ledger.jsonl"
FRESH_S = 6 * 3600

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


def load_ledger(now):
    out = []
    try:
        for l in LEDGER.read_text().splitlines():
            if not l.strip():
                continue
            try:
                e = json.loads(l)
            except Exception:
                continue
            if now - (e.get("ts") or 0) < FRESH_S:
                out.append(e)
    except Exception:
        pass
    return out


def decide(command, staged, ledger, now):
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
    # DA ledger fresco (<FRESH_S) cobrindo um dos ficheiros de sinal
    prot_base = {Path(f).name for f in prot}
    for e in ledger:
        if now - (e.get("ts") or 0) >= FRESH_S:      # DA velho não conta
            continue
        files = {Path(x).name for x in (e.get("files") or [])}
        if prot_base & files:
            return True, ""
    lst = "\n  ".join(sorted(prot_base))
    return False, (
        "🛑 G1 — GO-LIVE SEM DEVIL'S-ADVOCATE (Cris 2026-08-11)\n"
        f"  Este commit altera LÓGICA DE SINAL LIVE sem um DA registado:\n  {lst}\n"
        "  RAIZ S4: commitar/ligar live antes de validar (polaridade/FVG/anchor no dia 10/08).\n"
        "  → Corre um Devil's Advocate sobre a mudança e REGISTA-o:\n"
        "     python3 ~/.claude/hooks/pre_golive_da_guard.py --record <ficheiro.py> \"<verdicto do DA>\"\n"
        "  → OU, se for fix de OPS/infra (não muda edge/sinal), declara na mensagem: NO_DA_NEEDED: <razão>\n"
        "  → OU refere o DA já feito com a tag DA_OK na mensagem do commit.\n"
        "  (Bloqueio determinístico — auto-disciplina de LLM não segura; ver RECURRING_ERROR_CATALOG.)\n")


def _staged_files():
    try:
        r = subprocess.run(["git", "diff", "--cached", "--name-only"], capture_output=True, text=True, timeout=10)
        return [l.strip() for l in r.stdout.splitlines() if l.strip()]
    except Exception:
        return []


def record(files, verdict):
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    entry = {"ts": int(time.time()), "files": files, "verdict": verdict[:300]}
    with open(LEDGER, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"DA registado no ledger: {files}")


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--record":
        record([sys.argv[2]] if len(sys.argv) > 2 else [], " ".join(sys.argv[3:]))
        return 0
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0
    if data.get("tool_name") not in (None, "Bash"):
        return 0
    cmd = ((data.get("tool_input") or {}).get("command")) or ""
    if not re.search(r"\bgit\s+commit\b", cmd):
        return 0
    ok, msg = decide(cmd, _staged_files(), load_ledger(time.time()), time.time())
    if ok:
        return 0
    sys.stderr.write(msg)
    return 2


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        now = 1000000
        led_fresh = [{"ts": now - 100, "files": ["polarity_tracker.py"], "verdict": "ok"}]
        led_old = [{"ts": now - 7 * 3600, "files": ["polarity_tracker.py"], "verdict": "ok"}]
        t = []
        # 1) commit de sinal sem DA → BLOQUEIA
        ok, _ = decide('git commit -m "muda polarity"', ["alert-bridge/polarity_tracker.py"], [], now)
        t.append(("sinal sem DA bloqueia", ok is False))
        # 2) commit de sinal com DA ledger fresco → passa
        ok, _ = decide('git commit -m "muda polarity"', ["alert-bridge/polarity_tracker.py"], led_fresh, now)
        t.append(("sinal com DA fresco passa", ok is True))
        # 3) ledger velho (>6h) → bloqueia
        ok, _ = decide('git commit -m "muda polarity"', ["alert-bridge/polarity_tracker.py"], led_old, now)
        t.append(("DA velho bloqueia", ok is False))
        # 4) NO_DA_NEEDED escape → passa
        ok, _ = decide('git commit -m "fix cooldown NO_DA_NEEDED: ops anti-spam"', ["alert-bridge/entry_validator.py"], [], now)
        t.append(("NO_DA_NEEDED passa", ok is True))
        # 5) DA_OK tag → passa
        ok, _ = decide('git commit -m "polarity DA_OK verdicto refutado"', ["alert-bridge/polarity_tracker.py"], [], now)
        t.append(("DA_OK passa", ok is True))
        # 6) commit de doc/estudo → passa (não protegido)
        ok, _ = decide('git commit -m "doc"', ["docs/governance/x.md", "my-strategy/research/revalidation/a1a2_fvg_lab/study_v9.py"], [], now)
        t.append(("doc/estudo passa", ok is True))
        # 7) não é git commit → passa
        ok, _ = decide('git status', ["alert-bridge/polarity_tracker.py"], [], now)
        t.append(("nao-commit passa", ok is True))
        for lab, r in t:
            print(f"  [{'OK' if r else 'FAIL'}] {lab}")
        allok = all(r for _, r in t)
        print("selftest", "PASS" if allok else "FAIL")
        sys.exit(0 if allok else 1)
    sys.exit(main())
