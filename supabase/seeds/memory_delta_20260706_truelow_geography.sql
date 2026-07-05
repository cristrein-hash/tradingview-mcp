-- ============================================================================
-- SUPABASE MEMORY — DELTA SEED · seed:memory_delta_20260706_truelow_geography
-- ============================================================================
-- Bloco: ondas v2 low-verdadeiro + geografia dos 60 circulos (2026-07-06).
-- APLICACAO: autonoma via scripts/supabase/apply_memory_delta.py.
-- ROLLBACK: delete from memory_items where tags @> array['seed:memory_delta_20260706_truelow_geography'];
-- Total: 1 row.
-- ============================================================================
begin;

insert into memory_items (id, scope, visibility, category, title, body, tags, source_ref, status) values
(
  md5('seed:memory_delta_20260706_truelow_geography:memory_items:truelow-negativos-geografia')::uuid,
  'product', 'internal', 'project',
  'Ondas v2 low-verdadeiro: F0 refutada, banda com skew-2025, GEOGRAFIA dos 60 circulos',
  'Correcao declarada executada com licoes de metodo (seeds fixas, precisao por circulo distinto, sub-janela anual, painel por episodio). (a) Hipotese "sosia estrutural = entra acima do low real" REFUTADA pela medicao corrigida: 59% da banda entra <=0,2ATR do low verdadeiro (GT 71% vs sosia 59%, sem poder) — o universo flush-reclaim ja seleciona lows por construcao. (b) vol_dryup = separador de mediana (GT 0,86 vs 1,03) mas corte da 24,6% < banda: separador-de-mediana != edge. (c) T1-T3 P_episodio 0,07-0,14, 2024 negativo; DA4: banda inteira tem skew-2025 (2024 -107, 2025 +62, 2026 -71) — qualquer corte interno herda o loading. (d) GEOGRAFIA (muda arquitetura): banda retr 0,5-1,3 alcanca 34/60 circulos; 11 sao MAIS FUNDOS (retr 1,35-8,26, abaixo da projecao da perna); 8 mais RASOS (0,23-0,48); 2 sem perna zigzag; 5 circulos (4,5,6,16,34) SEM CANDIDATO no universo (gerador flush-reclaim nao os ve). CONCLUSAO: retr deve ser FEATURE nunca FILTRO; recall-first: consertar gerador p/ os 5 invisiveis, montar seletor de cobertura circulo-a-circulo, so entao discriminar. Mandato Cris: encontrar todas/maior parte das 60 com lucro e streak baixo; sem amostra nova.',
  array['seed:memory_delta_20260706_truelow_geography','layer-2','geografia-circulos','refutada','method-lesson'],
  'inband_truelow_waves_20260705.py + inband_truelow_da4_probe.py (commit 26ec573)',
  'active'
)
on conflict (id) do nothing;

commit;
