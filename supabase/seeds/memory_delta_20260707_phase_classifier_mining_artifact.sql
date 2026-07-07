-- ============================================================================
-- SUPABASE MEMORY — DELTA SEED · seed:memory_delta_20260707_phase_classifier_mining_artifact
-- ============================================================================
-- Bloco: classificador de fase do ciclo (workflow) = MATO pelo DA (winner's-curse de mineracao composta) (2026-07-07).
-- ROLLBACK: delete from memory_items where tags @> array['seed:memory_delta_20260707_phase_classifier_mining_artifact'];
-- Total: 1 row.
-- ============================================================================
begin;
insert into memory_items (id, scope, visibility, category, title, body, tags, source_ref, status) values
(
  md5('seed:memory_delta_20260707_phase_classifier_mining_artifact:memory_items:fase-ciclo-mining-artifact')::uuid,
  'product', 'internal', 'project',
  'Classificador de FASE do ciclo (workflow multi-agente) = MATO pelo Devil''s Advocate: winner''s-curse de mineracao composta; discriminador real = reclaim_lag disfarcado',
  'Apos leitura estrutural TOTAL dos prints (4 fases: A markup-ativo/B iniciacao/C distribuicao-topo/D bear-ativo; separador = posicao-no-ciclo, nao demanda-proximidade que foi refutada), Cris pediu engine multi-agente do classificador de fase. Workflow wf_24a7c342: 7 classificadores causais; 3 sobreviveram gates (FaseD-bear N73 0.603, CHoCH-up-no-fundo N45 0.667, FSM-4-estados N54 0.63); sintese combinou por intersecao FaseD INTERSECT FSM4 = N44 hit-3R 68.2% (+14pp), poison 0.73, 2025 70.8%/2026 65.0%, corta 18/22 loser-targets, null single-look P=0.0096. DEVIL''S ADVOCATE INDEPENDENTE (obrigatorio por hook, corrido ANTES de reportar) = VEREDITO (c) ARTEFATO DE MINERACAO / WINNER-CURSE: reconstruiu o menu real = 1257 avaliacoes / 547 masks distintas em 7 familias × 13 set-ops sobre 96 outcomes FIXOS. Mining-null (shuffle de outcomes + re-seleccao da pipeline): mediana do melhor-gate-passing hit-3R = 0.6857 SUPERIOR ao observado 0.682; P(best_null>=0.682)=0.515 = moeda ao ar. O +14pp senta-se NA MEDIANA do que a mineracao produz de puro ruido. Sob multiplicidade real (Sidak a 547 masks) o P single-look 0.0096 vira ~0.995. Intersecao FABRICA o hit: FaseD sozinho 0.603, FSM4 0.630, UNIAO 0.578 (abaixo base!), so a INTERSECAO 0.682 por encolher N 83->44 = concentracao mecanica best-of-13. Discriminador REAL por baixo = reclaim_lag (reclaim rapido), NAO fase: winners-mantidos rl mediana 3.0 vs winners-cortados 8.0 vs losers-cortados 7.0 = "manter reclaim rapido, cortar reclaim lento" disfarcado de maquina 4-estados; corta winners genuinos (#29 rl16, #96 rl13, #1, #95) pelo mesmo eixo que corta losers. OOS esperado ~= base 54.2%; +14pp deve evaporar. CONCLUSAO: SEM edge novo. Os losers Fase-C (distribuicao-topo) sao ESTRUTURALMENTE INDISTINGUIVEIS do markup com features 15M in-sample. Teto honesto continua reclaim-R ~61% (unico causal-clean nao-mining). LICAO DE METODO PERMANENTE: null single-look de um resultado escolhido de N masks/combos e IRRELEVANTE; o null correto e o MINING-NULL (re-correr toda a pipeline de selecao sobre outcomes embaralhados) — se a mediana do best-of-menu sob ruido >= observado, e artefato. Sempre contar TODOS os looks (features × variantes × set-ops), nao so a ultima camada. Scripts da_mining_null / da_attacks_345_20260707.py; doc XAU15M_TOTAL_STRUCTURAL_READING_20260707.md. commit 4fe7412.',
  array['seed:memory_delta_20260707_phase_classifier_mining_artifact','classificador-fase-ciclo','mining-null','winners-curse-composto','reclaim-lag-disfarcado','devils-advocate-matou','licao-metodo-mining-null'],
  'docs/architecture/XAU15M_TOTAL_STRUCTURAL_READING_20260707.md; da_mining_null/da_attacks_345_20260707.py (workflow wf_24a7c342, commit 4fe7412)',
  'active'
)
on conflict (id) do nothing;
commit;
