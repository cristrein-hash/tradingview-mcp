-- ============================================================================
-- SUPABASE MEMORY — DELTA SEED · seed:memory_delta_20260723_consolidation_e0_guard
-- ============================================================================
-- Sessao 2026-07-23: auto-boicote (reader paralelo) diagnosticado + CONSOLIDACAO no dossie E0
-- + guard hard-block (exit 2) contra reconstruir em vez de consumir. + forward-test dos sinais.
-- Aplicar via scripts/supabase/apply_memory_delta.py. Idempotente. Total: 2 rows.
-- ============================================================================
begin;
insert into memory_items (id, scope, visibility, category, title, body, tags, source_ref, status) values
(
  md5('seed:memory_delta_20260723_consolidation_e0_guard:memory_items:auto-boicote-consume-e0')::uuid,
  'product', 'internal', 'feedback',
  'AUTO-BOICOTE: construir reader PARALELO em vez de CONSUMIR o aprovado (E0) — falha comportamental recorrente + guard hard-block (Cris 2026-07-23)',
  'Falha comportamental grave e RECORRENTE: a cada evolucao, o meu default errado e construir do zero uma invencao (pior/falhada) em vez de PROCURAR o que ja existe (memoria + sistema vivo + dossie E0). CASO-MAE: construi o motor mtf_cross/classify_zone (FRACO/FORTE) 2026-07-21 e DESLIGUEI os monitores que liam o dossie E0 (market_context.json) — que JA TINHA TUDO: mtf multi-TF (15/60/240/1D trend+CHoCH), macro (real_yield_10y 2.37, usd_broad=DXY, vix, event-window, eventos), confluence sell/buy, regime, magnets, fresco (daemon E0 vivo). Substitui por reader paralelo POBRE (perna 15M-3h + zonas, cego a yields/DXY/multi-TF). Consequencia: o sinal ficou cego aos lower-highs do 1H que o Cris via a olho — nao por falta de config, mas porque criei um segundo cerebro burro e desliguei o bom. Viola feedback_consolidate_on_approved_not_new_process (2026-07-19). Cris exausto: "auto-boicotas o projeto constantemente, nao sei mais o que fazer". FIX = 3 camadas de guard: (1) memoria permanente feedback_consume_existing_never_rebuild; (2) aviso PARALLEL_CONTEXT_BUILD em systematic_error_guards.py; (3) HARD-BLOCK exit 2 consolidation_guard.py (PreToolUse Write|Edit, wired) que IMPEDE a escrita de reader de contexto/regime/mtf/sinal que re-le bars/store, a nao ser que o codigo CONSUMA o E0 OU tenha corrido scripts/safety/consolidation_check.py (busca-primeiro, token 20min). Smoke 4/4 OK. PROTOCOLO: antes de qualquer leitura de contexto/regime/mtf/macro/sinal -> market_context.json (axes mtf/macro/confluence/regime/magnets) e o cerebro unico; CONSUMIR, nunca reconstruir.',
  array['seed:memory_delta_20260723_consolidation_e0_guard','auto-boicote','consume-existing-e0','parallel-reader-antipattern','consolidation-guard','hard-block-exit2','market_context-dossie','recurring-failure','user-feedback'],
  'my-strategy/core/price_shock/price_shock_cycle.py::classify_zone (consome E0) · scripts/safety/consolidation_check.py · ~/.claude/hooks/consolidation_guard.py · memoria feedback_consume_existing_never_rebuild · commits e466217/b6072b7',
  'active'
),
(
  md5('seed:memory_delta_20260723_consolidation_e0_guard:memory_items:fracoforte-consome-e0-forward')::uuid,
  'product', 'internal', 'project',
  'FRACO/FORTE (price-shock) consolidado no E0 + forward-test: 0/3 sinais mecanicos lucrativos; edge=discricionario (Cris 2026-07-22/23)',
  'Evolucao do motor de sinal OB-touch (price-shock check_ob_touch/classify_zone). (1) 2026-07-22 (commit e45ed3b): perna imediata passou a DRIVER DE DIRECAO (apos 2 SHORT FORTE stopados num markup) — veto-perna + veto-fluxo + continuacao. MAS a perna era so 15M-3h (mio pe). (2) 2026-07-23 (commit e466217): CONSOLIDACAO — classify_zone agora CONSOME o dossie E0: direcao pela TRAJETORIA MULTI-TF (15/60/240 trend+CHoCH via E0.mtf, resolve a cegueira dos lower-highs 1H), macro E0 (yield real 2.37 = teto ouro = suporte SHORT), event-window flag, confluence E0 no fluxo. Testado ao vivo: supply institucional+rejeicao que antes dava FRACO agora da SHORT FORTE. FORWARD-TEST criterioso (Cris pediu): 3 sinais FORTE mecanicos no historico (2x SHORT 4095-4103 22/07 = PERDA no markup; 1x LONG 4156-4164 = perda/marginal) = 0/3 lucrativos. As operacoes LUCRATIVAS foram DISCRICIONARIAS: EUR long +400 EUR (contexto macro nosso, sistema nem monitora EUR), XAU long +60.10 EUR (Cris leu fraqueza da perna e saiu). LICAO CONFIRMADA (alinha com project_strategic_reflection_copilot): o edge e o CRIS + contexto, nao o gatilho mecanico; o sistema vale como COPILOTO de contexto/alerta, nao gerador de entradas cego. Watcher de niveis ao vivo (level_alerts_watcher.py): ouro bar-store exato + EUR MCP pinado. FundedNext Fase1 +401/8K. Telegram ativo. PROXIMO: motor precisa de leitura contextual multi-TF + PA-sequence + externals (E0 ja da a base).',
  array['seed:memory_delta_20260723_consolidation_e0_guard','fraco-forte','consome-e0','trajetoria-multi-tf','forward-test-negativo','edge-discricionario','copiloto','level-alerts-watcher','fundednext','xau-eur-live'],
  'my-strategy/core/price_shock/price_shock_cycle.py · my-strategy/core/level_alerts_watcher.py · commits e45ed3b/e466217 · copilot/journal/trades.jsonl',
  'active'
)
on conflict (id) do nothing;
commit;
