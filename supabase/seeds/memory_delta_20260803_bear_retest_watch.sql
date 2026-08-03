-- ============================================================================
-- SUPABASE MEMORY — DELTA SEED · seed:memory_delta_20260803_bear_retest_watch
-- ============================================================================
-- Leitura do Cris (bear + reteste p/ vender) + vigia bidirecional armado. 1 row. Idempotente.
-- ============================================================================
begin;
insert into memory_items (id, scope, visibility, category, title, body, tags, source_ref, status) values
(
  md5('seed:memory_delta_20260803_bear_retest_watch:memory_items:read')::uuid,
  'product', 'internal', 'project',
  'Leitura Cris 03/08: tendencia claramente BEAR; ouro vem RETESTAR as demandas superiores (4047-4072) antes de descer — vigia BIDIRECIONAL armado (reteste-rejeicao=short com juizo do reader)',
  'LEITURA DO CRIS (03/08, pos-reabertura): "tendencia e claramente BEAR no visual do grafico; o ouro esta a vir fazer reteste nas demandas superiores antes de descer novamente". OPERACIONAL: o bounce do OB 4028-4036 para cima = reteste para VENDER (nao comprar); zonas de reteste = supply 1H 4047-4062 + supply 15M 4065-4072; alvos por baixo = OB 15M 4028-4036 e depois OB 4H 3995-4010. INSTRUMENTACAO: vigia watch_demanda_reader_20260728.py agora BIDIRECIONAL — lado SHORT novo: toque na supply = heads-up geografico; REJEICAO REAL (tocou e FECHOU de volta abaixo da borda inferior, vela vermelha) = juizo do reader E2 (que desde 03/08 tem os blocos fade-em-supply-com-sequencia + continuacao-em-compressao), com cooldown proprio (90min ou fecho 6pts abaixo); lado LONG mantido (reclaim nas demandas OB 4028-4036 / OB 4H 3995-4010 / CHoCH 4051) caso o bear surpreenda. Cobertura redundante: E1 zone_reject/magnet_reject + R10 top_fade geram nas mesmas zonas e o E2 surfa ao Telegram. Pedido do Cris: avisar no juizo do reader sobre o reteste. Commit 06006b1.',
  array['seed:memory_delta_20260803_bear_retest_watch','leitura-cris-bear-claro','reteste-demandas-superiores-para-vender','supply-4047-4062-e-4065-4072','vigia-bidirecional','rejeicao-real-juizo-reader','alvos-4028-4036-depois-3995-4010'],
  'research/watch_demanda_reader_20260728.py · project_week_eval_20260802_r9_r10 (leitura Cris) · commit 06006b1',
  'active'
)
on conflict (id) do nothing;
commit;
