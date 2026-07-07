-- ============================================================================
-- SUPABASE MEMORY — DELTA SEED · seed:memory_delta_20260707_pltdm_assimilation
-- ============================================================================
-- Bloco: assimilacao do guia manual PLT/DM do Cris + detector de polaridade causal (2026-07-07).
-- APLICACAO: autonoma via scripts/supabase/apply_memory_delta.py.
-- ROLLBACK: delete from memory_items where tags @> array['seed:memory_delta_20260707_pltdm_assimilation'];
-- Total: 1 row.
-- ============================================================================
begin;

insert into memory_items (id, scope, visibility, category, title, body, tags, source_ref, status) values
(
  md5('seed:memory_delta_20260707_pltdm_assimilation:memory_items:pltdm-escada-markup-polaridade')::uuid,
  'product', 'internal', 'project',
  'Assimilacao PLT/DM (guia Cris): retest da escada de markup = 1o discriminador de polaridade BULL na direcao certa (15/8); confluencia N101 recall14/42',
  'META MUDOU (Cris): parar metricas FN; detectar MAIS fundos sem lookahead + verificar entry 3x1 + dividir em familias; ordem ESTRUTURA->INDICADORES->ENTRY; nunca snapshot sem contexto estrutural; regras do Cris = GUIAS nao leis. Chave dada: a zona de demanda criada no retest do topo rompido anterior. Cris plotou no chart 15M 10 PLT (polaridade de topo) + 11 DM (demanda) como guia; extraidos via MCP (results/manual_shapes_pltdm_20260707.json). ASSIMILACAO: PLT = topos ASCENDENTES da escada de markup (higher-highs) rompidos — casam zigzag-high r=3 em 9/10, 0/10 sao EQH (matou hipotese EQH); DM = demanda fresca = origem de perna que rompe estrutura (BOS+ subsequente). ACHADO CENTRAL: retest da ESCADA de markup DISCRIMINA BULL na direcao certa (fund 15% vs nao-fund 8%, ~2x) — as 4 implementacoes genericas anteriores (BOS+/EQH/fractal/suporte-qualquer) TODAS anti-discriminavam (fundos retestavam MENOS). Confluencia PLT uniao DM: BULL 44/33. FRONTEIRA recall x N (universo 954 pivo zigzag, regra por-regime BULL/RANGE=polaridade BEAR=end-of-fall retr alto): confluencia-dupla(lad&dm) N101 recall 14/42 (22 fundos-pivo) = ponto na meta N<=100; pltdm&drop>=6 N228 recall 26; uniao N313 recall 26. LIMITE HONESTO (DA, confirmado em 7 metodos: score linear, CART OOF, fluxo, 4 impl polaridade, escada, DM, confluencia): N<=100 com recall alto NAO atingivel com features 15M — os ~16 fundos MISSED sao pullbacks BULL rasos (medianas fund BULL: drop 11 ATR mas retr 0,17 sweep -0,8 = queda local grande, retracao macro rasa, NAO varre minimos) estatisticamente indistinguiveis de pullbacks nao-marcados; residuo = DISCRICIONARIO (por isso Cris marca PLT/DM a mao). Casas do separador nao-cobertas: micro-forma/sequencia da reversao (shape bar-a-bar) / perna HTF 4H-1D / inter-mercado. PROXIMO (fork Cris decide): aceitar N101 ou N228 -> entry 3x1 + familias; ou marcar mais PLT/DM fora ago-out25; ou engenheirar micro-sequencia/perna-HTF.',
  array['seed:memory_delta_20260707_pltdm_assimilation','pltdm','escada-markup','polaridade-causal','detector-fundo-15m','residuo-discricionario','meta-detectar-fundos'],
  'docs/architecture/XAU15M_PLTDM_ASSIMILATION_20260707.md; assimilate_pltdm/bottom_polarity_scalev2/bottom_polarity_ladder/bottom_pltdm_confluence_20260707.py (commit b287bab)',
  'active'
)
on conflict (id) do nothing;

commit;
