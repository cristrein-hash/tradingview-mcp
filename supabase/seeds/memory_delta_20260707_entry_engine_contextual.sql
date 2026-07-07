-- ============================================================================
-- SUPABASE MEMORY — DELTA SEED · seed:memory_delta_20260707_entry_engine_contextual
-- ============================================================================
-- Bloco: engine de entry 3R sobre MASTER markup/correcao (VALIDADO visualmente Cris) + estudo losers (2026-07-07).
-- APLICACAO: autonoma via scripts/supabase/apply_memory_delta.py.
-- ROLLBACK: delete from memory_items where tags @> array['seed:memory_delta_20260707_entry_engine_contextual'];
-- Total: 1 row.
-- ============================================================================
begin;

insert into memory_items (id, scope, visibility, category, title, body, tags, source_ref, status) values
(
  md5('seed:memory_delta_20260707_entry_engine_contextual:memory_items:entry-3r-markup-master-losers')::uuid,
  'product', 'internal', 'project',
  'Engine de entry 3R sobre MASTER markup/correcao = MELHOR entry 15M ate agora (Cris validou visual); estudo losers refuta exaustao/bearleg, lever real = macro-trending + reclaim-speed',
  'RECONTEXTUALIZACAO a partir da leitura contextual de perna (caminhada markup/correcao MASTER). Engine entry 3R (entry_engine_master_20260707.py): universo = demandas de perna, janela ago25->2026-07-03 N164; entry causal = reclaim EMA21 apos demanda, SL=demanda-0.1ATR (regra V1), target +3R, outcome forward-only. BASELINE sem seletor: MARKUP 54.2% hit-3R (N96, 2025:63%/2026:46%) vs CORRECAO 39.7% -> a leitura de perna E por si bom engine 3R (breakeven 25%, ~2/sem, ambos anos+, causal). Seletor lider: reclaim_lag<=4 (reclaim rapido) 61.4% N44 (2025:68%/2026:55%), concentrado em <=2 barras (75% N20). Features SEQ do RWS (buy_recent) VAZIAS nesta populacao. CRIS VALIDOU VISUALMENTE (chart): os R (reclaim rapido) concentram verdes nas pernas fortes = CORRETO; "melhor estrategia de entry que fizemos em 15M disparado; percebes como leitura contextual que revela macro-estruturas funciona mesmo?". 96 sinais plotados (outcome-mode, sufixo R, via skill plotting-canon; removidas 130 ops anteriores preservando 50 circle+92 text_note do Cris). ESTUDO DE CASO LOSERS (filtragem CONTEXTUAL antes de indicadores, ordem Cris; loser_case_study_20260707.py): as 3 hipoteses do Cris TESTADAS -> (1) EXAUSTAO/entrada-alta NAO separa (leg_pos 0.39 loser vs 0.38 winner); (2) MACRO-BEARLEG REFUTADO (BEAR hit-3R 60.9% > BULL 55.9%; filtrar BEAR PIORA 2026); (3) NEAR-MISS pequeno (4/44 losers MFE>=2.5R; 40/44 falham cedo). LEVER CONTEXTUAL REAL: macro RANGE fraco 35.7% (3R precisa de tendencia p/ estender) -> cortar RANGE 54.2->57.3% ambos anos mantem N82; +reclaim rapido trending&R 66.7% N36 (2025:76%/2026:58%); reclaim<=2 77.8% N18. 27/44 losers = reclaim lento. Contexto de perna LARGAMENTE EXAURIDO (posicao/extensao/bearleg nao ajudam). PROXIMO (decisao Cris): indicadores p/ detetar exaustao nos ~12 losers que falham cedo dentro de trending&fast. CAVEAT: combos in-sample, cautela winner-curse; macro-trending = hipotese pre-especificada mecanica (defensavel); combo grelha 67% ja mostrado ser winner-curse (P null 0.45). LICAO: leitura contextual revelando macro-estrutura (markup/correcao master + reclaim-speed) = onde o edge 15M realmente vive; snapshot/features isoladas batiam no muro.',
  array['seed:memory_delta_20260707_entry_engine_contextual','entry-3r','markup-master','reclaim-speed','loser-case-study','macro-trending','cris-validou-visual','melhor-entry-15m'],
  'entry_engine_master/loser_case_study/plot_entry_signals_canonical_20260707.py (commits 2baf2e2,28db774,791a3a4)',
  'active'
)
on conflict (id) do nothing;

commit;
