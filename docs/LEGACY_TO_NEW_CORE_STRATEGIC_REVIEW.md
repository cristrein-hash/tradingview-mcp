# Legacy → New Core — revisão estratégica de manutenção (2026-06-16, read-only)

## 1. Executive summary
- **Decommission imediato seguro? PARCIAL.** `weekly-review` (falhando, ruído) = seguro decommissionar. D2R/enrich já dormant. **Mas** o event store vivo (`indicator_signals.jsonl` + receiver) = HARD_STOP.
- **Valor conceitual a preservar:** (a) digest/health periódico, (b) outcome engine (R post-hoc), (c) ingestão de indicator_signals como event store.
- **Ruído puro:** o `weekly_review` atual (lê logs do monitor dormant → vazio/erro, mistura Telegram de manutenção com canal de sinal).

## 2. Weekly Review
- **Função original:** digest semanal por frente (contagem `matches_by_strategy`) via Telegram (`--mode cron`).
- **Estado atual:** LaunchAgent carregado, **last exit code 1 (falhando)**.
- **Inputs:** `setup_research_log`, `setup_r_outcome_log`, `indicator_signals_outcomes` (deprecated), `strategy_eval_log`/`strategy_signals` (**stale** — monitor dormant), `indicator_signals.jsonl` (vivo).
- **Outputs:** Telegram digest (mesmo canal da L1).
- **Risco:** baixo (relatório, sem ordem/sinal de trade). Ruído: digest vazio/erro + mistura no canal Telegram da L1.
- **Valor reaproveitável:** o **conceito** (health/digest periódico) é útil; a implementação não.
- **Recomendação:** **REDESIGN_FOR_NEW_CORE** (health report da L1 limpo) + **DECOMMISSION_NOW** a versão atual.

## 3. D2R
- **Função original:** outcome engine post-hoc — `evaluate_r_outcomes.py` computa R-multiples de sinais; `generate_d2r_summary`; `run_d2r_backfill`. Era **pipeline de outcome/avaliação**, não detector nem sinal.
- **Estado atual:** LaunchAgent **NÃO carregado** (moratório re-pausado 2026-06-14); último log 06-14; dormant.
- **Conhecimento gerado:** matriz asset×direction R-outcomes (n=572 na memória); mecânica em `reference_d2r_mechanics`.
- **Valor reaproveitável:** o **conceito (medição de outcome em R)** já vive no novo core: `outcome.py` (L1, RAW-read-only) + `OUTCOME_ENGINE_SPEC` + Signal Outcome Lab (`outcomes_current.jsonl`, 72 CLEAN). D2R lia outcomes **contaminados** (razão do moratório).
- **Recomendação:** **ARCHIVE_AFTER_CAPTURE** (conceito já capturado; código = referência). Não redesenhar D2R; estender `outcome.py` quando precisar de outcome multi-estratégia.

## 4. Alarmes legacy
- **Função original:** Pine alerts → webhook → receiver → `indicator_signals.jsonl` (ingestão de sinais de indicadores) E, separadamente, recheck → SETUP_VALIDO → Telegram (sinal de trade).
- **Quais ainda importam:** **ingestão → `indicator_signals.jsonl` (VIVO, source-of-truth, FUTURE_CORE event store)** — receiver PID 841 ainda escreve (última 2026-06-15T21:00).
- **Quais são ruído/perigo:** o path **recheck → SETUP_VALIDO → Telegram** (trade signal) — **já NEUTRALIZADO** (recheck:931 + Telegram default-deny). Sem risco ativo.
- **Recomendação:** **HARD_STOP** no event store/receiver (manter); **KEEP_REFERENCE** no recheck neutralizado.

## 5. Proposta para a nova arquitetura
- **Manter digest semanal?** Sim, mas **redesenhado e L1-specific**: um **health report** (não digest de estratégias mortas).
- **Health report da L1 (conceito novo):** regime freshness, runs do scheduler + last exit, dedup anomalies, falhas de chart-restore, completude do journal. Read-only sobre `.runtime_state/` + regime_l1.
- **Review semanal de journal/outcome:** coberto por `outcome.py` + Signal Outcome Lab; um resumo opcional pode ser parte do health report.
- **Separar Telegram signal vs maintenance:** **SIM** — canal/marcação distinta para manutenção (nunca misturar com candidate notification). Hoje o weekly_review polui o canal de sinal.
- **O que deve morrer:** weekly_review atual, D2R como pipeline ativo, enrich.
- **O que deve existir:** event store (mantém), outcome.py (mantém), + futuro health report L1 limpo.

## 6. Classificação final
| Item | Classe |
|---|---|
| `weekly_review.py` + `weekly-review` LaunchAgent | **DECOMMISSION_NOW** (conceito → REDESIGN_FOR_NEW_CORE) |
| `archive-weekly` LaunchAgent | KEEP_AS_IS (retenção; inofensivo) ou DECOMMISSION se redundante |
| D2R (`auto_d2r_daily`, `evaluate_r_outcomes`, `generate_d2r_summary`, `run_d2r_backfill`) | **ARCHIVE_AFTER_CAPTURE** (conceito já no novo core) |
| `enrich_indicator_outcomes.py` (DEPRECATED) | ARCHIVE_AFTER_CAPTURE |
| `indicator_signals.jsonl` + receiver (vivo) | **HARD_STOP_DO_NOT_TOUCH** |
| recheck:931 neutralizado / monitor dormant | KEEP_REFERENCE |
| Signal Outcome Lab / `outcomes_current.jsonl` | KEEP_AS_IS (seed do outcome engine) |

## 7. Próximo bloco recomendado
**DECOMMISSION mínimo + reversível:** bootout do `weekly-review` LaunchAgent (para de enviar digest legacy falho ao canal de sinal) + arquivar a plist em `backups/launchagents_archive/` (move, não deletar). **NÃO** tocar D2R/enrich (já dormant — arquivar depois, em bloco separado), **NÃO** tocar receiver/event store/RAW. Opcional depois: desenhar o **health report L1** (módulo novo pequeno, canal de manutenção separado) — só com autorização.
