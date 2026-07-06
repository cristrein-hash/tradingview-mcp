-- ============================================================================
-- SUPABASE MEMORY — DELTA SEED · seed:memory_delta_20260706_event_level
-- ============================================================================
-- Bloco: nivel de evento + kNN nao-linear (2026-07-06).
-- APLICACAO: autonoma via scripts/supabase/apply_memory_delta.py.
-- ROLLBACK: delete from memory_items where tags @> array['seed:memory_delta_20260706_event_level'];
-- Total: 1 row.
-- ============================================================================
begin;

insert into memory_items (id, scope, visibility, category, title, body, tags, source_ref, status) values
(
  md5('seed:memory_delta_20260706_event_level:memory_items:evento-sinal-real-mas-fraco')::uuid,
  'product', 'internal', 'project',
  'Nivel de evento + kNN nao-linear: sinal causal REAL mas FRACO (AUC 0,62, p=0,002)',
  'Reframe unidade=evento (cluster 48h/3ATR, densidade 15:1, 58/60 circulos). FASE A (mapa evento-inteiro): eventos-fundo fortemente distintos (rsi_min8 p=2e-5, dur_h/n_cand/sell_climax/nas/pre_drop/low_wick p<1e-3). DA6: dur_h/n_cand/rev_speed/low_wick = RETROSPECTIVAS (colapsam causalmente) MAS nucleo (rsi/nas/poc/sell_climax/below_poc/flow_div/nas_long) separa ja no 1o candidato causal (9/14 p<0,013). FASE B causal (evento-ate-agora + 1-entrada/evento): 4 seletores falham null (P=0,61-0,84). DA6 gargalo: CLASSIFICAR-evento nao entrar (1o ~= aleatorio ~= base 26%; best-in-acc 54% = 90% inflacao de max-de-K, excesso oracle so 6pp). kNN NAO-LINEAR (15 feats causais do 1o candidato, LOO): AUC 0,623, null-permutacao P=0,002 = ESTRUTURA MULTIVARIADA REAL; top-decil precisao 6->11% (lift 1,8x); MAS hit3R top-decil 26,6% ~= base. VEREDITO (8o caminho, por ML rigoroso): o fundo do Cris TEM assinatura causal (AUC 0,62 significativo, contra ruido/impossivel) MAS sobreposicao grande demais para deteccao FN-operavel (contra so-afinar-resolve). Gap AUC 0,62->0,85 exige DIMENSOES DE FEATURE FALTANTES: micro-forma bar-a-bar da reversao (nunca construida), inter-mercado DXY/yields (EF nao-wired), ou discricionario (CRIS35 = unico que bate nulls). Opcoes p/ Cris: (a) engenheirar micro-forma sequencial; (b) semi-automacao (deteccao top-decil + confirmacao visual); (c) producao com o que passou (CASCEX/RWS-15M).',
  array['seed:memory_delta_20260706_event_level','nivel-evento','knn','sinal-real-fraco','auc','method-lesson'],
  'event_level_map + event_causal_layer + event_knn_nonlinear_20260706.py (commits 3539a25+03c48a4)',
  'active'
)
on conflict (id) do nothing;

commit;
