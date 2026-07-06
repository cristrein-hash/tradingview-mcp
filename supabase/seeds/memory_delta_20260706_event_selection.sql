-- ============================================================================
-- SUPABASE MEMORY — DELTA SEED · seed:memory_delta_20260706_event_selection
-- ============================================================================
-- Bloco: selecao causal de evento (familia+cascata sinergia) + layers por regime (2026-07-06).
-- APLICACAO: autonoma via scripts/supabase/apply_memory_delta.py.
-- ROLLBACK: delete from memory_items where tags @> array['seed:memory_delta_20260706_event_selection'];
-- Total: 1 row.
-- ============================================================================
begin;

insert into memory_items (id, scope, visibility, category, title, body, tags, source_ref, status) values
(
  md5('seed:memory_delta_20260706_event_selection:memory_items:selecao-evento-familia-cascata-layers')::uuid,
  'product', 'internal', 'project',
  'Selecao causal de evento: sinergia familia+cascata (WR 55%) + layers por regime (uniao WR 48% N65)',
  'Cris: baixar densidade mantendo top-60, sem look-ahead, sem conclusoes. Filtros causais (features<=cj, outcome nunca na decisao = NAO circular): envelope por-familia recall 100% dens 5,6:1 P(null)=0,004; k-means sub-tipo dens 10:1 (pior); features-especificas dens 7:1; cascade-no-evento dens 3:1 recall 12%. SINERGIA CENTRAL: familia+cascata JUNTAS >> cada uma so. familia&casc>=3->E6(cascade>=3&hl&reclaim): N20 WR 55% streak-q95 6 DD-2,3 anos+; familia&casc>=2->E6: N26 WR 50%. SEM familia (cascata so): WR 32% streak-8 — familia(envelope-retracao) corta capitulacoes BEAR-continuas nao-fundo, garante PULLBACK. Nulls: entry-E6-vs-aleatorio-no-evento P=0,20 (entry nao e edge, confirma DA8); cascata redundante com E6. DOIS REGIMES DE FUNDO: CAPITULACAO (cascata) WR 55% streak-q95 6 poucos sinais; SUAVE (oversold+demanda+reclaim, sem cascata) WR 44-47% streak-q95 9 (sem assinatura estrutural, dificil separar fundo-suave de lixo-suave). UNIAO: N65 WR 47,7% NET+52,5 DD-4,1 streak-q95 9, 0,59/sem, 7 circulos, anos+ fortes (2024+9,4/2025+22,9/2026+20,5). Trade-off recall x WR: qualidade (capitulacao) vs cobertura (uniao); teto AUC 0,62 manifesta no regime suave. EM CURSO: afiar layer suave / layers por tipo p/ mais recall mantendo WR.',
  array['seed:memory_delta_20260706_event_selection','selecao-evento','familia-cascata-sinergia','layers-regime','em-curso'],
  'event_{multilayer,subtype,famspecific,cascade_filter_curve,soft_layer}_20260706.py (commits 8038cbd..729e4ff)',
  'active'
)
on conflict (id) do nothing;

commit;
