# Setup R-Multiple Outcome Schema — D2R

Status: experimental / read-only

## Objetivo

Avaliar eventos do journal em termos de R-multiple teórico.

O D2R responde perguntas como:

- teria dado +1R?
- teria dado +2R?
- teria batido stop primeiro?
- tinha stop técnico claro?
- tinha R:R mínimo de 2:1?
- era realmente operável ou só parecia bom no gráfico?

## Regras

- Não executar trades.
- Não alterar strategy_rules.json.
- Não alterar operational_prompt.md.
- Não criar alertas.
- Não desenhar no TradingView.
- Não usar entrada perfeita com hindsight.
- Usar entrada, stop e alvo plausíveis com base no texto do alerta.
- Se não houver stop claro, marcar como no_trade ou unclear.
- Se R:R for menor que 2:1, não considerar como SETUP_VALIDO retroativo.

## Campos principais

Cada evento avaliado deve gerar:

- event_id
- symbol
- timeframe
- alert_type
- drawing_name
- classification_at_signal
- direction
- entry_model
- entry_price
- stop_price
- target_1_price
- target_2_price
- risk_points
- planned_rr_1
- planned_rr_2
- max_favorable_r
- max_adverse_r
- hit_stop
- hit_1r
- hit_2r
- hit_stop_first
- hit_target_1_first
- hit_target_2_first
- theoretical_r_outcome
- r_outcome_label
- would_have_been_tradeable
- why_tradeable_or_not
- setup_valid_retro
- candidate_strong_retro
- main_blocker_was_valid
- blocker_assessment
- suggested_learning
- should_review_manually

## Labels possíveis

- win_2r
- win_1r
- loss_1r
- breakeven
- no_trade
- unclear
- insufficient_data

## Interpretação

win_2r:
O trade teria atingido +2R antes do stop.

win_1r:
O trade teria atingido +1R, mas não +2R.

loss_1r:
O stop teria sido atingido primeiro.

no_trade:
Não havia entrada/stop/R:R suficientemente claros.

unclear:
Dados ou leitura insuficientes.

insufficient_data:
Ainda não há candles futuros suficientes.
