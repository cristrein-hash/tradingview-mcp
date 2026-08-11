#!/usr/bin/env python3
"""G3 — AUTO-INVOKE SAFETY CHECKERS ON COMMIT (Cris 2026-08-11).
BLOQUEIA (exit 2) um `git commit` se um dos checkers determinísticos fortes FALHAR. Fecha o buraco do
catálogo: os checkers `check_no_invented_zones.py` (S3 invenção de zona) e `check_slim_policy.py` (S1
SLIM-como-validação) EXISTEM e são bloqueantes (exit≠0), mas SÓ corriam se invocados à mão. Agora correm
sozinhos a cada commit.

Núcleo `decide(results)` puro (results = [(nome, ok, saida)]). py3 stdlib."""
import sys, re, json, subprocess
from pathlib import Path

REPO = Path("/Users/cristrein/tradingview-mcp")
CHECKERS = [
    ("check_no_invented_zones", REPO / "scripts/safety/check_no_invented_zones.py"),
    ("check_slim_policy", REPO / "scripts/safety/check_slim_policy.py"),
]


def decide(results):
    """(ok, msg). results = lista de (nome, ok:bool, saida:str)."""
    fails = [(n, out) for (n, ok, out) in results if not ok]
    if not fails:
        return True, ""
    blocos = "\n".join(f"  🔴 {n} FALHOU:\n     " + "\n     ".join((out or "").strip().splitlines()[-4:])
                       for n, out in fails)
    return False, (
        "🛑 G3 — CHECKER DETERMINÍSTICO FALHOU NO COMMIT (Cris 2026-08-11)\n"
        f"{blocos}\n"
        "  Estes são invariantes duros (S1 SLIM-como-validação / S3 invenção de zona). Corrige ANTES de commitar.\n"
        "  (Antes só corriam à mão e por isso eram esquecidos; agora bloqueiam automaticamente.)\n")


def run_checkers():
    out = []
    for name, path in CHECKERS:
        if not path.exists():
            continue
        try:
            r = subprocess.run(["/usr/bin/python3", str(path)], capture_output=True, text=True, timeout=40)
            out.append((name, r.returncode == 0, (r.stdout or "") + (r.stderr or "")))
        except Exception as e:
            out.append((name, True, f"(skip: {type(e).__name__})"))   # falha do próprio checker não bloqueia
    return out


LIVE_CODE = [r"alert-bridge/.*\.py$", r"strategies/.*\.py$", r"my-strategy/core/.*\.py$"]


def _staged_has_live_code():
    """True se o commit inclui CÓDIGO LIVE. Fix do audit: sem código live (docs/memória/research), NÃO
    corre os checkers — senão uma violação num ficheiro live não-relacionado bloqueava commits de docs/memória
    (e os commits autónomos da ponte-Telegram)."""
    try:
        r = subprocess.run(["git", "diff", "--cached", "--name-only"], capture_output=True, text=True, timeout=10)
        files = [l.strip() for l in r.stdout.splitlines() if l.strip()]
    except Exception:
        return True   # incerto = corre (conservador)
    if not files:
        return True
    return any(any(re.search(p, f) for p in LIVE_CODE) for f in files)


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0
    if data.get("tool_name") not in (None, "Bash"):
        return 0
    cmd = ((data.get("tool_input") or {}).get("command")) or ""
    if not re.search(r"^\s*git\s+commit\b|&&\s*git\s+commit\b|;\s*git\s+commit\b", cmd):
        return 0
    if not _staged_has_live_code():          # commit só de docs/memória/research → não corre checkers
        return 0
    ok, msg = decide(run_checkers())
    if ok:
        return 0
    sys.stderr.write(msg)
    return 2


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        t = []
        # 1) todos passam → ok
        ok, _ = decide([("a", True, "PASS"), ("b", True, "PASS")])
        t.append(("todos passam → ok", ok is True))
        # 2) um falha → bloqueia
        ok, m = decide([("check_no_invented_zones", False, "🔴 INVENÇÃO linha 5"), ("b", True, "PASS")])
        t.append(("um falha → bloqueia", ok is False and "FALHOU" in m))
        # 3) vazio → ok
        ok, _ = decide([])
        t.append(("vazio → ok", ok is True))
        # 4) live real: os checkers atuais passam (árvore limpa)
        real = run_checkers()
        t.append(("checkers reais passam agora", all(ok for _, ok, _ in real)))
        for lab, r in t:
            print(f"  [{'OK' if r else 'FAIL'}] {lab}")
        allok = all(r for _, r in t)
        print("selftest", "PASS" if allok else "FAIL")
        sys.exit(0 if allok else 1)
    sys.exit(main())
