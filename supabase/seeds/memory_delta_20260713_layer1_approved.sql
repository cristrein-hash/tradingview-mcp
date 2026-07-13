-- ============================================================================
-- SUPABASE MEMORY — DELTA SEED · seed:memory_delta_20260713_layer1_approved
-- ============================================================================
-- Sessao 2026-07-13 (3o bloco): Layer1 macro COMPLETO integrado + fix bear-flag = USER_APPROVED.
-- Aplicar via scripts/supabase/apply_memory_delta.py. Idempotente. Total: 1 row.
-- ============================================================================
begin;
insert into memory_items (id, scope, visibility, category, title, body, tags, source_ref, status) values
(
  md5('seed:memory_delta_20260713_layer1_approved:memory_items:layer1-approved')::uuid,
  'product', 'internal', 'project',
  'Layer1 MACRO detector COMPLETO (turnos CHoCH + RANGE SYNTH + fix bear-flag) = USER_APPROVED (nao producao)',
  'Cris APROVADISSIMO ("melhor leitura estrutural que fizemos ate agora"). macro_structural_v3.build_layer1() = detetor UNICO Layer1 (BULL/BEAR/RANGE em XAU 1D, causal close-only, RAW-only). Integra o motor de turnos CHoCH (escala imediata m=5) + ramo RANGE SYNTH do engine multi-agente (falha-de-progressao da 2a escala swing m=13 + gate posicao-na-banda + RSI mid-band; recall 93pct) e reproduz byte-a-byte o harness+SYNTH. Cris levantou 1 ponto na plotagem (2026-02: bear flag rotulado BULL); implementadas 2 correcoes ESTRUTURAIS causais que Cris nomeou como "maturidade estrutural": (1) reversao BEAR->BULL exige reconquistar o lower-high da 2a ESCALA DE SWING (nao o mini-high imediato) => bear flag nao vira bull; (2) gate de MATURIDADE (min_bear_age=8 barras) => bloqueia o ressalto logo apos crash. Efeito no caso 2026-02: era BULL 41d, agora BEAR 5d + RANGE 40d. VERIFICACAO: onsets dos 5 bears BYTE-IDENTICOS ao baseline (nenhum degradou), bears 5/5, 2026 held 99pct, RANGE recall 93pct, false-bear-in-range 3.4, range-in-bull 25.6 (TODOS inalterados), FBull_bear 12.4->0.4 (o fix apanhou tambem outros flags, nao so 2026). BULLrec 73->74, BEARrec 53->63. plot_macro_layer1.py plota o integrado; Cris conferiu visualmente e aprovou. STATUS = research/USER_APPROVED, NAO producao (sem runtime/Telegram/broker). Fonte RAW-only auditada PASS na sessao. PENDENTE: Layer2 (campo leg sob Layer1); SHORT so dispara em macro-BEAR (nunca espelho). Commits: 06a328f (turnos) -> 293b7e5 (engine RANGE) -> b4d6b88 (Layer1 completo + fix, pushed).',
  array['seed:memory_delta_20260713_layer1_approved','layer1','user-approved','nao-producao','choch','range-synth','fix-bear-flag','maturidade-estrutural','onsets-byte-identicos'],
  'my-strategy/research/revalidation/{macro_structural_v3.py::build_layer1,plot_macro_layer1.py,range_lab_harness.py,range_cand_SYNTH.py} · commit b4d6b88 · memory project_layer1_macro_detector.md',
  'active'
)
on conflict (id) do nothing;
commit;
