-- ============================================================================
-- SUPABASE MEMORY — DELTA SEED · seed:memory_delta_20260706_coverage_oracle
-- ============================================================================
-- Bloco: autopsia circulos invisiveis + matcher v2 + teto oracle (2026-07-06).
-- APLICACAO: autonoma via scripts/supabase/apply_memory_delta.py.
-- ROLLBACK: delete from memory_items where tags @> array['seed:memory_delta_20260706_coverage_oracle'];
-- Total: 1 row.
-- ============================================================================
begin;

insert into memory_items (id, scope, visibility, category, title, body, tags, source_ref, status) values
(
  md5('seed:memory_delta_20260706_coverage_oracle:memory_items:autopsia-matcher-v2-oracle')::uuid,
  'product', 'internal', 'project',
  'Recall-first passos 1+2: autopsia dos invisiveis, MATCHER v2 assimetrico, teto oracle +169,6R',
  'Autopsia dos 5 circulos GT invisiveis: 4/5 eram artefato do MATCHER (candidatos existiam com flush 1-2,6 ATR ABAIXO do low do circulo = mesmo fundo, pavio mais fundo; regra simetrica +-1ATR rejeitava); circulo 34 = warmup-hole de bloco (p>=96, 24h por inicio de bloco; conserto = stitch futuro); circulo 6 = sem candidato fractal no low. MATCHER v2 OFICIAL (assimetrico): captura se |dt|<=8h E -3ATR <= (flush_cand - low_circulo) <= +1ATR (so relaxa o lado de baixo; lado que inflava recall preservado). Cobertura 55->58/60. TETO ORACLE (declarado, nao estrategia): nos 58 capturados TODO circulo tem candidato 3R — oracle +169,6R hit 58/58; 1o-cronologico sem escolha +96,0R hit 40/58=69%. Sub-fato: nos 18 circulos onde 1o falha e oracle vence, estrutura = 1a tentativa stopada -> tentativa posterior vence (re-entry INTRA-episodio de fundo = questao aberta distinta da re-entry global morta). Passo 3 aprovado: mapear features por familia estrutural (banda 34 / fundos>1,3 11 / rasos<0,5 8 / sem-perna 2) sobre candidatos vencedores vs sosias da familia -> padrao de entry por familia; se preciso, layers separados por base estrutural.',
  array['seed:memory_delta_20260706_coverage_oracle','recall-first','matcher-v2','oracle','layer-2'],
  'gt_invisible_circles_autopsy_20260706.py + circle_coverage_oracle_20260706.py (commit 64d87ad)',
  'active'
)
on conflict (id) do nothing;

commit;
