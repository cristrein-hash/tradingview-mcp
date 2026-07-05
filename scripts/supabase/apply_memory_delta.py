#!/usr/bin/env python3
"""APLICADOR GUARDIÃO de deltas de memória no Supabase (2026-07-05, autorizado Cris).
Único caminho de ESCRITA autônoma no Supabase. O MCP interativo permanece read-only
(validação). Controle = guardas deste script, não confiança.

USO:
  python3 scripts/supabase/apply_memory_delta.py supabase/seeds/memory_delta_<nome>.sql
  python3 scripts/supabase/apply_memory_delta.py --validate-only <seed.sql>

GUARDAS (todas obrigatórias, falha = aborta sem tocar o banco):
  G1 ficheiro em supabase/seeds/ com padrão memory_delta_*.sql
  G2 ficheiro COMMITADO no git (git ls-files) — seed primeiro no repo, depois no banco
  G3 corpo = exatamente 1 INSERT em tabela permitida (memory_items | decisions | artifacts)
  G4 idempotência: 'on conflict (id) do nothing' presente
  G5 toda row carrega tag 'seed:<stem do ficheiro>' (verificado por contagem de ocorrências)
  G6 zero verbos proibidos: delete/update/drop/alter/truncate/grant/revoke/create
  G7 pós-aplicação: read-back por tag; n_rows lido == n_values do seed, senão alerta
AUDITORIA: linha em supabase/seeds/APPLY_LOG.md a cada aplicação (data, seed, rows, resultado).
SEGREDO: SUPABASE_ACCESS_TOKEN só do env; nunca impresso, nunca gravado.
"""
import json, os, re, subprocess, sys, urllib.request
import datetime as dt
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PROJECT_REF = "vgfofofozptrtjvtuyzy"          # trading-system-memory (DEV)
API = f"https://api.supabase.com/v1/projects/{PROJECT_REF}/database/query"
ALLOWED_TABLES = ("memory_items", "decisions", "artifacts")
FORBIDDEN = re.compile(r"\b(delete|update|drop|alter|truncate|grant|revoke|create)\b", re.I)


def die(msg):
    print(f"ABORT: {msg}")
    sys.exit(1)


def strip_sql(text):
    text = re.sub(r"--[^\n]*", "", text)
    text = text.replace("begin;", "").replace("commit;", "")
    return text.strip().rstrip(";").strip()


def run_query(token, sql):
    req = urllib.request.Request(
        API, data=json.dumps({"query": sql}).encode(),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json",
                 "User-Agent": "tradingview-mcp-memory-applier/1.0"},
        method="POST")
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode() or "null")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    validate_only = "--validate-only" in sys.argv
    if len(args) != 1:
        die("uso: apply_memory_delta.py [--validate-only] supabase/seeds/memory_delta_<nome>.sql")
    seed = (REPO / args[0]).resolve() if not Path(args[0]).is_absolute() else Path(args[0])

    # G1
    if seed.parent != (REPO / "supabase" / "seeds").resolve() or not re.fullmatch(r"memory_delta_[a-z0-9_]+\.sql", seed.name):
        die(f"G1: seed fora de supabase/seeds/ ou nome inválido: {seed.name}")
    tag = f"seed:{seed.stem}"
    # G2
    tracked = subprocess.run(["git", "ls-files", "--error-unmatch", str(seed.relative_to(REPO))],
                             cwd=REPO, capture_output=True)
    if tracked.returncode != 0:
        die("G2: seed não commitado no git — commit primeiro, banco depois")
    body = strip_sql(seed.read_text())
    code_only = re.sub(r"'(?:[^']|'')*'", "''", body)   # literais fora das guardas de sintaxe
    # G3
    stmts = [s for s in code_only.split(";") if s.strip()]
    if len(stmts) != 1:
        die(f"G3: esperado exatamente 1 statement, encontrados {len(stmts)}")
    m = re.match(r"insert\s+into\s+(\w+)\s*\(", body, re.I)
    if not m or m.group(1) not in ALLOWED_TABLES:
        die(f"G3: statement não é INSERT em tabela permitida {ALLOWED_TABLES}")
    table = m.group(1)
    # G4
    if not re.search(r"on\s+conflict\s*\(\s*id\s*\)\s*do\s+nothing", code_only, re.I):
        die("G4: falta 'on conflict (id) do nothing'")
    # G5
    n_rows = len(re.findall(r"md5\('", body))
    n_tagged = body.count(f"'{tag}'")
    if n_rows == 0 or n_tagged < n_rows:
        die(f"G5: {n_rows} rows mas só {n_tagged} carregam a tag '{tag}'")
    # G6
    bad = FORBIDDEN.search(code_only)
    if bad:
        die(f"G6: verbo proibido no seed: {bad.group(0)}")
    print(f"GUARDAS G1-G6 PASS · seed {seed.name} · tabela {table} · rows {n_rows} · tag {tag}")
    if validate_only:
        print("--validate-only: não aplicado.")
        return

    token = os.environ.get("SUPABASE_ACCESS_TOKEN")
    if not token:
        die("SUPABASE_ACCESS_TOKEN ausente do ambiente")
    before = run_query(token, f"select count(*) n from {table}")[0]["n"]
    run_query(token, body)
    after = run_query(token, f"select count(*) n from {table}")[0]["n"]
    got = run_query(token, f"select count(*) n from {table} where tags @> array['{tag}']")[0]["n"]
    status = "OK" if got == n_rows else f"ALERTA got={got}!=seed={n_rows}"
    print(f"APLICADO: {table} {before}→{after} · rows com tag: {got}/{n_rows} · {status}")
    log = REPO / "supabase" / "seeds" / "APPLY_LOG.md"
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    entry = f"- {stamp} · `{seed.name}` · {table} {before}→{after} · tag-rows {got}/{n_rows} · {status}\n"
    log.write_text((log.read_text() if log.exists() else "# APPLY LOG — deltas de memória Supabase\n\n") + entry)
    if got != n_rows:
        sys.exit(2)


if __name__ == "__main__":
    main()
