# Project Authority Docs & Skills (repo-side, importado 2026-06-16)

Cópia **versionada** dos documentos de autoridade operacional do Trading System e das skills do projeto.
Importados do path externo `~/Desktop/TRADING/GPT_ trading_system_project_core_md_v1/` (raiz + `GPT.MD/` + `trading_system_project_skills_md_v1/`) em **2026-06-16** para blindar a continuidade do projeto contra compactação de conversa, perda de path local ou assistente sem contexto.

## O que estes arquivos são
- **Autoridade operacional do projeto.** Definem como qualquer assistente deve pensar, trabalhar e se proteger neste sistema.
- **RAW / source data continua sendo a fonte de verdade para DADOS** (backtest, edge). Estes docs são autoridade de **processo/governança**, não de dados.
- O **bootstrap canônico** aponta o estado atual do sistema: [`../BOOTSTRAP_REARCHITECTURE_CANONICAL_CONTEXT.md`](../BOOTSTRAP_REARCHITECTURE_CANONICAL_CONTEXT.md).
- As **skills (`SKILL_01`–`SKILL_07`) devem ser aplicadas silenciosamente** por qualquer assistente, sem precisar de instrução explícita a cada tarefa.

## Índice
**Authority docs (00–10):**
- `00_PROJECT_OVERVIEW.md` · `01_ASSISTANT_OPERATING_SYSTEM.md` · `02_DATA_SOURCE_POLICY_RAW_FIRST.md` · `03_BACKTEST_VALIDATION_PROTOCOL.md` · `04_STRATEGY_STATUS_MASTER.md` · `05_SYSTEM_ARCHITECTURE_CURRENT.md` · `06_CLEANUP_AND_RESTRUCTURE_PLAN.md` · `07_INCIDENTS_AND_PROCESS_LESSONS.md` · `08_PROMPT_AND_TASK_TEMPLATES.md` · `09_SKILLS_INDEX.md` · `10_DO_NOT_DO_RULES.md`

**Skills (01–07):**
- `SKILL_01_MINIMUM_SAFE_EXECUTION.md` · `SKILL_02_RAW_BACKTEST_PROTOCOL.md` · `SKILL_03_VISUAL_REVIEW_AUCTION_THEORY.md` · `SKILL_04_STRATEGY_GOVERNANCE.md` · `SKILL_05_PRODUCTION_SAFETY.md` · `SKILL_06_CLEANUP_GOVERNANCE.md` · `SKILL_07_PROMPT_DISCIPLINE.md`

## Origem / proveniência
- **Fonte externa:** `~/Desktop/TRADING/GPT_ trading_system_project_core_md_v1/`
  - `00,01,02,03,05,06,08,10` ← raiz
  - `04,07` ← subpasta `GPT.MD/` (não existem na raiz)
  - `09` + todas as `SKILL_0x` ← subpasta `trading_system_project_skills_md_v1/`
- **Data de importação:** 2026-06-16. Cópia fiel (sem edição de conteúdo). Os originais externos **não foram movidos nem apagados**.
- As duplicatas raiz↔`GPT.MD/` de `01/02/03/10` foram confirmadas **idênticas** (a raiz é a canônica importada).

## Regras de uso
- **Não editar** estes arquivos sem um bloco explícito autorizado para isso.
- Não resumir nem reescrever as políticas no lugar dos originais — esta cópia é o registro fiel.
- **Se houver conflito** entre estes authority docs e a memória/chat/estado do repo: **parar e reportar**, não decidir sozinho.
- Estado vivo do sistema (scheduler, regime, gate, legacy) está no bootstrap canônico, não aqui.
