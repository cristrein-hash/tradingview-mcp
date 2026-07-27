-- ============================================================================
-- SUPABASE MEMORY — DELTA SEED · seed:memory_delta_20260727_stacked_zones
-- ============================================================================
-- Gap #1 (topo invisivel) FECHADO em producao: stack de zonas empilhadas/atravessadas no E0/E1.
-- Aplicar via scripts/supabase/apply_memory_delta.py. Idempotente. Total: 1 row.
-- ============================================================================
begin;
insert into memory_items (id, scope, visibility, category, title, body, tags, source_ref, status) values
(
  md5('seed:memory_delta_20260727_stacked_zones:memory_items:stacked-zones-golive')::uuid,
  'product', 'internal', 'decision',
  'E1 STACKED ZONES em producao (gap #1 do topo invisivel FECHADO, Cris 2026-07-27) — bug real = zonas ATRAVESSADAS, nao N-nearest',
  'Plan-agent (design) + implementacao + go-live no mesmo dia, aprovado Cris ("SEGUE, PODE IMPLEMENTAR"). BUG REAL (achado do Plan agent que mudou o fix): zonas que o preco ATRAVESSA nao satisfazem low>last (above) nem high<last (below) -> eram deitadas fora pela vista nearest-only; foi assim que o topo de supply em camadas 4110-4116 de 27/07 ficou invisivel (0 vendas geradas; Cris vendeu o topo manualmente). Um N-nearest ingenuo AINDA as perderia. FIX: context_mtf._zone_view = helper UNICO (caminho STORE _zones_from_payload E caminho MCP _nearest_zones em lockstep — o caminho vivo de producao e o do store!) com above/below VERBATIM (paridade byte G1 PASS) + campo aditivo stack{above,below} nearest-first N=3 com dedup por geometria (estudos duplicados no chart, HTF PoT x2, desperdicavam slots) — membership: above=high>last, below=low<last (inclui atravessadas, que aparecem nos 2 lados). e1_detector: R4 zone_reject e R7 magnet_reject iteram o stack via _zstack (nearest-first + break = 1 candidato/regra/dir/bar; SL ancora na zona REJEITADA especifica via dict(zones,side=z) — regra levels intocada; fallback nearest-only se flag OFF/stack ausente). FLOOD contido de graca: entry=close para todos os candidatos do stack -> anti-spam-por-zona e collapse deduplicam (G3 PASS 1-de-2). GATE research/gate_stacked_zones_20260727.py: G1 paridade OFF byte-exata · G2 recall na barra REAL 02:15 27/07 (OFF=0 reproduz o miss real; ON=SHORT zone_reject entry 4100.08 SL-estrutural 4114.32 rr 3.0) · G3 contencao; selftest flag-OFF byte-identico. DEPLOY: flag E1_STACKED_ZONES=1 exportada nos DOIS wrappers (context constroi, e1 consome; restart context primeiro), backups .pre_stacked_bak, rollback = tirar flag + kickstart. PROVA VIVA pos-deploy: stack do dossie inclui a PoT 4081-4090 atravessada NOS 2 LADOS (o caso que a logica antiga deitava fora) e, apos dedup, a demanda 4065-4070 (a New York Low onde o Cris comprou o fundo, antes invisivel). Limitacao declarada: nao ha historico de zonas (replay 16-24/07 = so corroboracao direcional). Commits: pacote + dedup/wrappers (git log 27/07). Gap #2 (long em fundo fresco bear, Cp nao apanhou flush ~14xATR) = pendente, fase de caracterizacao antes de codigo (nunca baixar limiar do Cp congelado ao dia visivel).',
  array['seed:memory_delta_20260727_stacked_zones','e1','stacked-zones','zonas-atravessadas','topo-invisivel-fechado','paridade-byte','sl-zona-rejeitada','anti-flood-gratis','flag-reversivel','plan-agent','user-approved','producao'],
  'alert-bridge/context_mtf.py::_zone_view/_zs_of · alert-bridge/e1_detector.py::_zstack/detect · research/gate_stacked_zones_20260727.py · research/poc_stacked_zones_20260727.py · wrappers start_{context_engine,e1_detector}.sh',
  'active'
)
on conflict (id) do nothing;
commit;
