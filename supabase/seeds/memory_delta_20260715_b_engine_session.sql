-- ============================================================================
-- SUPABASE MEMORY — DELTA SEED · seed:memory_delta_20260715_b_engine_session
-- ============================================================================
-- Sessao 2026-07-15: A1/A2 entry fix causal + A2 aprovado; B macro gate aprovado; B engine v1.1 selado.
-- Aplicar via scripts/supabase/apply_memory_delta.py. Idempotente. Total: 3 rows.
-- ============================================================================
begin;
insert into memory_items (id, scope, visibility, category, title, body, tags, source_ref, status) values
(
  md5('seed:memory_delta_20260715_b_engine_session:memory_items:a1a2-causal-lowreal')::uuid,
  'product', 'internal', 'project',
  'A1/A2 ENTRY (XAU 15M LONG): fix lookahead da ancora + SL low-real estrutural + A2 APROVADO (Cris 2026-07-15)',
  'DA lookahead (a1a2_lookahead_da.py) apanhou que a ancora do SL usava janela [j-16, j+8] = espreitava 8 barras a frente (inflava ~1 win). Corrigido para ancora = swing-low fractal CAUSAL confirmado (a1_causal_entry.py, m=3, tudo <= barra decisao), zero lookahead. Numeros honestos causais: A1 MB3 11/14, A2 14/18, e MB3 ~= reclaim (o "MB3 domina" era artefato do lookahead). DEPOIS, SL ESTRUTURAL low-real APROVADO: diagnostico (a1a2_loser_diagnosis.py) provou 7/7 losers recuperavam ao 3R IGNORANDO o SL = regiao certa, SL raso varrido; o fractal m=3 ancorava num swing-low prematuro. Fix = SL ancorado ao LOW REAL do pullback (menor low ate a entrada -0.1ATR), causal. Painel selado: A1 MB3 13/14 (RCL 11/14), A2 MB3 16/18 (RCL 15/18) -> MB3 >= reclaim. HONESTO: melhoria +2 cada mas NAO gratis (SL fundo R^->alvo^ partiu A2#6 WIN->LOSS; probe previa 17/18, sealed=16/18; winners-curse leve no parametro SL). A2 APROVADO com MESMO entry de A1 (engine nao achou edge distinto; buy-the-dip). Coletor a1_forward_score.py usa causal_entry (herda SL novo). Prereg emendado (lookahead-fix datado, nao move-baliza). Commits 3d63e44/2f829d3. Caveat: N pequeno=desenho, winners curados, forward=arbitro.',
  array['seed:memory_delta_20260715_b_engine_session','a1a2-entry','xau-15m-long','lookahead-fix','sl-low-real','a2-approved','mb3-reclaim-empate','user-approved','forward-arbitro'],
  'my-strategy/research/revalidation/{a1_causal_entry.py,a1a2_lookahead_da.py,a1a2_loser_diagnosis.py,a1_forward_score.py,A1_MB3_ENTRY_PREREG_FORWARD_20260714.md} · commits 3d63e44/2f829d3',
  'active'
),
(
  md5('seed:memory_delta_20260715_b_engine_session:memory_items:b-macro-gate')::uuid,
  'product', 'internal', 'project',
  'B MACRO GATE — subtipo RANGE accum-vs-distrib (crash-born=SKIP) APROVADO in-sample (Cris 2026-07-15)',
  'Gate macro da camada B (LONG em range). ESTUDO DE CASO: accum-vs-distrib NAO e discriminavel no macro de forma geral (range_accum_distrib_test.py, 15 episodios RANGE 2016-2026, base-rate 33pct distrib): predecessor (BULL/BEAR) / dom-swing-break / dd252 = TODOS REFUTADOS (overlap total: 2021 acum dd 14.6pct == 2026 distrib dd 14.6pct). crashPre (crash ret2d <= -6pct, o MESMO limiar do engine, em [onset-15, onset]) = UNICO com precisao 1.00 (dispara 1/15, so 2026, NUNCA skipou uma acumulacao) = seguro ASSIMETRICO (custa oportunidade, nao capital) que apanha o caso catastrofico (2026 -> bear ate hoje). Recall 0.20: distrib-QUIETAS passam por design (geridas por invalidacao apertada + flip macro->BEAR fecha gate). b_macro_gate.py envolve macro_structural_v3.build_layer1 SEM tocar; subtipo fixado no onset (causal). Verificacao: historico 11/15 coincide; nos 15 B do GT KEEP 12 (2025 re-acum) SKIP 3 (B#13-15 = distrib 2026 que virou o bear). Commit b8aaf35. CAVEAT: precisao 1.00 e 1-de-1 (fina); FORWARD = arbitro.',
  array['seed:memory_delta_20260715_b_engine_session','b-macro-gate','xau-15m-long','range-accum-distrib','crashpre','seguro-assimetrico','user-approved','forward-arbitro'],
  'my-strategy/research/revalidation/{b_macro_gate.py,range_accum_distrib_test.py} · commit b8aaf35',
  'active'
),
(
  md5('seed:memory_delta_20260715_b_engine_session:memory_items:b-engine-v1')::uuid,
  'product', 'internal', 'project',
  'ENGINE DE B v1.1 (retomada no FUNDO de range plano) SELADO in-sample N=4 (Cris 2026-07-15)',
  'Camada B (LONG em range) do stack XAU 15M, formato A1/A2. Composicao causal (b_engine_v1.b_signal): (1) gate macro b_macro_gate RANGE_ORDERLY (crash-born=SKIP); (2) banda causal p10 lows / p90 highs do range-so-far (aterra ~[3245-3450] do frame do Cris SEM hardcode); (3) gate POSICAO anchor_low na banda <= 40pct = so a porcao BAIXA (suporte), REJEITA continuacao perto do topo (o streak-killer, licao dura do Cris); (4) gatilho MB3 + SPRING (low varre suporte imediato -0.1ATR e o MB3 reclama acima; testado vs null: spring 45pct vs 39pct baseline, ABSORCAO REJEITADA por piorar 27pct) + SL low-real + 3R. ESTUDO DE CASO: GT B contaminado: 7/12 fundos (B#5-12) estao perto do TOPO do range plano = survivorship dos streak-killers que o Cris rejeita; so B#1-4 sao fundo genuino. 3 erros meus de medicao corrigidos no caminho (lookahead ancora; truncamento de dados que deu posicoes falsas). Frame do range plano = [3245-3450] (niveis do Cris), banda causal p10/p90 reproduz. Painel in-sample seed N=4 (B#1-4, todos springs): MB3+spring 3 WIN 0 LOSS 1 OPEN; gate KEEP 4/12 SKIP B#5-12. CAVEATS HONESTOS: N=4 seed, 1 range, spring modesto +6pp, o GATE DE POSICAO e a contribuicao principal (gatilho NAO provado; null alto B#2/B#3 88-90pct = buy-any-dip ja ganha ai). Vetor de falha declarado: distribuicao QUIETA (gate recall 0.20). Prereg B_ENGINE_V1_PREREG_FORWARD_20260715.md congelado (PASS = N>=20 forward, hit-3R>=45pct, streak<=5, bate null, exp>0). Coletor b_forward_score.py. Commit 4ed88f8. Forward=arbitro. PROXIMO: coletar forward + camadas Cp (capitulacao) / Cg (fundo-profundo).',
  array['seed:memory_delta_20260715_b_engine_session','b-engine-v1','xau-15m-long','range-plano-fundo','gate-posicao','mb3-spring','streak-killer-avoid','n4-seed','user-approved','forward-arbitro'],
  'my-strategy/research/revalidation/{b_engine_v1.py,b_trigger_refine.py,b_forward_score.py,B_ENGINE_V1_PREREG_FORWARD_20260715.md} · commit 4ed88f8',
  'active'
)
on conflict (id) do nothing;
commit;
