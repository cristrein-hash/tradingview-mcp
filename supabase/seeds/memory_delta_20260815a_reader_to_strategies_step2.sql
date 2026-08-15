-- memory_delta_20260815a_reader_to_strategies_step2
-- STEP 2 (ligar reader as estrategias) DESENHADO + AUDITADO, NAO aprovado/NAO implementado (Cris "NAO IMPLEMENTAR")
-- + revisao da semana 14 LONGs 4W/10L como evidencia. commit git ANTES do apply (G2).
insert into memory_items (id, scope, visibility, category, title, body, tags, source_ref, status)
values
 (md5('reader_to_strategies_step2_design_audit_20260815')::uuid, 'private', 'internal', 'project',
  'Reader->estrategias STEP 2: opcao 1 Reader-valida-sincrono DESENHADO+AUDITADO — NAO aprovado, NAO implementado',
  'Roadmap 3 passos (Cris 15/08, "por partes com muita calma"): (1) alinhar reader p/ ler shorts/nao comprar topos
  = DONE-pendente-forward (recalibracao 14/08); (2) LIGAR reader as estrategias = STEP 2 AGORA; (3) construir SHORT 15M.
  Achado: as estrategias fazem BYPASS do reader — A1/A2 (a1a2_runtime.py ~l172) chama e2_quality._tg_send DIRETO; so
  guards mecanicas (choch_guard, sweep_reject_guard blocks_long) as filtram. Por isso longs dispararam no topo/faca
  esta semana. STEP 2 escolha Cris = OPCAO 1 (Reader-valida via read Opus sincrono): estrategia dispara -> reader le a
  barra -> so vai ao grupo se aprovar (pode vetar long lido como faca/distribuicao/direcao-oposta).
  DESENHO (Plan agent): helper unico reader_gate(direction,emitter,bar,dsr,kind) em candle_reader.py antes de cada
  _tg_send ao grupo; reusa candle_reads.jsonl (fresco so em cache-miss); veta LONG se direction/bias=SHORT ou fase
  EXAUSTAO/REVERSAO_A_FORMAR sem bias long ou choch/sweep ja bloqueiam; 5 pontos A1/A2, Cp(sem guard, comprou o crash
  13/08), L1, L2(so entrada), AMD(fora v1); erro->fail-CLOSED no LONG/fail-open short+saida; flag
  STRATEGY_READER_ROUTING off/shadow/on + log reader_route.jsonl.
  AUDITORIA (devil advocate, 5 fragilidades): (1) CONFLITO DE SEQUENCIA=o mais grave: reader ESPERA confirmacao
  (quebra+retest/CHoCH) mas Cp/A1A2 disparam ANTES por construcao (Cp compra o flush) -> gate pode vetar a Cp quando
  esta certa; (2) falso-veto mata os WINs (is_chase_long ja foi desligado por matar continuacoes legitimas no topo);
  (3) premissa forward-nao-provada (dependencia circular: filtrar por componente que tinha o mesmo bug); (4) reuse de
  read falha a entrada (estrategia dispara no fecho antes do reader ter o read -> cache-miss->read fresco->bloqueio
  ~90s); (5) L1 4H vs read 15M. RECOMENDACAO: so shadow primeiro, medir forward (taxa veto, se veta os 4 WINs, se mata
  a Cp) antes de enforce; ponderar tirar a Cp do gate. ESTADO: NAO aprovado, NAO implementado — Cris "NAO IMPLEMENTAR".
  Detalhe em memory/project_reader_to_strategies_wiring.md.',
  array['seed:memory_delta_20260815a_reader_to_strategies_step2','reader','estrategias','routing','step2','desenho','auditoria','nao-implementado'],
  'memory/project_reader_to_strategies_wiring.md', 'active'),
 (md5('week_review_20260815_14longs_4w_10l')::uuid, 'private', 'internal', 'project',
  'Revisao semana: 14 sinais LONG do grupo = 4 WIN / 10 LOSS, plotados no 15M (plotagem canonica)',
  'Revisao dos trades sinalizados no grupo esta semana (Cris ordenou plotagem canonica de TODOS no 15M, sem inventar):
  14 sinais LONG -> 4 WIN (08-11 cedo) / 10 LOSS (topo 08-12 sinais #6-8, crash 08-13 #10-14). Reader comprou
  continuacao nos topos; A1/A2 mecanico comprou o crash 5x. Plot por research/plot_week_group_signals_20260815.py
  (long_position+label, cor WIN=#2e7d32 LOSS=#c62828 OPEN=#1565c0). Evidencia que motiva o STEP 2 (gatear estrategias
  pelo reader). Datasets as-of: alert-bridge/logs/backtests/XAUUSD_{15m,60m,240m}_replay_2026-08-10_to_2026-08-14.jsonl.',
  array['seed:memory_delta_20260815a_reader_to_strategies_step2','week-review','longs','perdas','plotagem-canonica'],
  'research/plot_week_group_signals_20260815.py', 'active')
on conflict (id) do nothing;
