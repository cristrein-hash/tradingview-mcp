-- ============================================================================
-- SUPABASE MEMORY — DELTA SEED · seed:memory_delta_20260802_telegram_hygiene
-- ============================================================================
-- Higiene do Telegram: watchdog FJ-ws removido + origem do sinal SP500 identificada. 1 row. Idempotente.
-- ============================================================================
begin;
insert into memory_items (id, scope, visibility, category, title, body, tags, source_ref, status) values
(
  md5('seed:memory_delta_20260802_telegram_hygiene:memory_items:hygiene')::uuid,
  'product', 'internal', 'decision',
  'Higiene Telegram (Cris 2026-08-02): watchdog FJ-ws removido do painel + sinal SP500 micro identificado como alerta TradingView avulso do proprio Cris',
  'DUAS auditorias de poluicao do Telegram: (1) WATCHDOG "de FS" frequente = o FJ-ws: o daemon foi DESLIGADO por decisao do Cris 31/07 (403/plano caro, fonte secundaria) mas o stack_watchdog continuava a vigia-lo via heartbeat congelado, dando estado blind permanente e re-alerta "ainda cego" a cada 6h (REALERT_S). FIX: FJ-ws removido do painel do stack_watchdog.py (nota a apontar a decisao em project_fj_ws_disabled) + estado residual limpo em .watchdog_state/state.json; painel verificado 25/25 OK; watchdog e StartInterval (apanha sozinho). Commit c2d25a7. LICAO: ao desligar um daemon de proposito, remover TAMBEM a vigilancia dele no watchdog no mesmo ato — senao a decisao vira ruido cronico. (2) SINAL "SP500 micro" no Telegram (sex 31/07 02:42 e 06:05): raw_message "Micro DM ZONE_ HVN" = alerta TRADINGVIEW criado pelo proprio Cris no chart SP500 micro (zona demanda/HVN), ainda ativo na conta TV e apontado ao webhook; o tv_webhook_receiver reencaminha QUALQUER raw_message para o Telegram sem filtro de simbolo (desenho intencional dele). Outros alertas raw a passar: "4H", "4H High Week", "FVG". ACAO = do Cris no TradingView (apagar/desativar os alertas velhos); receiver NAO tocado (producao dormant, war-story CLAUDE.md). Ambos commitados/pushed.',
  array['seed:memory_delta_20260802_telegram_hygiene','watchdog-fj-ws-removido','ainda-cego-6h-poluia','licao-desligar-daemon-remove-vigilancia','sinal-sp500-era-alerta-tv-do-cris','receiver-reencaminha-sem-filtro','receiver-nao-tocado'],
  'my-strategy/core/stack_watchdog/stack_watchdog.py · alert-bridge/logs/launchd_tv_receiver_stdout.log · project_fj_ws_disabled · commit c2d25a7',
  'active'
)
on conflict (id) do nothing;
commit;
