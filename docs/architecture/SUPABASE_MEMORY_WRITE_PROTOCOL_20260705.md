# SUPABASE MEMORY — PROTOCOLO DE ESCRITA AUTÔNOMA CONTROLADA

**Data:** 2026-07-05 · **Autorização:** Cris ("quero que consigas subir no Supabase regularmente por ti mesmo e cries padrão de atualização de memória controlado por ti") · **Supersede:** o canon "escrita só Cris/SQL Editor" do checkpoint `SUPABASE_MEMORY_FULL_MIGRATION_CHECKPOINT_20260702.md`.

## Arquitetura (defesa em profundidade)

| Via | Capacidade | Uso |
|-----|-----------|-----|
| MCP `supabase-dev` (`--read-only`) | SELECT apenas (25006 em INSERT) | Validação interativa, consultas |
| `scripts/supabase/apply_memory_delta.py` | INSERT guardado via Management API | **Único caminho de escrita autônoma** |
| SQL Editor (Cris) | Tudo | Rollbacks, UPDATEs/supersede, schema, exceções |

O MCP interativo **permanece read-only de propósito**: a escrita autônoma flui exclusivamente pelo script-guardião, cujas guardas são código, não disciplina. Token: `SUPABASE_ACCESS_TOKEN` do ambiente (nunca impresso/gravado). Projeto: `vgfofofozptrtjvtuyzy` (trading-system-memory DEV).

## Guardas do aplicador (falha = aborta sem tocar o banco)

- **G1** seed em `supabase/seeds/` com padrão `memory_delta_*.sql`
- **G2** seed **commitado no git** antes de aplicar (repo primeiro, banco depois — trilha de auditoria completa)
- **G3** corpo = exatamente 1 `INSERT` em tabela permitida (`memory_items` · `decisions` · `artifacts`)
- **G4** idempotência obrigatória: `on conflict (id) do nothing` + ids `md5(seed_key)::uuid`
- **G5** toda row carrega a tag `seed:<stem-do-ficheiro>` (rollback endereçável)
- **G6** zero verbos fora de INSERT no código SQL (delete/update/drop/alter/truncate/grant/revoke/create) — literais de texto excluídos do scan
- **G7** pós-aplicação: read-back por tag; divergência → exit 2 + ALERTA no log

## Cadência padrão (a cada checkpoint de sessão com fatos novos)

1. Fato novo → card local em `~/.claude/.../memory/` + linha no `MEMORY.md` (como sempre)
2. Destilar em seed `supabase/seeds/memory_delta_<janela>.sql` (títulos/resumos/pointers; **zero RAW/candles, zero secrets, zero parâmetros de edge sensíveis**; ASCII sem acentos; header com ROLLBACK)
3. `git commit + push` do seed
4. `python3 scripts/supabase/apply_memory_delta.py supabase/seeds/<seed>.sql`
5. Validação read-only via MCP (contagem por tag)
6. Linha automática em `supabase/seeds/APPLY_LOG.md` (commitar)

`--validate-only` roda G1-G6 sem tocar o banco (dry-run).

## O que continua exigindo o Cris

- **DELETE / rollback** (`delete from memory_items where tags @> array['seed:<nome>']`) — só com ordem explícita
- **UPDATE / supersede / archive** de rows existentes (mudança de status é decisão de canon)
- **Schema/DDL** — via `apply_migration` + ficheiro de migração commitado + aprovação
- Escrita em qualquer tabela fora de `memory_items`/`decisions`/`artifacts`

## Estado no ato da adoção

- `seed:memory_delta_20260705` (16 rows) aplicado pelo novo caminho: `memory_items` 245→261, read-back 16/16 OK, validado também via MCP read-only.
- Histórico anterior intacto: baseline 240 (2026-07-02, waves manuais) + delta RAW-extension (5 rows, 2026-07-04, aplicado pelo Cris).
