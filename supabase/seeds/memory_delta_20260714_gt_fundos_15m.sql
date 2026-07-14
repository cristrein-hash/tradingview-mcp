-- ============================================================================
-- SUPABASE MEMORY — DELTA SEED · seed:memory_delta_20260714_gt_fundos_15m
-- ============================================================================
-- Sessao 2026-07-14: GT unico de fundos 15M (ancora) + sub-discriminacao em camadas de entry.
-- Aplicar via scripts/supabase/apply_memory_delta.py. Idempotente. Total: 1 row.
-- ============================================================================
begin;
insert into memory_items (id, scope, visibility, category, title, body, tags, source_ref, status) values
(
  md5('seed:memory_delta_20260714_gt_fundos_15m:memory_items:gt-fundos')::uuid,
  'product', 'internal', 'project',
  'GT UNICO DE FUNDOS 15M (ancora estudos entry) + sub-discriminacao em CAMADAS DE ENTRY = USER_APPROVED',
  'Cris aprovou (2026-07-14) o GT unico de fundos como ancora dos estudos de entry 15M com otica renovada (sob o stack Layer1 macro 1D + Layer2 leg 4H v3). CONSTRUCAO (fundos_gt_unify.py): unifica catalog_manual_tags_20260707 notas "VELA DE FUNDO" (42) + circulos (50); REGRAS Cris: prioridade a VELA (onde ha vela+circulo <=12h, fica a vela); circulo-only snapado a MENOR LOW 15M em +-6h (RAW-only do HD externo raw_replay/XAUUSD/15M, extrai ohlcv direto dos snapshots de replay, SEM slim/cache local); -4 INVALIDO => 61 FUNDOS. Auditoria comparativa (fundos_regime_context_audit.py) provou que notas e circulos sao o MESMO fenomeno (81% mesmo-dia, leg-dist quase identica) => unir, nao 2 categorias. DISCRIMINACAO por regiao (macro+leg causal) confirmou 3 classes; sub-discriminadas (fundos_gt_subdiscriminate.py) em 5 CAMADAS DE ENTRY operacionais + 1 descarte: A1_pullback_fundo 14 (BULL leg ACUM/PULLBACK_BEAR = reteste-corretivo) · A2_pullback_raso 18 (BULL leg IMPULSO_UP = continuacao-impulso) · B_range 15 · C_PANIC_aguda 5 (BEAR pull20>=18 = capitulacao aguda/panico, crash mar/26) · C_GRIND_profundo 3 (BEAR dd252>=25 & pull20 baixo = fundo profundo lento, jun/26) · C_shallow_bounce 6 (descarte). DECISOES Cris: A cortado por LEG (mecanica de entrada distinta), profundidade (pull20/dd252) = ATRIBUTO por fundo p/ sizing/R:R, nao camada; C em duas subcamadas profundas SEPARADAS (aguda vs lenta) + shallow a parte; classe C = capitulacoes que valem pegar = layer de entry especifico. Causal close-only (dd/pull do 1D conhecido<=t). N por camada pequeno = para DESENHAR, validacao vem com forward (Cris aprovou o caveat). Ficheiro ancora: results/REGIME_GT_FUNDOS_UNIFIED_20260714.json. Commits 17d3df1 (ancora) + a19abdb (sub-discriminacao). PROXIMO: desenhar mecanica de entry por camada (A1/A2/B/C_PANIC/C_GRIND) sob o stack.',
  array['seed:memory_delta_20260714_gt_fundos_15m','gt-fundos-15m','ancora-estudos-entry','camadas-de-entry','A1-A2-B-Cpanic-Cgrind','raw-only-hd-15m','user-approved','otica-renovada'],
  'my-strategy/research/revalidation/{fundos_gt_unify.py,fundos_gt_subdiscriminate.py,fundos_regime_context_audit.py,results/REGIME_GT_FUNDOS_UNIFIED_20260714.json} · commits 17d3df1/a19abdb',
  'active'
)
on conflict (id) do nothing;
commit;
