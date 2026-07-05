-- ============================================================================
-- SUPABASE MEMORY — DELTA SEED · seed:memory_delta_20260705
-- ============================================================================
-- Bloco: sessoes 2026-07-04 (pos RAW-extension) + 2026-07-05 (GT-60, CASCEX,
--   Layer 2, RWS hardening, rodada macro-estrutural).
-- APLICACAO: autorizada pelo Cris em 2026-07-05 ("sobe pro Supabase tudo").
-- IDEMPOTENTE: md5(seed_key)::uuid + on conflict (id) do nothing. Re-executavel.
-- CONTEUDO: zero RAW/candles, zero secrets. Titulos/resumos/pointers.
-- ROLLBACK: delete from memory_items where tags @> array['seed:memory_delta_20260705'];
-- Total: 16 rows memory_items.
-- ============================================================================
begin;

insert into memory_items (id, scope, visibility, category, title, body, tags, source_ref, status) values
(
  md5('seed:memory_delta_20260705:memory_items:mtf-signature-gate-fail')::uuid,
  'product', 'internal', 'project',
  'MTF-Signature Gate = FAIL/REFUTADA — assinatura das 35 manuais era fill-fiction',
  'Assinatura ceu-limpo-15M + demanda-1H (lift 5,7-6,7x) das 35 ops manuais era artefato de preco-ancora retroativo ~3,3 ATR abaixo do mercado, que inflava as duas pernas. No preco real do mesmo instante: 6% ~= controles 8%; gate real: retencao 1,9%, runner-kill 52/53. LICAO DE METODO PERMANENTE: alvos de hindsight-target DEVEM ser reprecificados ao close real antes de qualquer lift; lentes preco-dependentes herdam artefato; null de rotulos NAO captura defeito de preco.',
  array['seed:memory_delta_20260705','mtf-gate','refutada','fill-fiction','method-lesson'],
  'memory/project_xau_15m_swept_runner_signal.md (delta 2026-07-04)',
  'active'
),
(
  md5('seed:memory_delta_20260705:memory_items:lab-b-r2-risk-control-only')::uuid,
  'product', 'internal', 'project',
  'Lab B r2 = RISK_CONTROL_ONLY — FB1 anti-veto-teto canon negativo, FB2 SIZE_50',
  'CANON NEGATIVO FB1: teto/supply convergente carrega PREMIO na base (runners no meio-alto/teto; SKIP por teto = taxar pagadores; 4 buscas independentes + DA). Losers reais = FUNDO/early-leg: FB2 (legpos60<=0,25 & h1_pos<=0,61 -> SIZE_50 via F4) +236,6R/101,3%/53 runners, MAS 2026 contradiz (+4,4) = calibracao. Medido: 57% do max-DD dentro da classe protegida -> DD/streak inatacaveis por contexto ex-ante. Forward-ledger congelado.',
  array['seed:memory_delta_20260705','lab-b','risk-control','anti-veto-teto'],
  'memory/project_xau_15m_swept_runner_signal.md (delta 2026-07-04)',
  'active'
),
(
  md5('seed:memory_delta_20260705:memory_items:reclaim-quieto-kill-cris35-mercado')::uuid,
  'product', 'internal', 'project',
  'RECLAIM-QUIETO v1.0 = KILL · CRIS35 a mercado = percentil 100/100 vs nulls',
  'Entry independente de 6 lentes (pullback envelhecido + higher-low + CHoCH + dip quieto 30M + retrace + reclaim EMA21) lido one-shot: NET +6/157, stk -11, nulls 51-57%, ablacao melhora removendo qualquer lente = KILL. LICAO CORRIGIDA (Cris desafiou e provou): o que morreu foi a reconstrucao de 6 lentes, NAO as entradas dele — CRIS35 a mercado (close real, SL desenhado, alvo fixo 3R): +68,5 NET, WR 85,7, DD -2,0, r/DD 34 = percentil 100/100 vs nulls uniforme E time-matched (+42R/+31pp sobre o regime). Caveat: set desenhado vendo o grafico; arbitro prospectivo = ~15 trades live.',
  array['seed:memory_delta_20260705','reclaim-quieto','kill','cris35','selecao-real'],
  'research/xau_15m_bb_nas_leonardo/entry_exit_cross_20260704.py · memory delta 2026-07-04',
  'active'
),
(
  md5('seed:memory_delta_20260705:memory_items:exit-family-lab-tradeoff')::uuid,
  'product', 'internal', 'project',
  'EXIT FAMILY LAB = EXIT_VARIANT_MATERIAL_TRADEOFF — exit e dial convexidade x streak',
  'Trail-so-pos-3R na BASE435: +316,7 vs +234,3 (delta +82,3, IC exclui 0 full-sample) MAS falha gates proprios (concentracao 38%>35, 2024 negativo, IC cruza 0 sem 2025-01) e piora FN (WR 38,4, stk q95 19, pior mes -11,2). E2 alvo-3R no Sistema A: +47,1 (delta +21,2, IC positivo, anos+, stk q95 8) mas N53. Winner-curse declarado (melhor-de-4). Exit = DIAL, nao erro; adocao = Cris; arbitro limpo = deltas re-medidos em dados virgens. Decisao Cris: exit FIXO 3R (Programa 3R).',
  array['seed:memory_delta_20260705','exit-family','tradeoff','programa-3r'],
  'memory delta 2026-07-04 · entry_exit_cross_20260704.py',
  'active'
),
(
  md5('seed:memory_delta_20260705:memory_items:programa-3r-fundacao-bearpb-v3f')::uuid,
  'product', 'internal', 'project',
  'PROGRAMA 3R — fundacao computada · Sistema A 49,1% melhor semente · BEARPB_V3F congelada',
  'Mandato Cris: exit fixo 3R; otimizar entradas+cortes. Universo hit-3R: BULL 29,6% / RANGE 26,8% / BEAR 24,8%; breakeven 25%; BASE435 38,2%; SISTEMA A 49,1% = melhor semente. Frente 1 (cortes no A@3R): SEM corte material. Frente 2: BEARPB_V3F congelada (73 sinais, sha 359328de); pre-checks outcome-blind: cobertura dos 4 do Cris = ACASO (P=27%), freq 2,60/sem viola mandato 2,6x -> PRE-CONDICAO 0: Cris decide escopo ANTES da leitura R3 one-shot.',
  array['seed:memory_delta_20260705','programa-3r','sistema-a','bearpb-v3f'],
  'memory delta 2026-07-04',
  'active'
),
(
  md5('seed:memory_delta_20260705:memory_items:expansao-funil-a-negativo')::uuid,
  'product', 'internal', 'project',
  'Expansao funil Sistema A = CONFIRMA_NEGATIVO — otimo local estreito a 0,48/sem',
  '6 eixos univariados pre-declarados, regra congelada (marginal hit>=49,1% & N>=15): NENHUM aprovado (marginais diluem 31/28/43,6%; X4 estruturalmente vazio — reclaim_ema_bars satura em 3; efetivos 4 looks). Sistema A = otimo local ESTREITO sob relaxamento univariado; multivariado = espaco nao-explorado declarado. Observacao p/ futuro: X5 marginal RANGE N39 hit 43,6% NET +30,8 (acima do breakeven 3R) = sub-populacao candidata a rodada propria.',
  array['seed:memory_delta_20260705','sistema-a','funil','confirma-negativo'],
  'memory delta 2026-07-05',
  'active'
),
(
  md5('seed:memory_delta_20260705:memory_items:diagnostico-sistema-a-monforte')::uuid,
  'product', 'internal', 'project',
  'Diagnostico Sistema A (Cris) CONFIRMADO — entra no topo do range; classe MON+FORTE = 58 fundos',
  'Sistema A entra no TOPO do range (box96 med 0,87; 0/53 no fundo, 41/53 no topo); WR 60% inflado por let-run em pops esticados; ~8 runners genuinos. Arbitro correto = hit-3R limpo. Classe MON+FORTE = 58 fundos genuinos (label FORWARD, nunca feature), 57/58 hit-3R limpo. Perfil (medianas MF vs resto): box96 0,28/0,59 · ema21_dist -0,19/+0,19 · legpos60 0,0/0,39 · sweep_depth 1,27/0,17 · reclaim 2,35/1,36 = pullback profundo a base, abaixo das EMAs, varredura funda, reclaim forte (descricao do Cris; OPOSTO do Sistema A). TETO: convergencia 6/6 da so 10% precisao-MF.',
  array['seed:memory_delta_20260705','sistema-a','diagnostico','mon-forte'],
  'scripts dip3r_design/monforte_signature/monforte_trajectory/deepdip_convergence (commit 4af684c)',
  'active'
),
(
  md5('seed:memory_delta_20260705:memory_items:fase12-htf-teto-confirmado')::uuid,
  'product', 'internal', 'project',
  'FASE 1+2 (perna HTF + indicadores pos-estrutura) vs MON+FORTE = TETO CONFIRMADO',
  'Perna 4H revela fundos MF genuinos em CORRECAO 4H (h4_trend_up MF=0, hh_intact MF=0, retrace 0,53) mas lift fraco (2,4%). Pool estrutural (dip 15M + correcao 4H, N427): hit-3R 25,8% (pior que universo); melhor convergencia pool+3-indicadores = N62 hit 32,3%, prec-MF 11%, 2026 negativo. EXAUSTIVO: 5 familias (momentum/estrutura/trajetoria/perna-HTF/indicadores) TODAS capam ~10-11% precisao-MF e ~32-33% hit-3R. Classe dos 58 NAO identificavel ex-ante com features atuais em nenhum TF. Familias nao cobertas: micro-forma/sequencia, inter-mercado, discricionario.',
  array['seed:memory_delta_20260705','mon-forte','teto','htf'],
  'memory delta 2026-07-05',
  'active'
),
(
  md5('seed:memory_delta_20260705:memory_items:rws-15m-breakthrough')::uuid,
  'product', 'internal', 'project',
  'BREAKTHROUGH RWS-15M — porte do V1.4g-RWS-A6 4H para 15M, primeiro mecanico com perfil FN',
  'Cris insistiu: leitura SEQUENCIAL nao snapshot; replicar engines 4H que funcionaram. Reads sequenciais multi-barra (bubble buy_recent acumulacao, burst recente-vs-antigo, large_buy_win8, RSI-above-MA, anti-RSI-bear-div, NAS). RWS-15M: N54 · hit-3R 44,4% · WR 46,3% · streak -4 · DD -5,1 · 0,49/sem · TODOS anos+ (incl. 2026). NULL: hit P=0,7%, NET P=0,0%, streak 4 vs aleatorio 9,5. ABLACAO: carregador = buy_recent (remover -> 29,3%). Populacao DIFERENTE dos 58 MON+FORTE (pullback-em-uptrend com acumulacao). ~26/ano = mais frequente que V1.4g-4H com perfil igual.',
  array['seed:memory_delta_20260705','rws-15m','breakthrough','sequencial'],
  'research/xau_15m_bb_nas_leonardo/rws_sequence_engine_20260705.py (commit d180cff)',
  'active'
),
(
  md5('seed:memory_delta_20260705:memory_items:frente2-expansao-exaurida')::uuid,
  'product', 'internal', 'project',
  'Frente-2 (expandir N do RWS-15M) = EXAURIDA em 3 abordagens — N nao expande limpo',
  'Mapa exaustivo 4 grupos: SEQ e o UNICO com edge (STR 27,5%, HTF 25,4%, IND 2025-loaded); contextualizar RWS com fundo-estrutural/HTF NAO ajuda (SEQ intersecao STR = vazio; >=2/4 grupos DILUI). Soft-score sequencial enriquecido expande N a custo de streak (score>=2,5: N170 hit 36,5% mas streak 10). Conjuncoes nitidas alternativas = VAZIAS (bubbles esparsos). Price-action denso = sem pocket limpo. CONCLUSAO ROBUSTA: RWS-15M N54 e o edge singular; expansao limpa mantendo streak<=4 = problema aberto (precisa discriminacao sequencial mais afiada).',
  array['seed:memory_delta_20260705','rws-15m','expansao','exaurida'],
  'commits df53833 + 9eb9434',
  'active'
),
(
  md5('seed:memory_delta_20260705:memory_items:rws-hardening-pass-caveats')::uuid,
  'product', 'internal', 'project',
  'HARDENING RWS-15M = PASS_WITH_CAVEATS -> PROMISSOR-NAO-VALIDADO',
  'Config selada (54 sinais, sha b391f7bb); causalidade PROVADA pelo DA (54/54 byte-identicos; variante leaky da 131@33,6% = known_at load-bearing); NET P<0,001 sobrevive multiplicidade (hit marginal P->0,040 sob 5-8 looks); jackknife pior-mes 23%. RESSALVA CENTRAL (DA): streak observado -4 mas DISTRIBUCIONAL q95 = 9-10, P(streak>5) ~0,45-0,50 sob exit 3R -> REPROVA FN<=5; obs-4 foi sorte. Trade-off: let-run WR 57,4 P(stk>5)=0,16 FN-compativel mas -17R e 2026 negativo. 2026 INCONCLUSIVO (dormante desde marco). Promocao condicional exige: mitigacao streak + NAS-known_at + forward.',
  array['seed:memory_delta_20260705','rws-15m','hardening','pass-with-caveats'],
  'docs/architecture/XAU_15M_LONG_RWS_SEQUENCE_ENGINE_HARDENING_20260705.md (commit 0f5cc03)',
  'active'
),
(
  md5('seed:memory_delta_20260705:memory_items:gt-60-selado-recall-estrito')::uuid,
  'product', 'internal', 'feedback',
  'GT-60 selado (circulos do Cris = ground truth) + regra permanente de recall ESTRITO',
  'Apos veredito visual do Cris nos 28 sinais RWS plotados ("vergonhoso — entries altas/tardias, nunca capturam fundos de capitulacao"), Cris marcou circulos no chart = fundos verdadeiros. 61 circulos -> 60 GT unicos selados com sha-check obrigatorio (snap price-anchored +-120b, low mais proximo do preco do circulo). REGRA PERMANENTE: GT capturado apenas se sinal em +-8h E |flush_sinal - flush_GT| <= 1 ATR (janela +-8h solta inflava recall 4x). GT e sempre METRICA/calibracao declarada, NUNCA feature de selecao. Cobertura RWS/BASE435 dos GT = acaso.',
  array['seed:memory_delta_20260705','ground-truth','recall-estrito','method-lesson'],
  'research/xau_15m_bb_nas_leonardo/results/ground_truth_bottoms_20260705.json + .sha256',
  'active'
),
(
  md5('seed:memory_delta_20260705:memory_items:cascex-v01-preaprovada')::uuid,
  'product', 'internal', 'project',
  'CASCATA-EXAUSTA v0.1 (XAU15M_CASCEX) = USER_PREAPPROVED LAYER 1 ENTRY XAU 15M LONG',
  'Pre-aprovada pelo Cris 2026-07-05 ("primeira estrategia realmente mais madura"). Config: cascata SMC>=4 (BOS-/CHoCH- consecutivos, known_at, janela 48h) & h1_rsi<=42 & demanda (in_demand ou dist<=0,5ATR) & reclaim>=1,5 ATR, MENOS veto pernada-macro (vel>=0,10 ATR/barra OU recent_frac>=0,5). Entry=close@cj, SL=flush-0,1ATR, exit fixo 3R. PAINEL: N34 · 55,9% · +39,6R · DD -4,8 · stk -4 · 0,31/sem · todos anos+. Pendencias promocao: streak P(>5)=0,19 · buraco BEAR-envelhecido · prereg + forward. USER_PREAPPROVED != producao.',
  array['seed:memory_delta_20260705','cascex','layer-1','preapproved'],
  'docs/architecture/XAU15M_CASCEX_V01_PREAPPROVAL_20260705.md (commit e4b2b9a)',
  'active'
),
(
  md5('seed:memory_delta_20260705:memory_items:macro-veto-reentry-killed')::uuid,
  'product', 'internal', 'project',
  'Veto pernada-macro = RISK_CONTROL (forma, nao expectancy) · re-entry/skip BEAR = KILLED',
  'Mecanismo nomeado pelo Cris ("losers entram no inicio/meio de pernada macro fortissima") virou familia de features causais (origem = high max 1920 barras: age_h, travel_atr, vel, recent_frac, n_retraces). Vetos M3/M6 melhoram forma (DD/streak) sem mover expectancy = camada de risco. Re-entry v2 (ancora no flush novo) = breakeven; lab de regras R1-R4 KILLED por null de random-timing (null mediana +60,8 > R3 +45,0) — janelas re-entry nao batem timing aleatorio. Ajustes de geometria BEAR-interna: todos falham.',
  array['seed:memory_delta_20260705','macro-leg-veto','risk-control','reentry-killed'],
  'macro_leg_position_veto_20260705.py · reentry_rule_lab_20260705.py',
  'active'
),
(
  md5('seed:memory_delta_20260705:memory_items:layer2-h1up-fdr-gtq-agulha')::uuid,
  'product', 'internal', 'project',
  'Layer 2: primeira lente FDR (h1up P=0,002) + agulha GTQ (GT-precisao 28%, CALIBRACAO)',
  'Sobre base v3 (ctx pre-perna + demanda + reclaim, N1555, 30,3%): h1_trend==1 P=0,0020 FDR (N859 +194,6) · h1up&rsi40-60 P=0,0015 · quiet30&h1up P=0,0070. Agulha GTQ = bandas q25-75 dos 14 GT-estritos h1up em 5 features (legpos60, atr_spike, ema21_dist, sweep_depth, supply): N18 · hit 44,4% · +12,9 · DD -4,1 · stk -4 · GT-precisao 28% (5/18 SAO fundos do Cris; teto historico ~11%). ESTATUTO: CALIBRACAO label-fitted (P=0,23 ns, N18); banda larga q10-90 auto-refuta -> assinatura APERTADA. Veredito visual Cris nos plots GTQ+DF: 5-6 fundos validos, resto pontos altos.',
  array['seed:memory_delta_20260705','layer-2','h1up-fdr','gtq-agulha'],
  'layer2_cris35_lenses / layer2_gtq_conjunction / plot_gtq18_df40 (commits ate b467a97/8a778fe)',
  'active'
),
(
  md5('seed:memory_delta_20260705:memory_items:rodada-macro-estrutural-null-licao')::uuid,
  'product', 'internal', 'feedback',
  'Rodada macro-estrutural: assinatura de retracao sobrevive DA · LICAO null-de-candidatos',
  'Camada de leitura de pernas macro causal (zigzag r-ATR no 15M). SOBREVIVE ao DA com null honesto: fundos GT = retracao PROFUNDA da ultima perna macro (med 0,74 vs candidatos nao-GT 0,42; banda 0,5-1,3: 58,1% vs 31,3% = lift 1,86, z~6) — dimensao que legpos60 (15h) nao via. REFUTADOS: nivel swing-high-rompido (lift honesto 1,32), melhora GTQ-banda (hipergeom P=0,52), agulha v2 q10-q90 (dilui). LICAO PERMANENTE: null de BARRAS ALEATORIAS infla assinaturas de minimos locais ~2x (flush_low e minimo profundo por construcao) — null correto = candidatos do MESMO mecanismo. Banda macro = contexto descritivo sem valor de outcome sozinho; proximo declarado: cruzar carregador sequencial RWS com contexto retr-profundo.',
  array['seed:memory_delta_20260705','macro-estrutural','retrace','null-honesto','method-lesson'],
  'macro_* + gt_*_diag + 3 scripts _da_ (commit 8a778fe)',
  'active'
)
on conflict (id) do nothing;

commit;
