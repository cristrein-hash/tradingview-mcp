-- ============================================================================
-- SUPABASE MEMORY — DELTA SEED · seed:memory_delta_20260705_inband_round1
-- ============================================================================
-- Bloco: discriminacao em-banda rodada 1 (2026-07-05 noite).
-- APLICACAO: autonoma via scripts/supabase/apply_memory_delta.py.
-- ROLLBACK: delete from memory_items where tags @> array['seed:memory_delta_20260705_inband_round1'];
-- Total: 1 row.
-- ============================================================================
begin;

insert into memory_items (id, scope, visibility, category, title, body, tags, source_ref, status) values
(
  md5('seed:memory_delta_20260705_inband_round1:memory_items:inband-round1-negativo-bug')::uuid,
  'product', 'internal', 'project',
  'Discriminacao em-banda rodada 1 = NEGATIVO com bug de calculo identificado (flush-bar)',
  'Alvo ordenado: separar fundo-genuino de sosia DENTRO da banda retr 0,5-1,3 (N1421, hit 26,2% = base). Exaustao na janela do reclaim = DEGENERADA (cj ~3 barras pos-flush). Familia ondas-do-pullback (n_waves 4v3, bottom_time 0,16v0,29, vol_dryup 0,85v0,94): D1 N202 34,2% +49,2 MORTO pelo DA3 — 100% do efeito em 2025 (fora-2025: 26,4%, NET -8,2), Bonferroni 0,087-0,20, null por episodio p=0,029, streak q50=10 = FN-inviavel; D3 GT-precisao 23% = artefato de circulo duplicado. BUG SEMANTICO (correcao seguinte declarada): fi localizada por preco de tras p/ frente pega o RETEST nao o flush (mismatch vs argmin 46-86%; em 41-79% o low real da janela esta ABAIXO do flush_low do candidato). Proximo: refazer W-features com fi=argmin low em [h1i..ci] + feature posicao-do-flush-vs-low-verdadeiro; gargalo GT-60 permanece. Licoes DA3: seeds de null fixas (hash salted nao reproduz); GT-precisao por circulo distinto; sub-janela anual antes de headline.',
  array['seed:memory_delta_20260705_inband_round1','layer-2','em-banda','negativo','method-lesson'],
  'inband_{exhaustion_discriminator,wave_structure,composite_needle}_20260705.py + inband_audit_da3_full.py (commit e3a28e8)',
  'active'
)
on conflict (id) do nothing;

commit;
