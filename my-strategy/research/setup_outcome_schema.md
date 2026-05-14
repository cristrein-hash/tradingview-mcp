# Setup Outcome Log Schema v0.1

Objetivo:
Avaliar o que aconteceu após cada alerta/reavaliação registrada em setup_research_log.jsonl.

Arquivo principal:
~/tradingview-mcp/alert-bridge/logs/setup_outcome_log.jsonl

Cada linha JSONL representa a avaliação posterior de um evento registrado no journal.

Horizontes avaliados:
- 5 candles
- 10 candles
- 20 candles
- 50 candles

Campos principais:
- event_id
- evaluated_at
- symbol
- timeframe
- alert_type
- drawing_name
- strategy_layer
- source_timeframe
- price_at_alert
- bars_after

Dados de preço:
- close_at_alert
- high_after
- low_after
- close_after
- max_favorable_excursion
- max_adverse_excursion
- mfe_percent
- mae_percent

Interpretação direcional:
- inferred_direction
- direction_confidence
- direction_source

Resultado teórico:
- would_have_helped
- would_have_hurt
- was_noise
- outcome_label

Valores possíveis de outcome_label:
- favorable_reaction
- adverse_reaction
- sideways_noise
- breakout_continuation
- false_breakout
- invalidation_confirmed
- setup_missed
- insufficient_data
- unclear

Análise estratégica:
- classification_at_signal
- was_setup_valid
- was_near_setup
- was_observation
- was_no_trade
- was_invalidated
- had_rsi_extreme_text
- had_bubbles_text
- had_top_bottom_text
- had_rejection_text
- had_rr_text
- macro_mentioned

Campos de aprendizado:
- what_worked
- what_failed
- confluences_confirmed
- confluences_missing
- suggested_learning
- should_adjust_strategy
- proposed_adjustment_summary

Regras:
- Avaliar inclusive sinais silenciados no Telegram.
- Avaliar inclusive NO TRADE e SETUP EM OBSERVAÇÃO.
- Não alterar strategy_rules.json automaticamente.
- Claude pode sugerir ajustes, mas o usuário deve aprovar qualquer mudança.
- Eventos com dados insuficientes devem ser marcados como insufficient_data, não ignorados.

Fases futuras:
D3: relatórios diários/semanais por ativo, timeframe e confluência.
D4: propostas formais de ajuste da estratégia.
D5: aprovação humana antes de alterar regras.
