-- ============================================================================
-- SUPABASE MEMORY — DELTA SEED · seed:memory_delta_20260712_leg_field_exog
-- ============================================================================
-- Bloco 2 da sessão 2026-07-12: exógenas + casos + campo leg (fecho pré-desligamento).
-- Aplicar via scripts/supabase/apply_memory_delta.py (autorizado Cris no fecho).
-- Idempotente. Total: 3 rows.
-- ============================================================================
begin;
insert into memory_items (id, scope, visibility, category, title, body, tags, source_ref, status) values
(
  md5('seed:memory_delta_20260712_leg_field_exog:memory_items:exog-cases')::uuid,
  'product', 'internal', 'project',
  'Exogenas coletadas (DXY 1974-2026, US10Y 2003-2026, RAW no HD) · sonda separa 4/7 casos · regra C2 nov/24 REJEITADA 2x pelo criterio dano-zero',
  'Coleta via MCP paginacao (chart posicionado pelo Cris · backfill programatico NAO dispara, precisa scroll manual): DXY 12974 barras 1974-2026 e US10Y 5216 barras 2003-2026, gzip+sha256+roundtrip+manifest em raw_external/ no HD GUTS LACIE, caches locais no repo. SONDA exogena por caso (features causais dxy_ret20/dxy_slope/y_chg20/y_slope · veredicto congelado overlap<10pct=SEPARA): C2 nov/24 SEPARA x3 (dxy_ret20 2,2pct!) · C4 x2 · C1 V-turn x2 · C5 x1 · C3 range21-22 NAO separa (morre na sonda) · C6/C7 parciais. REGRA C2 (dolar rally + yields subindo + ouro caindo, D_KNOWN causal, DA 5/5): resolve o caso a 100pct nos 4 combos MAS viola dano-zero -> REJEITADA r1 (spillover no range adjacente + guerra fev/22) e r2 com cap de onset (elimina dano da guerra · resta range adjacente por RE-ONSETS · REJEITADA 6/6). Licao: choque (8d) != condicao rolling (20d) · e as janelas GT BEAR-nov24/RANGE-nov17 SOBREPOEM-SE (dano-zero na fronteira pode ser inatingivel por construcao). Revisao visual com Cris: nov/24-jan/25 = pullback bear DENTRO de bull + acumulacao (estrutura hierarquica unica) · detector desfasado uma perna (rotula queda como range e repique como bear, histerese K=5).',
  array['seed:memory_delta_20260712_leg_field_exog','exogenas-coletadas','sonda-separa-4-7','c2-rejeitada-2x','choque-vs-condicao','janelas-sobrepostas'],
  'my-strategy/research/revalidation/{collect_exog_daily.py,exog_context_probe.py,case_c2_nov24_rule.py,case_c2_nov24_rule_r2.py} · reports/CASE_C2_NOV24_EXOG_PREREG{,_R2_ONSET}.md · commits 634c90a..a74079c',
  'active'
),
(
  md5('seed:memory_delta_20260712_leg_field_exog:memory_items:leg-field')::uuid,
  'product', 'internal', 'project',
  'CAMPO leg (Opcao A) implementado v1->v2 — leitura hierarquica paralela ao macro intocado · STATUS Cris: MELHOROU MAS NAO RESOLVEU',
  'Decisao Cris: corrigir a leitura hierarquica sem tocar no detector (macro byte-intocado, zero risco as deteccoes corretas). leg_state_4h.py: pivots zigzag R=6 auditados -> leg IMPULSO_UP/PULLBACK_BEAR/IMPULSO_DOWN/PULLBACK_BULL/ACUMULACAO/DISTRIBUICAO + leg_age. v1 leu certo nov/24 (PULLBACK_BEAR cobrindo a janela que o macro perdia) e as pernas bull internas do bear gigante, MAS: cego em impulso (rally ago-out/25 = 318 barras ACUM, zigzag sem pivots sem retracao 6ATR), memoria de 2 pares de pivots perdia contexto macro (IMPULSO_UP 157b dentro do bear 2026), ACUM cega ao macro. v2 = 4 correcoes do Cris: C1 estrutura por QUEBRA DE NIVEL causal (close alem do ultimo pivot = evento imediato — cegueira em impulso RESOLVIDA: rally 25 -> 200 IMPULSO_UP) · C2 ancora macro (evento contra-macro exige dupla) · C3 ACUMULACAO/DISTRIBUICAO pelo macro · C4 plot 2 camadas (preenchimento=leg, borda=macro modal; 135 blocos). DA 6/6 CAUSAL_OK zero repaint (v1 e v2). RESIDUAL DECLARADO: fev/26 topo final le IMPULSO_UP (preco ainda subia · GT do Cris marca BEAR do topo — convencao macro dele) + barras onde o proprio macro diz BULL/RANGE (leg herda erro do macro por design). VEREDICTO CRIS AO FECHO: melhorou mas nao resolveu · AINDA NECESSITA AJUSTES (proxima sessao).',
  array['seed:memory_delta_20260712_leg_field_exog','campo-leg-v2','opcao-a-macro-intocado','quebra-de-nivel-causal','melhorou-nao-resolveu'],
  'my-strategy/research/revalidation/{leg_state_4h.py,case_context_leg_eval.py,replot_leg_blocks_v2.py} · commits 2c5b8da/47e893c/2422f80',
  'active'
),
(
  md5('seed:memory_delta_20260712_leg_field_exog:memory_items:open-state-fecho2')::uuid,
  'product', 'internal', 'project',
  'Fecho 2 da sessao 2026-07-12: pendencias do campo leg e trilhas abertas do regime 4H',
  'PENDENTE (Cris desligou o sistema · retomar): ajustes do campo leg v2 — residuais conhecidos: (a) topo final fev/26 como IMPULSO_UP (discutir semantica: preco subia vs marcacao BEAR-do-topo do GT) · (b) leg herda barras BULL/RANGE erradas do macro no bear 2026 · (c) range out-nov/25 le pernas direcionais (com borda RANGE no plot 2-camadas pode ser aceitavel — Cris avalia) · (d) possivel afinacao da ancora macro (dupla confirmacao) e da semantica ACUM/DIST. Casos exogenos vivos: C4/C1/C5 separam na sonda e nunca foram rodados como regra · C2 rejeitado 2x (variante onset-unico/refratario possivel, novo prereg) · C3 morto na sonda. GT: opcao declarada de marcar 2012-2019 no diario (1D nativo extraido) para triplicar episodios · e possivel GT v2 dois niveis (macro+leg). Chart: blocos leg v2 plotados (135) + desenhos do Cris preservados. Nada de producao tocado em toda a sessao.',
  array['seed:memory_delta_20260712_leg_field_exog','fecho-2','pendencias-leg','casos-c4-c1-c5-vivos','gt-v2-dois-niveis'],
  'git log 5976e6c..2422f80 · reports/REGIME_DETECTOR_TUNING_SESSION_20260712.md',
  'active'
)
on conflict (id) do nothing;
commit;
