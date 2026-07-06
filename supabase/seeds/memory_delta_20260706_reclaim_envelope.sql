-- ============================================================================
-- SUPABASE MEMORY — DELTA SEED · seed:memory_delta_20260706_reclaim_envelope
-- ============================================================================
-- Bloco: entry-bar reclaim (refutado DA7) + filtro de envelope de evento (validado) (2026-07-06).
-- APLICACAO: autonoma via scripts/supabase/apply_memory_delta.py.
-- ROLLBACK: delete from memory_items where tags @> array['seed:memory_delta_20260706_reclaim_envelope'];
-- Total: 1 row.
-- ============================================================================
begin;

insert into memory_items (id, scope, visibility, category, title, body, tags, source_ref, status) values
(
  md5('seed:memory_delta_20260706_reclaim_envelope:memory_items:reclaim-refutado-envelope-validado')::uuid,
  'product', 'internal', 'project',
  'Entry-bar reclaim REFUTADO (DA7 null errado); FILTRO de envelope de evento VALIDADO (recall 100%)',
  'Cris apontou que forcar entry no 1o candidato falha (o fundo se constroi ao longo de barras). Mapa: RECLAIM (close>high[-1] pos-low-do-evento) vira NET negativo->+156 = entry-bar correta e a confirmacao de reversao. Politica 1o-reclaim/evento (P0): N376 hit3R 31,9% NET +67 anos+; afinacao two_up N224 33,9% DD-16. DA7 REFUTOU: null ERRADO (permutava universo); null correto (candidato aleatorio do MESMO evento) iguala reclaim ~80% (episode-null 0,795/0,845); timing intra-evento NAO adiciona; two_up INERTE; nao sobrevive Bonferroni x10; 95% do NET em 3 trimestres. reclaim/two_up = REFUTED. Unico sobrevivente do DA = selecao-de-evento fraca (+2,4pp). Cris (ordem correta): inverter — FILTRAR eventos-lixo com os 60 fundos ANTES da entry. FILTRO DE ENVELOPE VALIDADO: envelope multi-feature dos eventos-fundo, versao CAUSAL alto-recall (ate 3o cand): mantem 50/50 fundos + 58/60 circulos (recall 100%), corta 39% dos eventos, densidade 14,9:1->8,8:1, P(null envelope-aleatorio)=0,0000 — eventos-fundo ocupam regiao COMPACTA identificavel (1o filtro a bater null com recall 100%). MAS hit3R do pool filtrado so 27,6->28,6% (marginal). Arquitetura validada: estagio-1 filtro (14,9->8,8:1) -> estagio-2 entry/classificacao no pool limpo (desafio aberto em densidade menor). LICAO DA7 PERMANENTE: em pool clusterizado por evento, null DEVE ser por-episodio/dentro-do-evento; null-universo credita a entry o efeito de selecao-de-evento.',
  array['seed:memory_delta_20260706_reclaim_envelope','reclaim-refutado','envelope-filter','recall-100','null-por-episodio','method-lesson'],
  'event_entry_bar_map + event_reclaim_entry + reclaim_microform_refine + event_envelope_filter_20260706.py (commits 6ba3b9b..971dd6c)',
  'active'
)
on conflict (id) do nothing;

commit;
