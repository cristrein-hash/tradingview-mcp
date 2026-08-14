-- memory_delta 20260814e — sweep-reject 4H guard LIVE (tripwire de protecao, nao edge). Consome store_reader/market_context.
insert into memory_items (id, scope, visibility, category, title, body, tags, source_ref, status)
values
 (md5('sweep_reject_guard_live_20260814')::uuid, 'private', 'internal', 'project',
  'sweep-reject 4H guard LIVE — tripwire de protecao (NAO edge), aprovado Cris apos estudo',
  'Cris 14/08: sweep_reject_guard.py LIVE. REGRA (confirmada): LIGA quando vela 4H FECHADA tem pavio superior '
  '> 50%% do corpo (sweep/rejeicao no topo) -> bloqueia LONG; DESLIGA na QUEBRA DE ESTRUTURA 15M (close acima do '
  'ultimo lower-high = HH + higher-low, ex. 14/08 ~06:00 HH4336.7>LH4328.2). Stateless: block = sweep 4H mais '
  'recente que a ultima quebra-up 15M. NAO e reclaim-do-high nem tempo-fixo (isso foi inventado por engano e '
  'removido). CONSOME store_reader bars 4H/15M nativas (nao reconstroi contexto, nao inventa). Fail-open. Wired em '
  '3 emissores (candle_reader send_confirmed_tg, e2_quality notify_surfaced, entry_validator GO-LONG) ao lado do '
  'choch_guard. launchd com.cristrein.sweep-reject-guard tick 5min -> logs/sweep_reject_guard.jsonl (medir FP '
  'forward). IMPORTANTE: o estudo multi-ano (research/xau_15m_short/sweep_reject_study_20260814.py, RAW 4H 6,5 '
  'anos, 1519 candidatos) mostrou 45%% capture = SEM edge vs baseline ~50%%. NAO tem poder preditivo. Cris '
  'aprovou-o assim mesmo como "precaucao facil, barata e valida" para o forward: se repetir o cenario que '
  'estourou a conta em 13/08, ao menos nao emite longs na faca. Custo aceite: bloqueia alguns longs bons. '
  'Forward=arbitro via o log. Contas ainda frageis (FTMO/FN).',
  array['seed:memory_delta_20260814e_sweep_reject_guard_live','guard','sweep-reject','tripwire','xau','long-block','forward'],
  'alert-bridge/sweep_reject_guard.py', 'active')
on conflict (id) do nothing;
