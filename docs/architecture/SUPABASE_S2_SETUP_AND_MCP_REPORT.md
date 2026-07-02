# SUPABASE S2 — SETUP & MCP REPORT (2026-07-02)

**Modo:** read-only recon + docs. **Sem conexão remota, sem aplicar schema, sem migrar dados, sem instalar nada, sem secrets no repo.**
**Projeto DEV (Cris):** `trading-system-memory-dev` · URL `https://vgfofofzptrtjvtuyzy.supabase.co` · ref `vgfofofzptrtjvtuyzy`.

## ⭐ STATUS UPDATE — schema aplicado (Cris, 2026-07-02)
- **Schema APLICADO manualmente** via **Supabase Dashboard → SQL Editor** no projeto **DEV** `trading-system-memory-dev`. `supabase/schema.sql` executado com sucesso.
- **11 tabelas criadas:** `memory_items · decisions · artifacts · agent_runs · safety_reports · external_factor_events · market_context_snapshots · trade_journal_events · episode_context_links · source_registry · retrieval_queries` (+ extensão `pgcrypto`).
- **`memory_embeddings` NÃO criada** — pgvector ficou comentado de propósito (`DEFERRED / pgvector optional`; ativar só se/quando busca semântica for necessária).
- **Nenhum dado inserido.** Nenhum RAW/candle/backtest/log/trade-journal migrado. Bloco **RLS não aplicado** (fica comentado até validação dev + separação anon/service-role).
- **Nenhum secret** no chat/repo. **MCP ainda NÃO configurado.**
- **Próximo passo:** configurar **MCP Supabase project-scoped (`vgfofofzptrtjvtuyzy`) + `--read-only`**, PAT (nunca service role), auth via `/mcp` — **só sob autorização** (plano em §5). Testes iniciais permitidos: `list tables` / `SELECT` simples; sem INSERT/UPDATE/DELETE/migração.

## 1. O que foi verificado (read-only)
CLI/Docker/psql, `.env` gitignore/staging, MCP config, git sync. Nenhum comando de escrita/conexão.

## 2. CLI / local status
| Ferramenta | Estado |
|---|---|
| `supabase` CLI | **NÃO instalado** (`command not found`) |
| `docker` | **NÃO instalado** (daemon indisponível) |
| `psql` | **NÃO instalado** |
- **Consequência:** não é possível `supabase start` (local Postgres) nem aplicar/validar o schema localmente **nesta máquina agora**. **Não instalei nada** (regra: reportar se faltar).

## 3. Cloud project status
- Projeto DEV criado pelo Cris (`vgfofofzptrtjvtuyzy`). **Schema NÃO aplicado** · **sem dados** · **sem conexão do runtime/Claude**. Nada mutado remotamente.

## 4. Schema status
- `supabase/schema.sql` = **draft S1 versionado** (12 tabelas). **Não aplicado** (nem local nem remoto).
- Sem CLI/psql/Docker local → **via de aplicação = manual pelo dashboard** (Cris), quando autorizado (ver §Instruções manuais no `supabase/README.md`). **Não aplicar sem autorização explícita.**

## 5. MCP status & plano
- **Não há** `.mcp.json` nem MCP Supabase configurado. **Nada conectado.**
- **Plano de ligação (NÃO executado):** MCP oficial Supabase, **project-scoped** a `vgfofofzptrtjvtuyzy`, **read-only**, **sem service role**. Auth via `claude /mcp` (browser/PAT) **só quando Cris autorizar**.
  - Comando-plano (a correr só sob autorização; PAT = Personal Access Token, NÃO service role, fora do repo):
    ```
    claude mcp add supabase-dev --scope local -- \
      npx -y @supabase/mcp-server-supabase@latest \
      --read-only --project-ref=vgfofofzptrtjvtuyzy
    # o PAT vai por variável de ambiente/prompt de auth, NUNCA no repo
    ```
  - **Tratar o MCP como write-capable até prova contrária.** `--read-only` reduz risco, mas confirmar comportamento antes de qualquer operação com efeito.
- Qualquer passo que exija token/browser-auth/mutation remota → **PARAR e pedir autorização** (não feito neste bloco).

## 5.b MCP read-only setup — PLAN + capability check (2026-07-02, NÃO executado)
- **Capability check (read-only, sem token/conexão):** `node v25` + `npx 11` + `claude` CLI presentes. Pacote `@supabase/mcp-server-supabase@latest` baixa e parseia args (usa `parseArgs`). Flags `--read-only` e `--project-ref` conforme doc oficial (confirmar no add; se rejeitados → PARAR).
- **Comando proposto (a correr só com PAT + autorização):**
  ```
  claude mcp add supabase-dev -s local -- \
    npx -y @supabase/mcp-server-supabase@latest --read-only --project-ref=vgfofofzptrtjvtuyzy
  # PAT via env SUPABASE_ACCESS_TOKEN — NUNCA no chat/repo/comando visível
  ```
