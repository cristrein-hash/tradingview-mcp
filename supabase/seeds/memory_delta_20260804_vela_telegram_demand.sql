-- ============================================================================
-- SUPABASE MEMORY — DELTA SEED · seed:memory_delta_20260804_vela_telegram_demand
-- ============================================================================
-- Vela-no-nivel Telegram autorizado (daemon permanente) + demand 4H no mapa. 1 row. Idempotente.
-- ============================================================================
begin;
insert into memory_items (id, scope, visibility, category, title, body, tags, source_ref, status) values
(
  md5('seed:memory_delta_20260804_vela_telegram_demand:memory_items:phase2')::uuid,
  'product', 'internal', 'decision',
  'Vela-no-nivel: Telegram AUTORIZADO -> daemon launchd permanente + mapa ganha OB demand 4H 3995.84-4011 tese LONG critica (Cris 2026-08-04 tarde)',
  'FASE 2 do copiloto no MESMO dia do go-live (apos aceitacao PASS 5/5 e 1a sessao chat-only): (1) Cris AUTORIZOU o Telegram do vela-no-nivel -> promovido a daemon launchd PERMANENTE com.cristrein.vela-no-nivel (KeepAlive, RunAtLoad, wrapper start_vela_no_nivel.sh com VELA_PRODUCTION_AUTHORIZED=1 e VELA_READER_CONSULT=1; logs alert-bridge/logs/vela_no_nivel.out/err.log; pid vivo, banner "telegram=ON" confirmado; sobrevive a sessoes e reboot; a instancia chat-only da sessao foi parada e substituida por tail do log para espelho no chat). Cada alerta 🕯️ vai ao Telegram do Cris + juizo do reader em follow-up (cooldown 2h/zona). (2) Mapa do trader ganhou a 3a zona: OB demand 4H 3995.84-4011.0, tese LONG, criticidade critica, validade sexta — "monitoracao de LONG, o bloco do monstro da semana passada" — o vela-no-nivel passa a ler velas de absorcao LONG (pavio inferior + venda absorvida + fecho de volta em cima) nessa demanda, espelho exato do short. MAPA ATIVO COMPLETO: supply 4066-4073 SHORT + OB premium 4101-4116 SHORT + OB demand 3995.84-4011 LONG (todas criticas, expiram 08/08 21:00Z) + tese geral SHORT. Cobertura: alertas de barra nos DOIS lados + prefixo de conflito em sinais E2 contra qualquer das 3 teses. Commit 5546c70.',
  array['seed:memory_delta_20260804_vela_telegram_demand','vela-telegram-autorizado','daemon-launchd-permanente','com.cristrein.vela-no-nivel','ob-demand-4h-3995-4011-LONG','mapa-3-zonas-criticas','cobertura-dois-lados','reader-consult-cooldown-2h'],
  'alert-bridge/start_vela_no_nivel.sh · ~/Library/LaunchAgents/com.cristrein.vela-no-nivel.plist · alert-bridge/trader_map.json · project_copiloto_mapa_trader · commit 5546c70',
  'active'
)
on conflict (id) do nothing;
commit;
