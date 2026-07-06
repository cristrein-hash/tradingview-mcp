-- ============================================================================
-- SUPABASE MEMORY — DELTA SEED · seed:memory_delta_20260706_raw_indicators
-- ============================================================================
-- Bloco: aprofundamento indicadores RAW dedicados (2026-07-06).
-- APLICACAO: autonoma via scripts/supabase/apply_memory_delta.py.
-- ROLLBACK: delete from memory_items where tags @> array['seed:memory_delta_20260706_raw_indicators'];
-- Total: 1 row.
-- ============================================================================
begin;

insert into memory_items (id, scope, visibility, category, title, body, tags, source_ref, status) values
(
  md5('seed:memory_delta_20260706_raw_indicators:memory_items:raw-discrimina-mediana-nao-detector')::uuid,
  'product', 'internal', 'project',
  'Indicadores RAW dedicados: discriminam mediana (MWU) mas NAO viram detector sob null honesto',
  'Cris: builder aggregations nao bastavam, indicadores RAW DEVEM discriminar, nao desista. Construi 26 features RAW DEDICADAS causais (bubbles/absorcao/NAS/RSI-profundo/SMC-OB/Volume-Profile SVP) + convergencias cruzadas. RESULTADO 2 NIVEIS: (1) MWU winner-vs-sosia por familia = SINAL REAL (Cris certo): FUNDO sell_climax4 p=0,031; BANDA rsi_min8 p=0,0005, poc_dist(SVP) p=0,018, vol_climax; RASO (mais rica) nas_dist p=0,003 (0,42 vs 1,31), rsi_min8 p=0,0003, below_poc(SVP) p=0,010, rsi_cj p=0,005. (2) MAS nao vira detector: seletores de corte falham null-episodio (0,86-0,99); score combinado ponderado da lift-deteccao 1,8-2,1x MAS P(lift>=obs)=0,19-0,49 sob null-permutacao-ATRAVES-do-mecanismo = lift do acaso. CAUGHT OWN LEAK: sell_absorb8 (p=0,012) usava barras APOS a bubble futuras ao cj; fix bt+4<=ci matou. DISTINCAO METODOLOGICA PERMANENTE: deslocar mediana (MWU p<0,01) != detector rentavel quando alvo e 3-5% com caudas sobrepostas; teto de densidade explica o gap. Hold-out temporal impossivel (60 circulos todos pos-ago/2025). Caminho inexplorado (nao esgotado): nivel de EVENTO — agregar features RAW por cluster e classificar EVENTOS (1-em-10-15), nao candidatos (1-em-37); o Cris classifica o EVENTO olhando. Cache reusavel: results/raw_feature_cache_20260706.jsonl.',
  array['seed:memory_delta_20260706_raw_indicators','indicadores-raw','mediana-vs-detector','svp','method-lesson'],
  'raw_indicator_discriminator + raw_family_layers + raw_score_detector_20260706.py (commits 7346917+a0e460b)',
  'active'
)
on conflict (id) do nothing;

commit;
