# FORWARD OUTCOME LAYER — ROADMAP (2026-06-16, design-only)

Plano de implementação faseado. **Nada implementado ainda.** Cada fase = bloco isolado, read-only, com autorização explícita. Módulo futuro: `my-strategy/core/forward_outcome/`. Escopo inicial **XAU-only**.

## Pré-condições para iniciar (todas exigidas)
- Hard-stops da SPEC §2 re-verificados PASS no momento da implementação.
- L1 acumulou ≥ N candidatos/sinais forward reais (regime atual BEAR → poucos; sem amostra a camada roda vazia). Sugestão N≥10 candidatos forward antes da Fase 2.
- Autorização explícita do Cris por fase.

## Fase 0 — Spec (FEITA)
SPEC + ROADMAP versionados. Sem código.

## Fase 1 — MVP: forward signal quality (mais barato, sem R)
`report_forward_quality.py` + `ingest_live_signals.py` (read-only).
- Lê `indicator_signals.jsonl` (XAU) + journal L1 (`signal_emitted`).
- Calcula métricas D **de contagem/qualidade** (densidade/dia, payload completeness, duplicate rate, latência estimada, Telegram sent/dedup) — **sem cálculo de R**.
- Saída: `forward_signal_quality.jsonl` + `forward_outcome_summary.md`. Sem Telegram.
- **Valida o pipeline de leitura sem tocar em RAW nem em outcome.**

## Fase 2 — Match candidato ↔ live signal
`match_candidates.py`.
- Junta RawIndicatorSignal ↔ StrategyCandidate (bar/ts/símbolo), marca matched/unmatched.
- Saída: enriquece `forward_signal_quality.jsonl` com match rate. Ainda sem R.

## Fase 3 — Forward outcome (R)
`compute_forward_outcomes.py` (reusa exit policy do `outcome.py`, read-only sobre RAW).
- THEORETICAL (sem entrada) / REAL (entry_taken no journal).
- Saída: `forward_outcomes.jsonl`.

## Fase 4 — Comparação backtest vs forward
`compare_backtest_forward.py`.
- OutcomeComparison (agree/diverge + dimensão: timing/payload/outcome).
- Saída: `forward_outcomes.jsonl` + seção no summary.

## Fase 5 — Hipóteses + (opcional) digest manutenção
`forward_hypotheses.jsonl` (clusters/falsos-positivos para validar em RAW) + digest em **canal de manutenção separado** (nunca canal de sinal).

## Invariантes em todas as fases
Read-only sobre fontes · escreve só `forward_*` próprios + manifest · XAU-only inicial · sem scheduler · sem Telegram de trade · não toca receiver/event store/RAW/journal/D2R/broker/pause flag · edge só valida em RAW.
