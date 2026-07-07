-- ============================================================================
-- SUPABASE MEMORY — DELTA SEED · seed:memory_delta_20260707_lookahead_trap
-- ============================================================================
-- Bloco: tentativa vencer-muro-como-PLTDM = lookahead apanhado; natureza causal do muro (2026-07-07).
-- APLICACAO: autonoma via scripts/supabase/apply_memory_delta.py.
-- ROLLBACK: delete from memory_items where tags @> array['seed:memory_delta_20260707_lookahead_trap'];
-- Total: 1 row.
-- ============================================================================
begin;

insert into memory_items (id, scope, visibility, category, title, body, tags, source_ref, status) values
(
  md5('seed:memory_delta_20260707_lookahead_trap:memory_items:escala-walk-lookahead')::uuid,
  'product', 'internal', 'project',
  'Vencer-muro-como-PLTDM (subir escala do walk) = LOOKAHEAD apanhado; muro do winner/loser 15M e causal-fundamental (nao previsivel pre-entry)',
  'Cris: "como venceste o muro PLT/DM? faz o mesmo aqui". Licao PLT/DM = trocar snapshot-feature por PROCESSO sequencial (caminhada de pernas). Apliquei: estado sequencial da escada + subir a ESCALA do master walk. Resultado espetacular e robusto por-ano: r=6 54% -> r=8 61% -> r=9 68% -> r=10 76% -> r=12 80% (N30, 2025:88%/2026:71%). MAS = LOOKAHEAD, apanhado por auto-DA: a caminhada zigzag so rotula um low como "demanda r=12" DEPOIS de a subida de 12-ATR o confirmar — e essa subida E o proprio movimento vencedor; selecionar demandas r=12 = selecionar winners por construcao. TESTE CAUSAL DECISIVO (causal_priorleg_test_20260707.py): a perna ANTERIOR causal (momentum passado, conhecido ANTES do entry) NAO separa — WIN med 12.59 vs LOSE med 12.77; filtrar por ela da no maximo 58% (vs 54% base) e desmorona a thresholds altos. Portanto o ganho de escala era artefato de lookahead. NATUREZA DO MURO (!= PLT/DM): PLT/DM era DETETAR uma estrutura que existe CAUSALMENTE (fundos = demandas da caminhada, identificaveis com dados passados) -> venci mudando a representacao. AQUI a distincao winner/loser depende de a perna ROMPER no FUTURO -> o estado sequencial que separaria E o proprio resultado, nao esta na estrutura pre-entry. "Qual perna rompe" NAO e causalmente previsivel pela estrutura anterior nestes dados; e a aleatoriedade forward do mercado. reclaim-R 61% (causal, ambos anos+, Cris-validado) = o que E causalmente conhecivel; e o teto honesto do que da p/ prever pre-entry. LICAO DE METODO PERMANENTE: ao subir escala/agregacao de um detector baseado em zigzag/pivo, a CONFIRMACAO do pivo usa movimento FUTURO = lookahead embutido; SEMPRE testar a versao causal (features so-passado) antes de celebrar qualquer salto de hit-rate com a escala. Auto-devils-advocate apanhou este; teria envenenado com um 80% falso.',
  array['seed:memory_delta_20260707_lookahead_trap','lookahead-escala-zigzag','muro-causal-fundamental','vencer-muro-pltdm-falhou','reclaim-r-teto-causal','licao-metodo','auto-devils-advocate'],
  'docs/architecture/XAU15M_ENTRY_CONTEXTUAL_FILTER_STUDY_20260707.md sec 6b; sequential_walk_state/causal_priorleg_test_20260707.py (commit ca21524)',
  'active'
)
on conflict (id) do nothing;

commit;