- **Token:** PAT gerado pelo Cris (Account → Access Tokens → `claude-mcp-trading-system-memory-dev-readonly`); passado por env/auth, **nunca colado no chat**; vive na config MCP local (`~/.claude.json`, fora do repo). **NUNCA service role.**
- **Project-scoped:** `vgfofofzptrtjvtuyzy` (só DEV). **Read-only:** `--read-only` (tratar write-capable até prova).
- **Testes planeados (só-leitura):** list tables · `SELECT count(*)`/`limit` em tabela vazia · sem INSERT/UPDATE/DELETE/migração.
- **Rollback:** `claude mcp remove supabase-dev`.
- **Estado:** **PENDENTE** — aguarda PAT do Cris + autorização para executar o `add`. Não configurado nesta sessão.

## 5.c MCP remoto (hosted) FALHOU — HTTP 400 → fallback local npx/PAT (2026-07-02)
- **Tentativa (Cris):** MCP **remoto hosted** `type:http` → `https://mcp.supabase.com/mcp?project_ref=vgfofofzptrtjvtuyzy&read_only=true` (registado em `.mcp.json` project-scope).
- **Resultado:** **HTTP 400** na URL. Sem autenticação concluída, **sem dados migrados, sem mutation, sem token exposto**.
- **Ação:** **NÃO** re-autenticar no remoto. Configuração removida:
  ```
  claude mcp remove supabase-dev
  # -> "Removed MCP server supabase-dev from project config" (.mcp.json agora {"mcpServers":{}})
  ```
  (`.mcp.json` untracked; ficou com `mcpServers` vazio; sem `supabase-dev` em `~/.claude.json`.)
- **Decisão:** abandonar o **remote OAuth com query params** (HTTP 400) e usar o **fallback local npx/PAT read-only** (§5.b) — só quando o Cris autorizar e fornecer o PAT (não pelo chat).
- **Estado:** nenhum MCP Supabase configurado. Aguarda autorização para o `add` local (§5.b).

## 6. Security / secrets status
- `.env` **gitignored** (✅), existe localmente, **não trackeado** (✅). Nenhum secret impresso/colado.
- `.env.example` = **só placeholders** (`SUPABASE_URL/ANON_KEY/SERVICE_ROLE_KEY/DB_URL/ENV`).
- **`SUPABASE_SERVICE_ROLE_KEY` nunca** no MCP/Claude/commits. MCP usa PAT read-only project-scoped.
- Credenciais reais vivem **só** no `.env` local (Cris preenche; não colar no chat).

## 7. Read-only / write-capable assessment
- Estado atual: **nenhuma conexão** → risco zero agora.
- Quando ligar: MCP `--read-only` + project-scoped DEV; testes permitidos = list tables / SELECT simples (após schema aplicado). **Sem INSERT/UPDATE/DELETE/migration.** Assumir write-capable até verificar.

## 8. Testes executados
**Nenhum teste de conexão/DB** (sem CLI/DB/MCP e sem autorização). Só recon local read-only.

## 9. Próximos passos
1. **Aplicar schema (Cris, manual):** dashboard Supabase DEV → SQL Editor → colar `supabase/schema.sql` → run (dev). OU instalar CLI/Docker/psql (reportar antes) para via local.
2. Preencher `.env` local com vars DEV (não colar no chat; não commitar).
3. **Autorizar** ligação MCP read-only project-scoped (§5) — só então testar list/SELECT.
4. S3: scripts de ingestão mínimos (pointers), após schema aplicado + MCP validado.

## 10. Riscos
- Instalar CLI/Docker sem reportar (evitado). · Colar secrets no chat/repo (evitado). · MCP com service role (proibido; usar PAT read-only). · Aplicar schema remoto sem autorização (evitado). · Assumir read-only sem verificar (mitigado: tratar write-capable até prova).

## 11. Rollback
Doc-only: apagar este report + a secção manual do README. Nenhuma conexão/mutação para reverter. `.env` local é do Cris (fora do git).

## 12. Confirmação
**Nenhum dado trading/RAW/MEMORY migrado. Nenhuma conexão remota. Nenhum schema aplicado. Nenhum runtime tocado. Nenhum secret no repo.**
