-- ============================================================================
-- SUPABASE MEMORY — DELTA SEED · seed:memory_delta_20260712_regime_detector_session
-- ============================================================================
-- Bloco: sessão 2026-07-12 de verificação/afinação do regime detector 4H.
-- Aplicar via scripts/supabase/apply_memory_delta.py (autorizado Cris 2026-07-12).
-- Zero RAW/candles/secrets. Idempotente (on conflict do nothing). Total: 4 rows.
-- ============================================================================
begin;
insert into memory_items (id, scope, visibility, category, title, body, tags, source_ref, status) values
(
  md5('seed:memory_delta_20260712_regime_detector_session:memory_items:causal-fix')::uuid,
  'product', 'internal', 'project',
  'Regime detector 4H-nativo: vazamento causal em ovr_at CORRIGIDO (barra em formacao) · gates L1/L2 byte-identicos · DA 6/6',
  'Leak real encontrado por inspecao (familia apontada por auditoria externa): t do RAW = ABERTURA da barra e ovr_at selecionava a barra 1H/4H QUE CONTEM t (em formacao), usando o close dela (ate 1h/4h no futuro). Fix: ultima barra FECHADA <= t (bisect por ts-dur), commit 67bb7ef. Re-medicao: TODOS os paineis de gate L1-34/L1-26/L2-276 byte-identicos (so 1 barra amostral muda na distribuicao) · artifact l1_FINAL_regime_gated.json inalterado · a validacao indireta L1/L2 sobrevive. DA lookahead-only 6/6 CAUSAL_OK pos-fix (incl. regime_prevday_close barra 23:00 agora excluida, conservador). Licao: delta zero = sorte de amostra, nao imunidade · o fix estava certo independente do delta. Acusacao de repaint REFUTADA: maquina de estados forward-only, rotulos nunca reescritos (caixas do plot = cosmetica hindsight de PRECO, nao de tempo).',
  array['seed:memory_delta_20260712_regime_detector_session','regime-4h','causal-fix-ovr-at','gates-intactos','repaint-refutado'],
  'my-strategy/research/revalidation/engine_4h_regime_gate_RAW.py · commit 67bb7ef',
  'active'
),
(
  md5('seed:memory_delta_20260712_regime_detector_session:memory_items:gt-frozen-baseline')::uuid,
  'product', 'internal', 'project',
  'GT de regime 4H congelado (19 janelas Cris, sha be4a9d6f) · baseline vs GT: bal 64,1 OOF / 73,4 cego · 4 modos de erro mapeados',
  'GT = REGIME_GT_CRIS_4H_20260712.json: 19 janelas coloridas desenhadas pelo Cris no chart 4H (lidas via MCP), bordas APROXIMADAS com tolerancia +-3d excluida do scoring, CONFUSO descartado (redundante), metrica intrinseca NUNCA P&L. Baseline (K5/K5/dd6) vs GT: acc 66,5 bal 64,1 · recall B/Be/R 68,6/70,7/53,1. Modos de erro: (1) RANGE nas pernas internas de estruturas direcionais, (2) lag em viradas V (pos-COVID 6,9 pct), (3) BEAR curto perdido (nov/2024 0 pct, janela de 6 barras 1D), (4) instabilidade na zona 2021-22 (35,8 pct). Churn: range 1,07 vs trend 0,95/100b = detector fatia a mesma cadencia sempre. Hibrido com rotulos do Cris (hindsight, teto): L1 impacto ZERO · L2 +54R de premio disponivel. Exposicao janela range 2021-22: L1 2/24 · L2 56/276.',
  array['seed:memory_delta_20260712_regime_detector_session','gt-19-janelas','baseline-64-73','modos-de-erro','premio-l2-54r'],
  'my-strategy/research/revalidation/results/REGIME_GT_CRIS_4H_20260712.json · reports/REGIME_DETECTOR_TUNING_SESSION_20260712.md',
  'active'
),
(
  md5('seed:memory_delta_20260712_regime_detector_session:memory_items:six-mechanisms-refuted')::uuid,
  'product', 'internal', 'feedback',
  'SEIS mecanismos de afinacao do regime 4H REPROVADOS (~200 variantes causais) · baseline = otimo local real · sonda-antes-de-rodar = padrao obrigatorio',
  'Todos causais, DA-limpos, contra GT congelado, P&L fora: (1) contencao ER-120 acima do detector: saldo -16 a -43pp em TODA a grelha, ARQUIVADA por triagem barata sem coletar historico longo. (2) Dial dd x K_in x K_out: soma-zero (compra recall direcional vendendo RANGE), nada bate baseline. (3) Pivots fractais micro: ESCALA ERRADA (129 pivots dentro de janela com ~8 swings a olho — licao: verificar escala da medicao vs escala do GT ANTES de rodar). (4) Pivots macro zigzag: melhor cego 56,2 vs barra 73,4. (5) Quatro familias ortogonais multi-agente (leg_geometry, congestion_revisit, extreme_cadence, mtf_1d_pattern) + combinador congelado: melhor combo cego 66,3. (6) Hierarquico (baseline decide RANGE, mtf da direcao): reprovado por criterio congelado 3-partes do Cris (OOF 62,6 < 64,1 · nov/24 0 pct — estrutural: base-RANGE cala o mtf). K-fold purged/embargoed r2 (purge por janela GT): C_V voto media 67,5+-8,7 vs baseline 66,0+-13,1 MAS OOF 60,9 < 64,1 (ganha direcao, perde RANGE 31 vs 53). LICOES PERMANENTES: (a) episodios n=1 nao se atacam com mecanismos globais (imposto em 6700 barras por 60), (b) SONDA de separacao de distribuicoes ANTES de cada corrida (matou o precision-override de graca: nov/24 n=6, sep EMA sobreposta aos ranges, sinal troca dentro da janela), (c) arbitro com 19 janelas nao tem poder para ganhos de 2-4pp.',
  array['seed:memory_delta_20260712_regime_detector_session','seis-mecanismos-reprovados','baseline-otimo-local','sonda-antes-de-rodar','episodios-n1'],
  'my-strategy/research/revalidation/reports/REGIME_DETECTOR_TUNING_SESSION_20260712.md · gt_kfold_eval_r2.py · probe_ema_sep_nov24_vs_range.py · commit f4b19a3',
  'active'
),
(
  md5('seed:memory_delta_20260712_regime_detector_session:memory_items:case-exogenous-plan')::uuid,
  'product', 'internal', 'project',
  'PLANO APROVADO (Cris 2026-07-12): afinacao do regime 4H CASO A CASO + contexto EXOGENO (DXY/yields) · estruturais viram diagnostico',
  'Mudanca de angulo decidida pelo Cris: de mecanismos globais para CASO A CASO. FASE 0 (dados existentes): fichas dos 7 casos = janelas com concordancia <60 pct (V-turn 6,9 · nov/24 0 · range21-22 35,8 · bull-abr-jun21 39,1 · bull-fev-abr22 53,8 · bear-gigante-bordas 59,7 · bear-jun-ago21 58,6). FASE 1 (aguarda autorizacao de chart): coletar DXY+US10Y diario ideal 2012+ via MCP paginacao · sonda de separacao POR CASO antes de qualquer regra (sem separacao = caso morre na sonda). FASE 2: regras de caso pre-registadas uma a uma · aceitacao congelada: resolve >50 pct do caso E dano <=0 nas outras 18 janelas E racional causal fisico · entram como EXCECAO/REVIEW-LAYER com watch forward (nunca refit global) · DA por regra · honestidade: n=1 por caso, validacao real so com forward ou GT longo. FASE 3: baseline manda + excecoes estreitas · tabela 19 janelas antes/depois · k-fold r2 como nao-regressao · plot canonico para visual. Features estruturais NAO estao erradas (Cris): viram ferramenta de diagnostico por caso + confirmacao estreita (mtf_1d acertou nov/24 a 100 pct como referencia). Alavanca opcional: Cris marcar GT 2012-2019 no diario (1D nativo ja extraido, raw_1d_ohlc.jsonl 2012-2026) para triplicar episodios. 1H nativo so 2024+ (declarado).',
  array['seed:memory_delta_20260712_regime_detector_session','plano-caso-a-caso','exogenas-dxy-yields','estruturais-diagnostico','gt-2012-2019-opcional'],
  'my-strategy/research/revalidation/reports/REGIME_DETECTOR_TUNING_SESSION_20260712.md secao 7 · raw_1d_ohlc.jsonl',
  'active'
)
on conflict (id) do nothing;
commit;
