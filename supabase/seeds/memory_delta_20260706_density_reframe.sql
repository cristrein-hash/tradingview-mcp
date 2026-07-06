-- ============================================================================
-- SUPABASE MEMORY — DELTA SEED · seed:memory_delta_20260706_density_reframe
-- ============================================================================
-- Bloco: reframe da densidade (unidade candidato -> evento) (2026-07-06).
-- APLICACAO: autonoma via scripts/supabase/apply_memory_delta.py.
-- ROLLBACK: delete from memory_items where tags @> array['seed:memory_delta_20260706_density_reframe'];
-- Total: 1 row.
-- ============================================================================
begin;

insert into memory_items (id, scope, visibility, category, title, body, tags, source_ref, status) values
(
  md5('seed:memory_delta_20260706_density_reframe:memory_items:reframe-densidade-evento')::uuid,
  'product', 'internal', 'project',
  'Reframe densidade: a parede 37:1 era da UNIDADE (candidato), nao do grafico — evento ~10:1',
  'Cris desafiou "37:1 indistinguivel e IMPOSSIVEL no grafico" e tinha razao. (a) Reframe por PERNA refutou meu proprio palpite: fundos tem perna MENOR (travel 20 vs 30 ATR); filtrar por perna grande REMOVE fundos (44/60). (b) Reframe DEMANDA-VERDADEIRA (nivel revisitado com memoria, descricao literal do Cris) NAO colapsa (37,7:1, 44/60) — maioria dos candidatos tambem toca demanda revisitada. (c) GRANULARIDADE = resposta: o gerador crava varios fractais k=3 no mesmo movimento; colapsando em EVENTOS a densidade despenca mantendo 58/60 circulos: candidato 37:1 -> visual(24h/2ATR) 22:1 -> largo(48h/3ATR) 15:1 -> dia 10:1. REFORMULACAO ARQUITETURAL: o problema nao e discriminar 1-em-37 candidatos (impossivel); e (1) CLASSIFICAR EVENTOS (1-em-10-15, tratavel) e (2) escolher o melhor candidato DENTRO do evento-fundo (oracle +169R disponivel, 1o-crono +96R/69%). 604 dias-com-setup, 55 tem fundo = 1 em ~11 dias; o olho distingue 1 de 10-11 por contexto, nao 1 de 37. Proxima fase (decisao Cris): features de EVENTO agregadas p/ classificar evento-fundo, depois politica de entrada intra-evento.',
  array['seed:memory_delta_20260706_density_reframe','densidade','reframe','evento','arquitetura'],
  'density_reframe_leg + density_true_demand + density_granularity_20260706.py (commit 0b4056e)',
  'active'
)
on conflict (id) do nothing;

commit;
