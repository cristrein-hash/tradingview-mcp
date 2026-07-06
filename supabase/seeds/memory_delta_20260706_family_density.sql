-- ============================================================================
-- SUPABASE MEMORY — DELTA SEED · seed:memory_delta_20260706_family_density
-- ============================================================================
-- Bloco: passo 3 recall-first (mapa features por familia + seletores) (2026-07-06).
-- APLICACAO: autonoma via scripts/supabase/apply_memory_delta.py.
-- ROLLBACK: delete from memory_items where tags @> array['seed:memory_delta_20260706_family_density'];
-- Total: 1 row.
-- ============================================================================
begin;

insert into memory_items (id, scope, visibility, category, title, body, tags, source_ref, status) values
(
  md5('seed:memory_delta_20260706_family_density:memory_items:passo3-teto-densidade')::uuid,
  'product', 'internal', 'project',
  'Passo 3 recall-first: mapa por familia + seletores = TETO DE DENSIDADE 28-108:1',
  'Mapa winner-de-circulo vs sosia por familia estrutural (BANDA 34c / RASO 13c / FUNDO 12c). DA5: familias descritivamente distintas MAS a manchete (h1_trend flip RASO=+1 vs BANDA/FUNDO=-1) e ARTEFATO da propria definicao de familia (retracao rasa => uptrend; winner ~= sosia dentro da familia, MWU p=0,6-0,76 ns). Binarias sep=1,0 (killzone/in_demand/confluence) degeneradas (IQR~0). UNICO sinal winner-vs-sosia REAL: sell_bub_w em FUNDO (17 vs 5, p=0,0025) + h4n_dist_demand_atr em BANDA/RASO (p<0,0001/0,012) = FLUXO(absorcao venda) e HTF(dist demanda 4H), nao snapshot 15M. Seletores por familia: nenhum vira estrategia — RASO null-cand 0,04 morre em null-episodio 0,40 (autocorrelacao intra-episodio), 2025-loaded (+102,5 de +104,3; 2024 21%<base 30%); streak P(>5)=1,0 nas tres = FN-inviavel. RAZAO-RAIZ MEDIDA (6o caminho ao mesmo teto): densidade sosia:winner 28:1 BANDA / 29:1 FUNDO / 108:1 RASO; fundos verdadeiros = 0,9-3,4% de qualquer contexto => teto precisao ~1-3%. Oracle prova que a entrada EXISTE (+169R, 58/58); bloqueio = 100% discriminacao sob densidade. Fios vivos: (1) FLUXO/ABSORCAO sequencial (sell_bub_w) nunca construido como discriminador dedicado; (2) re-entry INTRA-episodio de fundo (oracle 1o-crono +96R/69% vs total +169R).',
  array['seed:memory_delta_20260706_family_density','recall-first','densidade','teto','fluxo-absorcao'],
  'family_feature_map_20260706.py + family_selector_test_20260706.py + _da5_family_audit.py (commit 5448538)',
  'active'
)
on conflict (id) do nothing;

commit;
