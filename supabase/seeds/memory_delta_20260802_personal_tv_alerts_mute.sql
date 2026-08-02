-- ============================================================================
-- SUPABASE MEMORY — DELTA SEED · seed:memory_delta_20260802_personal_tv_alerts_mute
-- ============================================================================
-- Receiver: alertas TradingView pessoais mudos (logados, sem Telegram/recheck). 1 row. Idempotente.
-- ============================================================================
begin;
insert into memory_items (id, scope, visibility, category, title, body, tags, source_ref, status) values
(
  md5('seed:memory_delta_20260802_personal_tv_alerts_mute:memory_items:mute')::uuid,
  'product', 'internal', 'decision',
  'Receiver: alertas TradingView PESSOAIS = MUDOS (Cris 2026-08-02) — logados para auditoria mas sem Telegram nem claude_recheck; estruturados intactos',
  'DIRETIVA Cris: "vou seguir colocando alertas no TradingView para minha analise pessoal, nao preciso deles sinalizados no Telegram nem a serem considerados pelo sistema" (supersede a acao anterior de apagar os alertas TV). CONTEXTO: alertas pessoais chegam ao webhook como corpo NAO-JSON, viram payload raw_message (unico local onde raw_message nasce = parse-fail, grep-verificado em todo o alert-bridge) e eram reencaminhados ao Telegram + claude_recheck (ex: "Micro DM ZONE_ HVN" sex 31/07, "4H", "4H High Week", "FVG"). IMPLEMENTACAO (desenho previo obrigatorio por ser webhook routing, protocolo CLAUDE.md + verificacao viva): guard no tv_webhook_receiver.py APOS o log de auditoria: payload nao-dict OU (raw_message presente E sem alert_type E sem symbol/ticker) => personal_tv_alert=true -> fica em tradingview_alerts.jsonl (auditoria) mas SEM Telegram, SEM claude_recheck, SEM schema_warnings; responde 200 sempre (senao o TradingView desativa o alerta do Cris). Flag rollback TV_MUTE_PERSONAL_ALERTS=0 + restart. BONUS: elimina rechecks Claude desperdicados em alertas pessoais + o "Reavaliacao falhou" no Telegram quando o recheck engasgava com payload de texto. VERIFICACAO VIVA pos-kickstart: (1) POST texto puro -> 200 personal_tv_alert true, telegram skipped, 0 recheck spawn, logado; (2) POST estruturado test_connectivity -> caminho normal intacto (telegram_ok + recheck_queued); (3) /health 200. Receiver kickstarted (nunca python3 direto). Commit 265f3a8.',
  array['seed:memory_delta_20260802_personal_tv_alerts_mute','alertas-tv-pessoais-mudos','raw_message-so-nasce-em-parse-fail','guard-pos-log-auditoria-preservada','200-sempre-senao-tv-desativa','TV_MUTE_PERSONAL_ALERTS-rollback','estruturados-intactos-testado','webhook-routing-desenho-previo'],
  'alert-bridge/tv_webhook_receiver.py · logs/tradingview_alerts.jsonl · project_fj_ws_disabled (follow-up) · commit 265f3a8',
  'active'
)
on conflict (id) do nothing;
commit;
