# Setup Research Journal Schema v0.1

Objetivo:
Registrar todas as reavaliações feitas pelo Claude após alertas do TradingView, incluindo setups válidos, quase válidos, observações, invalidações e NO TRADE.

Arquivo principal:
~/tradingview-mcp/alert-bridge/logs/setup_research_log.jsonl

Cada linha JSONL representa uma reavaliação de alerta.

Campos principais:

- event_id
- received_at
- evaluated_at
- symbol
- base_symbol
- timeframe
- alert_type
- event
- drawing_type
- drawing_name
- strategy_layer
- source_timeframe
- price_at_alert
- alert_message
- reason
- expected_recheck

Resultado da reavaliação Claude:

- classification
- direction
- health
- summary
- main_blocker
- action_taken
- next_action
- telegram_sent
- telegram_reason

Campos de pesquisa:

- is_setup_valid
- is_near_setup
- is_observation
- is_no_trade
- is_invalidated
- is_critical
- has_rsi_extreme_text
- has_bubbles_text
- has_top_bottom_text
- has_rejection_text
- has_rr_text
- macro_mentioned

Texto bruto:

- claude_stdout
- claude_stderr

Regras:
- Registrar todos os alertas, inclusive NO TRADE.
- Não usar o journal para executar ordens.
- Não alterar strategy_rules.json automaticamente com base no journal.
- O journal serve para pesquisa, estatística e propostas futuras.
- Claude pode sugerir ajustes, mas o usuário deve aprovar qualquer mudança de estratégia.

Fases futuras:

D2:
Medir resultado após 5, 10, 20 e 50 candles.

D3:
Gerar relatórios diários/semanais de confluências.

D4:
Gerar propostas formais de ajuste de estratégia.

D5:
Aprovação humana antes de mudar strategy_rules.json.
