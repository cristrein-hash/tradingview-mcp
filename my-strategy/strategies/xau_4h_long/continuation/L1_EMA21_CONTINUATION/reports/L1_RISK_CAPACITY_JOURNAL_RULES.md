# L1 EMA21 4H LONG Continuation — REGRAS DE RISCO / CAPACIDADE / JOURNAL (canónico)

**Data:** 2026-07-09 · **Status:** `FROZEN_NOT_WIRED` · **Produção:** `NOT_AUTHORIZED`
**Supersede:** `L1_PREPRODUCTION_CAPACITY_RISK_RULES.md` (política antiga 3 slots / 1.0R — REVOGADA).

Política inicial congelada (Cris 2026-07-09) para o início REAL da L1. **Espelha exatamente `capacity_journal.py`** (fonte de verdade do código; funções puras, fail-closed, **NÃO wired** a runtime/broker). Auditado por `reports/l1_risk_capacity_journal_audit.py` (11/11 PASS).

## Regras congeladas (€-based)
| parâmetro | valor |
|---|---|
| `max_open_l1_positions` | **2** |
| `max_same_symbol_l1_positions` | **2** |
| `max_total_l1_open_risk_eur` | **€200** |
| `position_risk_mode` | `fixed_equal` |
| `each_position_risk_eur` | **€100** |
| `duplicate_same_bar_signal` | **BLOCK** |
| `opposite_position_hedge` | **NOT_ALLOWED_FOR_L1** |
| `broker_execution` | **MANUAL_APPROVAL_ONLY** |
| `telegram_signal` | **HUMAN_REVIEW_ONLY** |
| `auto_broker_execution` | **NOT_AUTHORIZED_YET** |

## Notas obrigatórias
- Pepperstone pode permitir múltiplas posições/hedging, mas **a L1 continua LONG-only**.
- **2 posições em XAUUSD = exposição direcional concentrada** — não é dobrar aposta independente.
- Limite inicial **deliberadamente simples**: máx **2** posições L1, máx **2** no mesmo símbolo, risco agregado **€200**, **€100/posição**. **Sem 3º slot** nesta fase.
- Cada sinal = **`trade_id` próprio** no journal (fonte por-trade), mesmo que a plataforma agregue visualmente.
- Não abrir novo trade se já houver **2** posições L1 abertas · não abrir duplicado no mesmo `bar_time` · sem hedge/oposto · risco total aberto **não pode exceder €200**.
- Broker execution futura = **manual approval**, nunca automática.

## Fail-closed (garantido por `capacity_journal.evaluate_capacity`)
Bloqueia (`decision_state=BLOCK`) em qualquer: direção≠LONG · hedge/oposto presente · símbolo/bar_time ausente · duplicado mesmo bar · ≥2 posições abertas · ≥2 no mesmo símbolo · risco/posição>€100 · risco agregado>€200. Ambiguidade ⇒ BLOCK.

## Journal — campos mínimos (por-trade)
`trade_id · strategy_id · symbol · timeframe · bar_time · signal_time · entry · sl · target · risk_eur · slot_index · open_l1_positions_before · open_l1_positions_after · aggregate_open_risk_eur_before · aggregate_open_risk_eur_after · decision_state · human_status · broker_status · telegram_status · source_snapshot · created_at`
- Defaults em `build_journal_record`: `human_status=PENDING_REVIEW`, `broker_status=NOT_EXECUTED_MANUAL_ONLY`, `telegram_status=NOT_SENT`.

## Status
`FROZEN_NOT_WIRED` — regras congeladas e testadas; **enforcement em runtime + broker NÃO implementado, NÃO autorizado.** Wiring futuro = autorização explícita separada do Cris.
