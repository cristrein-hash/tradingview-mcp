# MCP × Managed Agents — Fronteira de Design

**2026-06-19.** Guia de arquitetura para escalar agentes (multi-agente / Anthropic Managed Agents) neste
projeto **sem quebrar o TradingView MCP**. Baseado na auditoria do `src/` (CDP singleton, 80 tools, lazy
history, foot-guns). Doc-only; não altera código/produção.

## Princípio-mãe
> **O trabalho que dá valor é offline e paralelo-seguro. O chart só serve para ESCREVER.**
> Separe sempre: **N agentes paralelos sobre dados RAW frozen** + **1 agente serializado para I/O de chart.**

```
[OFFLINE — escalável, paralelo]                 [CHART — single-instance, serializado]
geração de hipóteses · evidência de               plotagem de revisão · screenshots ·
especialistas sobre packets RAW · backtest        set symbol/timeframe · draw_* ·
estatístico · OOS · DA · aggregator diag.         replay manual
        │ (Workflow/fan-out, Managed Agents)              │ (1 agente, 1 chart, com lock)
        ▼                                                  ▼
   Hypothesis Registry → gate → library            revisão humana discricionária
```

## Regras (invioláveis)

1. **Offline agents = PERMITIDO / ESCALÁVEL.** Tudo que lê dados RAW frozen (packets, raw_features, OHLCV
   exportado, evidência de especialistas) roda em N agentes paralelos — não toca o chart, não tem singleton,
   escala em Workflow/Managed Agents. É aqui que o engine criativo + validação vivem.

2. **Chart agent = SERIALIZADO.** Qualquer escrita no chart (plot, screenshot, símbolo/TF, draw_*, replay)
   passa por **um único agente de cada vez**, com pause dos LaunchAgents (daemon+cron+xau-l1-cycle) + lock.
   Nunca dois agentes no chart simultaneamente.

3. **TradingView MCP = I/O frágil, NÃO engine.** O MCP é `Runtime.evaluate` contra internals não-documentados
   do TradingView Electron (version-fragile; o próprio README pede fixar a versão). Use-o para *ler/escrever
   no chart*, jamais como motor de cálculo/decisão. A lógica de estratégia vive em Python/dados frozen, fora do MCP.

4. **SEM paralelismo no chart.** `connection.js` tem um **singleton CDP global** (1 server ⇄ 1 chart, sem fila/
   mutex). Chamadas concorrentes se atropelam no mesmo socket e estado. Para paralelismo real no chart seria
   preciso N instâncias TradingView em N portas — fora de escopo. Até lá: **um chart, um agente, serial.**
   (Risco correlato: leak de `server.js` órfão por processo; `pkill -f server.js` é inseguro.)

5. **SEM replay/autoplay agressivo.** `replay_autoplay` só aceita 9 velocidades whitelistadas — valor inválido
   **corrompe a conta na nuvem PERMANENTEMENTE** (`src/core/replay.js`). Replay = passo-a-passo controlado,
   nunca loops rápidos/automáticos sem necessidade. Idem `requireFinite` em níveis que persistem na nuvem TV.

6. **SEM chart/MCP em validação histórica quando RAW frozen existe.** Toda audit/backtest/OOS usa o RAW
   congelado (datasets em HD externo + `repro_recovery/`), nunca o chart ao vivo. Motivos: (a) **lazy history** —
   `data_get_ohlcv` lê só o buffer em memória, sem backfill programático (precisa scroll humano; foi o que
   travou os trades 2020); (b) reprodutibilidade — RAW frozen é determinístico, o chart não; (c) o chart é
   recurso único e frágil. O chart entra só na **revisão visual discricionária**, depois da validação offline.

## Notas de implementação (futuro)
- `src/core/` é **importável como lib** (`package.json` exports `./core`) → um app Agent SDK/Managed Agents pode
  importar as funções core sem a camada stdio do MCP. Preferir isso a spawnar `server.js` por agente.
- Segurança: port 9222 **só localhost** (SECURITY.md); cookie de sessão + ToS = risco de ban multiplicado por
  agentes paralelos num login único → **nunca** expor o chart a uma frota hospedada; managed agents ficam no
  lado offline.
- Não confiar nos números dos docs (contagem de tools / caps divergem do código) — **a verdade é o código**.

Relaciona: `docs/FUTURE_CORE_BOUNDARY.md`, `docs/CANONICAL_TRADE_PLOTTING.md`, memória `project_creative_strategy_engine_managed_agents`.
