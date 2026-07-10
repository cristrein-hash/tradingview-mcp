-- ============================================================================
-- SUPABASE MEMORY — DELTA SEED · seed:memory_delta_20260710_session_close
-- ============================================================================
-- Bloco: fecho total 2026-07-10 pré-restart (ordem Cris). Estado desde b517312 (checkpoint 0708).
-- Aplicar via scripts/supabase/apply_memory_delta.py (autorizado Cris 2026-07-10 no fecho).
-- Zero RAW/candles/secrets/outputs massivos. Idempotente (on conflict do nothing).
-- ROLLBACK: delete from memory_items where tags @> array['seed:memory_delta_20260710_session_close'];
-- Total: 6 rows.
-- ============================================================================
begin;
insert into memory_items (id, scope, visibility, category, title, body, tags, source_ref, status) values
(
  md5('seed:memory_delta_20260710_session_close:memory_items:l1-4h-status')::uuid,
  'product', 'internal', 'project',
  'L1 4H EMA21: exit review fechada (+3R mantido), gates pre-go-live fechados, dry-run live validado — producao NOT_AUTHORIZED',
  'Bloco L1 EMA21 fechado e pushado. (1) Exit review completa: manter +3R fixo (DA PASS); CHAND_5/trailing/let-run REJEITADOS (knife-edge, 88-92 pct do ganho em 2025, EX-2025 falha). Scanner reconciliado a SL V1 (zona_OB_low-0,1ATR), FINAL-24 reproduz 34/34 (commit 4b58ac9). (2) NAS live causal gate resolvido para dry-run (ledger_frozen i-1, barra fechada, forming excluida; threshold 1.31). (3) Pre-go-live controls: telegram_notify --send exige L1_PRODUCTION_AUTHORIZED=1; NAS startup fail-closed; capacity_journal.py puro NAO wired (max 2 pos, EUR200 agregado, EUR100/pos, LONG-only, broker MANUAL_APPROVAL_ONLY) (commit 6a32d28). (4) Dry-run live final XAUUSD 4H validado v2: 13 ob_zones reais, scanner evaluate live => no_candidate (regime_d1_not_BULL), tripwire Telegram zero (commit 630b806). PRODUCAO SEGUE NOT_AUTHORIZED; nada de Telegram/broker/daemon/monitor ativado.',
  array['seed:memory_delta_20260710_session_close','l1-ema21','exit-3r-mantido','dry-run-validado','not-authorized'],
  'reports/L1_EXIT_REVIEW_{PREREG,REPORT,DA}.md; my-strategy/reports/L1_FINAL_LIVE_XAU_DRYRUN_{REPORT,DA}.md; commits 4b58ac9/6a32d28/630b806',
  'active'
),
(
  md5('seed:memory_delta_20260710_session_close:memory_items:a2-v2-detector')::uuid,
  'product', 'internal', 'project',
  'XAU 15M detector A2 v2 = 32/42 no GT (CAP 12/12, RANGE 4/4, BULL 16/26); autopsia 0/42 AUSENCIA_REAL; 10 falhas BULL escada vertical SEM solucao',
  'Autopsia dos 42 VELA DE FUNDO (commit 8efd8ab): A2 NUNCA falhou por ausencia de estrutura (0/42); causas = geometria de pavio (11), invalidacao fragil por furos 0,01-0,11 ATR (5), capitulacao LATE_POR_NATUREZA (7). Reparo v2 (commit ef7c3ea): bandas por corpos/aceitacao (max/min CLOSE +-4 barras, largura 0,7-2,5 ATR), invalidacao tolerante (fecho >0,5 ATR alem OU 2 fechos consecutivos), familia capitulacao aceita regiao nascida do flush <=24h. Gate 42 SEM filtro de autoridade = 32/42 (commit d9493b5). As 10 falhas BULL (#8,9,11,12,13,15,17,27,29,30) = pullbacks de escada vertical: retracao <4 ATR nao vira ciclo, maquina nao publica topos de degrau. Tentativas falhadas e registadas: pause ruler (0/42, DISCARDED), gate BOS SMC do RAW (internal 3/10 mas 5,7 zonas/sem sujo; swing-only 0,68/sem limpo mas 0/10; commit 91d73ef). Cris admitiu nao saber resolver mecanicamente. GT principal = 42 VELA DE FUNDO em catalog_manual_tags_20260707.json (26 BULL_PULLBACK / 4 RANGE / 12 CAPITULACAO).',
  array['seed:memory_delta_20260710_session_close','xau-15m-a2-v2','gate42-32-de-42','escada-vertical-aberta','gt-42-vela-fundo','bos-gate-failed'],
  'research/xau_15m_structural_reading/{a2_detector_v2.py,autopsy_42.py,bos_gate.py}; reports/XAU_15M_A2_DETECTOR_REPAIR_SPEC.md; commits 8efd8ab/ef7c3ea/d9493b5/91d73ef',
  'active'
),
(
  md5('seed:memory_delta_20260710_session_close:memory_items:authority-pause-rejections')::uuid,
  'product', 'internal', 'feedback',
  'REJEICOES Cris 2026-07-10: Pause Ruler DISCARDED_BY_VISUAL_REVIEW; filtro de autoridade 168h REJECTED_AS_IMPLEMENTED; DA restrito a verificacao de lookahead APENAS',
  'Duas rejeicoes permanentes (commit b566d76/d9493b5). (1) PAUSE RULER (regua de pausa apertada p/ degraus de escada): densidade 0,95/sem OK mas cobertura 0/42; degraus reais tem ~4-5 barras < minimo 8 da spec => DISCARDED_BY_VISUAL_REVIEW. (2) FILTRO DE AUTORIDADE 168h: invencao do Claude NAO solicitada (conceito veio de um edit de DA; implementacao dura nao pedida); prints do Cris provaram TODAS as 9 zonas SEM_AUT validas (ex.: zona Out/2025 segurou capitulacao Jun/2026). Regra: se a zona esta bem formada e o preco reage nela, permanece valida; idade NAO invalida. => REJECTED_AS_IMPLEMENTED; gate recomputado sem filtro (32/42). ORDEM PERMANENTE do Cris: DA ESTA PROIBIDO de emitir qualquer informacao, opiniao ou inducao que nao seja verificacao de lookahead ("alucinacao de IA na mais forte manifestacao"). Tambem permanente: comportamento seco obrigatorio (responder curto/objetivo; fazer somente o que Cris mandar; formato 4 partes; ambiguidade => parar e perguntar).',
  array['seed:memory_delta_20260710_session_close','pause-ruler-discarded','authority-filter-rejected','da-lookahead-only','dry-behavior-mandatory'],
  'research/xau_15m_structural_reading/reports/{XAU_15M_PAUSE_RULER_SPEC.md,XAU_15M_A2_DETECTOR_REPAIR_SPEC.md}; memoria PRINCIPAL_1; commits b566d76/d9493b5',
  'active'
),
(
  md5('seed:memory_delta_20260710_session_close:memory_items:entry-logic-spec')::uuid,
  'product', 'internal', 'project',
  'XAU 15M ENTRY contextual = SPEC ditada por Cris (REGIAO+CONTEXTO+RETESTE+DEFESA+RECLAIM) — SPEC_ONLY_NOT_IMPLEMENTED',
  'XAU_15M_ENTRY_LOGIC_SPEC.md (commits c293230/6ca43f5/ea00ef7): entry nasce da RELACAO preco-regiao, nao de sinal; detector (v2, 32/42) so responde onde/tipo/quando/validade — ele NAO compra. Sequencia obrigatoria pos-regiao-conhecida: reteste -> defesa -> mudanca de comportamento -> entrada no reteste/reclaim pos-defesa. NUNCA: candle que cria a regiao, rompimento, primeiro bounce. Definicoes operacionais do Cris: DEFESA = tocou a demanda e nao aceitou abaixo (1 barra pode bastar, fecha dentro/acima); RECLAIM = apos defesa, fecho acima do topo da barra de defesa OU do topo da regiao; entry = fecho da barra de reclaim; SL = piso da regiao -0,1 ATR; alvo inicial 3R; regiao larga demais = RISCO_RUIM (nao forcar). Mudanca real de comportamento fica como leitura do Reader (nao mecanizar demais). D2 = veto contextual BULL topo sem pullback proporcional, NAO filtro universal. ORDEM DE LEITURA OBRIGATORIA: 1 familia estrutural, 2 regiao valida p/ familia, 3 movimento ate ela faz sentido, 4 corrigindo/capitulando/repicando, 5 so entao defesa/reclaim. Defesa/reclaim = GATILHOS FINAIS; logica da entry = CONTEXTO+FAMILIA+POSICAO+REACAO.',
  array['seed:memory_delta_20260710_session_close','xau-15m-entry-spec','spec-only','defesa-reclaim-gatilhos-finais','contexto-antes-de-gatilho'],
  'research/xau_15m_structural_reading/XAU_15M_ENTRY_LOGIC_SPEC.md; commits c293230/6ca43f5/ea00ef7',
  'active'
),
(
  md5('seed:memory_delta_20260710_session_close:memory_items:retest-classifier-spec')::uuid,
  'product', 'internal', 'project',
  'XAU 15M classificador causal de contexto do reteste = SPEC_ONLY_NOT_CODED; a/c/d resolvidos; RANGE_BASE bloqueado (regua refutada por print)',
  'XAU_15M_RETEST_CONTEXT_CLASSIFIER_SPEC.md (commits 6100616/6368063 + edit fecho): classificar contexto do reteste ANTES de defesa/reclaim, SO pecas existentes (macro_at 1D+1H override; ciclo A2 r=4; S2a px1d=(close-EMA21_1D)/ATR15 congelado BEAR&>=0=raso; S3 bounce_peaks K=1,5 ndesc>=2=pressionando; regiao v2; pos384 so-reportado). Classes: BULL_PULLBACK / BULL_VETADO_TOPO / RANGE_BASE / BEAR_CAPITULATION / BEAR_BOUNCE_RASO / UNCLASSIFIED. Decisoes Cris: (a) reteste = saiu (1 barra inteira acima da banda) e voltou; (c) SEM pos384 como regra; veto topo = ciclo nao virou (pullback proporcional = virada de ciclo >=4 ATR — regua existente, zero threshold novo); (d) toque BULL sem virada = BULL_VETADO_TOPO (classe propria, nao entry). BLOQUEIO (b): "fundo REAL do range" sem mecanica aprovada — proposta "banda contem ultimo extremo BOTTOM" REFUTADA pelo GT #21 (21-nov-2025: fundo mais alto dentro do range, acima do low #20, entrada boa => fundo real != piso absoluto). Achado dos prints: macro_at 4H/1D so APROXIMA ranges 15M (trunca SEG2 em 14-nov vs range real ate ~25-nov; SEG4 engloba nao-range; SEG3/5 corrigidos pelo Cris); Cris distingue range ACUMULACAO vs DISTRIBUICAO e REGIAO PLT como ancora. Hipotese Cris NAO ordenada: 2o layer de regime detector especifico 15M. Classificador NAO codado ate decisao.',
  array['seed:memory_delta_20260710_session_close','retest-context-classifier','spec-only-not-coded','range-base-bloqueado','macro-aproxima-15m','segundo-layer-15m-hipotese'],
  'research/xau_15m_structural_reading/reports/XAU_15M_RETEST_CONTEXT_CLASSIFIER_SPEC.md; commits 6100616/6368063',
  'active'
),
(
  md5('seed:memory_delta_20260710_session_close:memory_items:session-close-open-state')::uuid,
  'product', 'internal', 'project',
  'Fecho 2026-07-10 pre-restart: pendencias abertas e proximos pontos bloqueados (XAU 15M structural reading)',
  'Fecho total (doc XAU_15M_SESSION_CLOSE_20260710.md). BLOQUEADOS aguardando decisao Cris: (1) mecanica RANGE_BASE fundo-real (regua refutada; possivel 2o layer regime 15M — nao ordenado); (2) 10 falhas BULL escada vertical sem representacao mecanica (ciclo r=4, pause ruler, BOS internal e swing todos falharam); (3) codificacao do classificador de contexto (so apos (1)); (4) etapa 2 entry (defesa/reclaim como maquina de eventos) so apos classificador aprovado visualmente. Trilhas separadas so por ordem: AND S2a-S3 = PRE_APPROVED_FOR_REVIEW_AFTER_ENTRY_APPROVAL (rescue winners 135/150/164); Fase 3 indicadores nas regioes. Blocos anteriores desta fase (commits 461e3cf..8c0f4dd): reset leitor contextual, D1-D3 (D2 anti-top-buy confirmado), mapa HTF BEAR = CALIBRATION_SIGNAL, OB detector = STERILE, skip ledger (S2a VALIDATED_CALIBRATION_SIGNAL, S3 NEW_PROMISING_SKIP_AXIS, sem composite aprovado), janela virgem (proibido conclusoes; base congelada). Licao operacional plots MCP: desenhar em data antiga exige chart_scroll_to_date previo para carregar historico, senao TradingView prende o desenho no viewport atual. Leg engine F0-F1.5 = BLOCKED (F1 seed degenerado). Nada de producao/runtime/Telegram/broker tocado nesta fase.',
  array['seed:memory_delta_20260710_session_close','fecho-pre-restart','pendencias-bloqueadas','skip-ledger-status','plot-scroll-lesson'],
  'research/xau_15m_structural_reading/reports/XAU_15M_SESSION_CLOSE_20260710.md; git log b517312..HEAD',
  'active'
)
on conflict (id) do nothing;
commit;
