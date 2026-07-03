# XAU 15M — LONG/SHORT STRATEGY SPLIT DECISION (Cris, 2026-07-02)

## Decisão

O XAU 15M passa a ser dividido **formalmente** em estratégias separadas:

- **`XAU 15M LONG`** — a estratégia construída até agora (swept-runner base #4 + regime-v5). `USER_APPROVED_NOT_PRODUCTION`. Objeto da re-adaptação de regime atual. **Toda análise 15M existente é e permanece LONG-only.**
- **`XAU 15M SHORT`** — estratégia FUTURA, SEPARADA, com lógica própria, a ser criada **depois** do LONG. `DEFERRED_AFTER_XAU_15M_LONG`.

## Motivo

O Regime Detector permite criar estratégias específicas por regime com maior precisão. Misturar LONG e SHORT no mesmo bloco estratégico contamina a arquitetura: a especialização correta é por estratégia-direção, com o detector servindo de camada de contexto/roteamento entre elas.

Evidência de suporte já existente (dados, não opinião): espelho SHORT simétrico **refutado** (`project_xau_15m_direction_short_mirror_refuted`) e direção-por-regime **refutada como beta-overlay** (Engine 8) — inverter gates ou usar o detector como direção automática já falhou empiricamente.

## Proibições (permanentes)

1. **Não** tratar o SHORT como espelho do LONG.
2. **Não** inverter gates LONG para criar SHORT.
3. **Não** usar o regime detector como direção automática.
4. Regime detector = **roteador/contexto/camada de especialização** — não licença para misturar estratégias.
5. Toda análise atual do 15M permanece **LONG-only**.

## Impacto na ordem dos próximos blocos

Inalterada, com escopo clarificado:
1. `RAW_15M_EXTENSION_PLAN_MAR_JUN_2026` → coleta futura: **foco = preparar dados para a re-adaptação do LONG** (os dados naturalmente servirão ao SHORT no futuro, mas esse não é o objetivo do bloco).
2. Slippage/cost manifest (pendência única OFICIAL_FN do **LONG**).
3. Regime v5 + macro-context re-adaptation (**LONG**).
4. Só depois: `XAU 15M SHORT` como bloco estratégico novo e independente.

## Docs atualizados (doc-only)

- `04_STRATEGY_STATUS_MASTER.md` §4.5 — split registrado com as proibições.
- `05_SYSTEM_ARCHITECTURE_CURRENT.md` — split + correção da cobertura RAW (2024-05-25→2026-05-25, gap = mai→presente).
- `XAU_15M_LONG_REGIME_READAPTATION_AUDIT_20260702.md` — addendum (correção RAW + split).
- MEMORY.md hot (auto-memória, fora do repo) — atualizado em paralelo.

## Confirmação

**Nenhum backtest, script, RAW, produção, plot, chart ou runtime tocado.** Bloco 100% doc-only. Safety report inalterado (BLOCKER=0 · WARNING=1 Caminho B TRUE_RISK · INFO=50).
