-- ============================================================================
-- SUPABASE MEMORY — DELTA SEED · seed:memory_delta_20260706_ordering_cascade
-- ============================================================================
-- Bloco: aperto filtro + estagio-2 + virada de ordenamento (DA8) (2026-07-06).
-- APLICACAO: autonoma via scripts/supabase/apply_memory_delta.py.
-- ROLLBACK: delete from memory_items where tags @> array['seed:memory_delta_20260706_ordering_cascade'];
-- Total: 1 row.
-- ============================================================================
begin;

insert into memory_items (id, scope, visibility, category, title, body, tags, source_ref, status) values
(
  md5('seed:memory_delta_20260706_ordering_cascade:memory_items:ordenamento-circular-cascata-limpa')::uuid,
  'product', 'internal', 'project',
  'Aperto por-familia REAL, virada de ordenamento CIRCULAR, cascata = unico degrau limpo (DA8)',
  'APERTO CRIATIVO: filtro por-FAMILIA (envelope separado por retracao) densidade 14,9:1->5,6:1 recall 100% (50/50 fundos), Mahalanobis null P=0,004 = melhor filtro estagio-1. VIRADA DE ORDENAMENTO (Cris: entry so funciona DENTRO do evento-fundo, testar no geral = otica erronea): DENTRO dos 50 eventos-fundo 1o-candidato = 52% hit3R. DA8: CIRCULAR — 100% dos eventos-fundo contem 3R (circulo marcado onde preco subiu); condicionar em evento-com-3R generico ja da 45%; incremento do circulo 44->52% = ruido (N50); null-dentro-do-fundo 0,87 = entry nao adiciona. Metodo do Cris esta certo (entry nao e gargalo, selecao e) MAS ter o evento correto ex-ante e o problema dificil (AUC 0,62), nao resolvido pela virada. ESTAGIO-2 (familia->cascade>=4->reclaim) E5 N19 WR52,6% / E6 N29 WR51,7% — DA8 REFUTA como edge FN: N minusculo (E5 indistinguivel de moeda P=0,68 vs 50%), Bonferroni x14 mata (p=0,25), reclaim NAO adiciona (cascata sozinha 34,6% = todo o trabalho; familia+reclaim sem cascata=28,1%=base), salto = compressao de N. E5∩CASCEX=5/19 (fork-irmao). CONCLUSAO ESTRUTURAL: unico degrau causal limpo = CASCATA SMC (27,6->34,6% N228) = veia do CASCEX pre-aprovado (filtros completos: 55,9% WR N34). Extensoes NAO superam CASCEX robustamente. Metodo ordenamento (estrutura->selecao->entry) certo e CASCEX ja o implementa. Gap restante = leitura-de-evento ex-ante (cascata mecanica 34-55% vs discricionario CRIS35). LICAO DA8: rotulo-oraculo (circulo=onde-subiu) torna hit3R-dentro-do-fundo tautologico; medir incremento sobre evento-com-3R-generico, nao sobre o geral.',
  array['seed:memory_delta_20260706_ordering_cascade','aperto-familia','ordenamento-circular','cascata','cascex','method-lesson'],
  'event_filter_tighten + event_stage2_entry_20260706.py + _da8_audit (commits aa5d7ff..34d759e)',
  'active'
)
on conflict (id) do nothing;

commit;
