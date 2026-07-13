-- ============================================================================
-- SUPABASE MEMORY — DELTA SEED · seed:memory_delta_20260713_layer1_macro_structural
-- ============================================================================
-- Sessao 2026-07-13: Layer1 MACRO detector 1D — redesenho estrutural (CHoCH) aprovado por Cris.
-- Aplicar via scripts/supabase/apply_memory_delta.py (autorizado Cris no fecho: "ATUALIZA SUPABASE").
-- Idempotente. Total: 2 rows.
-- ============================================================================
begin;
insert into memory_items (id, scope, visibility, category, title, body, tags, source_ref, status) values
(
  md5('seed:memory_delta_20260713_layer1_macro_structural:memory_items:turn-engine')::uuid,
  'product', 'internal', 'project',
  'Layer1 MACRO detector 1D — motor CHoCH estrutural v3: TURNOS RESOLVIDOS; RANGE em aberto',
  'Layer1 = regime que CONTEM legs (BULL/BEAR/RANGE em 1D, causal close-only, RAW-nativo raw_1d_ohlc.jsonl + DXY). Redesenho aprovado por Cris 2026-07-13: ESTRUTURA-cronometra / CONFLUENCIA-filtra. CAUSA-RAIZ do whack-a-mole anterior (macro_confluence_v2, superseded) = regime por NIVEL (SMA200/drawdown/dolar) em FSM pegajoso => toda virada atrasa => cada onset-patch (bear_rollover/bull_recovery) tem limiar que corrige um turno e erra a vizinha (os 2+2 pontos que o Cris anotou eram residuos dos meus tampoes). FIX estrutural: (1) TIMING = CHoCH geometrico sobre o pivo IMEDIATO protegido — higher-low do pullback antes do topo em BULL, lower-high em BEAR; dispara NA barra do rompimento, sem lag. (2) SIGNIFICANCIA = confluencia como PORTEIRO nao gatilho: bear-gate = crash|dd>=8|dolar-a-subir; bull-gate = dolar-a-cair|runup>=10; CHoCH sem gate = pullback interno MANTEM tendencia. (3) CRASH 2d<=-6pct = override BEAR imediato. RESULTADO (m=5,W_rng=150,band=13): bears 5/5 · onset 2020=+2 2022=-1 2023=+8 2024=+2 2026=-2 (todas as viradas no lugar; holdout antigo 2020 era 190d) · 2026 held 100pct · false-bull-in-bear 49.6(v2)->16 · range-in-bull ~0-7. Os 2 pontos anotados (topo 2026=BEAR imediato, fundo out/2022=BULL imediato) corrigidos por GEOMETRIA, zero tampao de threshold. Scorer AUDITADO layer1_audit_metrics — o coherence_score composto e GAMEAVEL por range-tudo (config degenerada marcou 75), NAO coroar composto, ler o VETOR completo. GT congelado results/REGIME_GT_LAYER1_CRIS_1D_20260713.json (16 janelas: 6 BULL/5 BEAR/5 RANGE, 2 nested 2024, bordas +-5d, sha 3132690cfafee7e8).',
  array['seed:memory_delta_20260713_layer1_macro_structural','layer1','macro','choch','estrutura-cronometra','turnos-resolvidos','audit-vetor-nao-composto'],
  'my-strategy/research/revalidation/macro_structural_v3.py · layer1_audit_metrics.py · results/REGIME_GT_LAYER1_CRIS_1D_20260713.json · commit 06a328f (pushed) · memory project_layer1_macro_detector.md',
  'active'
),
(
  md5('seed:memory_delta_20260713_layer1_macro_structural:memory_items:range-open')::uuid,
  'product', 'internal', 'project',
  'Fecho sessao 2026-07-13: Layer1 turnos selados, RANGE = sub-problema estrutural EM ABERTO (retomar)',
  'PENDENTE (Cris desligou o sistema · retomar): ramo RANGE do Layer1. Deteccao de range por CONTENCAO-Donchian (largura relativa <= band ao longo de W_rng dias) BRIGA com o motor de turnos = dial ZERO-SOMA medido no audit: banda larga (band=13/W=90) apanha range (recall 64pct) MAS come pernas bull (range-in-bull 41pct) e SUPRIME os onsets de bear (2022->143d, 2023 falha, bears 4/5); banda apertada preserva turnos mas range recall 0. Conclusao: contencao e a ferramenta ERRADA (threshold que briga com estrutura) — NAO continuar a afinar band_rng (e o whack-a-mole que o Cris mandou parar). RANGE certo = ESTRUTURAL tambem (entre-tendencias: CHoCH sem BOS de confirmacao em nenhum lado) => precisa de 2a ESCALA DE SWING propria. Ao retomar: (1) desenhar RANGE estrutural sem partir os turnos; (2) plotar versao final p/ Cris verificar (remove blocos solidos meus, mantem rgba dele; template plot_macro_confluence_v2.py; pausa /tmp/claude_recheck.paused OBRIGATORIA; SEM screenshot — Cris faz o visual). Depois: Layer2 = leg v2 sob Layer1; SHORT so dispara em macro-BEAR. Nada de producao tocado na sessao. Commits desta sessao: c0cb978 (v2 refine, superseded) · 06a328f (motor estrutural v3, pushed).',
  array['seed:memory_delta_20260713_layer1_macro_structural','fecho-20260713','range-em-aberto','zero-soma-contencao-vs-turnos','2a-escala-swing','retomar'],
  'my-strategy/research/revalidation/macro_structural_v3.py · git log c0cb978..06a328f',
  'active'
)
on conflict (id) do nothing;
commit;
