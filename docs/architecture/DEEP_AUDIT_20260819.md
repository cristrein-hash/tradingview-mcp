# DEEP AUDIT — TRADING SYSTEM — 2026-08-19 (FASE 1: READ-ONLY)

Ordem Cris 19/08: AUDIT → DIAGNOSE → CLASSIFY → PROPOSE → WAIT. Nenhuma alteração aplicada.
Método: 5 auditores paralelos read-only (inventário morto/duplicado · semântica/correção · fluxo de dados ·
arquitetura/config/entrypoints · testes/segurança/performance) + bootstrap de governança + git state.
Autoridade vigente: diretrizes 19/08 (notify.py único, 4 canais, TG=ENTRADA+LEITURA-LONG, avisos/infra shadow,
reclaim/retoma deletados, candle-reader off) prevalecem sobre docs anteriores.

## A. EXECUTIVE VERDICT
Sistema FUNCIONAL e coerente no caminho crítico (bar_store single-reader, atomicidade tmp+replace, causalidade
das barras fechadas e shift DXY verificados CORRETOS). Os riscos reais concentram-se em 7 causas-raiz:
centralização Telegram a meio, frescura não-uniforme, múltiplas fontes de verdade, ausência de package
(sys.path hacks), legado não formalmente removido, robustez operacional (crash-loop/fail-open), docs stale.
Nada CRITICAL ativo hoje; 3 HIGH confirmados/quase-confirmados. 11 commits locais NÃO pushados (trabalho 19/08).

## B. SYSTEM MAP (real)
33 LaunchAgents ativos + 1 _disabled_ (candle-reader) + 2 NOT-LOADED (realtime-monitor, fj-ws). Todos os alvos
existem. Fluxo: TV/CDP → bar_store (único MCP reader de barras, 60s) → store/ + extend RAW canónicos (em
research/revalidation!) → store_reader (canónico; fresh=heartbeat) → engines (cp/a1a2/router/amd/l1/l2),
reader (e1→e2 Opus), contexto (context_engine→market_context.json; contextual_read/mtf_cross p/ price_shock),
regime (regime_engine v5-4H + layer1_service 1D), vigias (health_check→PENDING/infra_events; watchdog),
saída = notify.py (4 canais) + receiver/bridge/d2r com senders próprios.

## C. CRITICAL FINDINGS (nenhum CRITICAL; HIGH primeiro)
C1 HIGH CONFIRMED — E0/MTF (contextual_read.py:37-80, mtf_cross.py) e A1/A2 (a1a2_runtime.py:33,57) leem o
   store DIRETO sem verificação de frescura: num congelamento (como 18/08 02:11) decidem sobre dados velhos
   até ~45min (só o vigia externo trava). FIX: rota via store_reader + gate fresh()/age_s.
C2 HIGH NEEDS_VERIFICATION — store_reader.fresh("60"/"240") mede heartbeat do store_meta mas bars() lê
   research/revalidation/raw_1h/4h — se o poll bate e o RAW não é reescrito, fresh()=True sobre 4H stale.
   Consome: sweep_reject_guard (gate LONG) e AMD. FIX: frescura derivada do MESMO ficheiro lido.
C3 HIGH CONFIRMED — DOIS caminhos LLM vivos: claude_recheck.py (89KB, subprocess do receiver:1760) E
   e2_quality (reader canónico). Custo duplicado + risco de leituras divergentes. DECISÃO CRIS (ver O).
C4 MEDIUM CONFIRMED — AMD ping2: falha de envio Telegram marca candidato como pinged (run_amd_cycle.py:132-134)
   → sinal perdido sem re-tentativa (ping1 faz certo). FIX 1 linha.
C5 MEDIUM CONFIRMED — health_check.market_open com fecho 21:00 UTC hardcoded = correto só no horário de verão;
   no inverno desfasa 1h (falsos congelamentos na janela 21-22 UTC). FIX: zoneinfo NY/Lisboa.
C6 MEDIUM CONFIRMED — choch_guard aceita dossiê VELHO (docstring promete fail-open em stale; código só trata
   ausente). FIX: gate por dossier_age_s.
C7 MEDIUM CONFIRMED — guards em notify_surfaced embrulhados em except:pass = fail-open silencioso
   (política pede fail-closed em SHORT; mitigado por SHORT já ser shadow). Escritores concorrentes no RAW 4H
   (bar_store + regime_engine fallback) = lost-update possível; fallback_ok() anti-herd só honrado pelo Cp.
C8 MEDIUM CONFIRMED — 8 daemons KeepAlive sem ThrottleInterval → crash-loop silencioso a ~10s se import falhar.

## D. SEMANTIC INCONSISTENCIES (confirmadas)
D1 entry_validator: gate reader-SHORT é código INALCANÇÁVEL (ok_reader nunca True p/ SHORT) — comentário
   promete "fail-closed com reader"; realidade = SHORT nunca enviado. Corrigir código OU comentário.
D2 L1 telegram_notify lê cand['timestamp'] mas o runtime produz 'candidate_timestamp' → "barra ?" no alerta.
D3 R fixo no rótulo: Cp/A1A2 "(3R)" e AMD "(2R)" hardcoded — mostrar R real calculado de ent/sl/tgt.
D4 scoreboard display: "Lisboa" no header mas now() naive + utcfromtimestamp no detail — unificar ZoneInfo.
D5 a1a2 docstring "macro==BULL" desatualizada (aceita BULL/RANGE + fast-path 4H).
D6 reclaim_location_gate.py = HTF Location Gate genérico do reader — nome herda linha morta (renomear
   htf_location_gate.py quando seguro).
D7 zone_watch.ZONES hardcoded no código com zonas datadas de 18/08 sem validade — migrar p/ trader_map ou expirar.
D8 news_gate._imminent_ffevent escolhe evento por |Δt| — pode apontar p/ evento já passado.
D9 VELA_LIVE (var interna) vs VELA_PRODUCTION_AUTHORIZED (env real) — naming fora do padrão.
Verificados CORRETOS (registo): SL-first same-bar no scoreboard; polaridade SHORT hit_sl; i0 exclui barra de
entrada; cruzamentos zone_watch/sentinel; shift DXY t+86400; exclusão de barra em formação; _live_read E2.

## E. DEAD / LEGACY / DUPLICATE INVENTORY (evidência por item no output dos auditores)
DELETE_CANDIDATE (sem plist, sem import vivo, sem subprocess — confirmado por grep+entrypoints):
  alert-bridge/config_stack.py · alert-bridge/arm_level.py (sistema de níveis cancelado 11/08) ·
  alert-bridge/investinglive_news.py (duplicado do collector external_factors_v2 vivo) ·
  my-strategy/core/scoreboard/scoreboard_dir_split.py (tool de auditoria de ontem, já servida — arquivável).
ARCHIVE (cluster D2R/research sem cabeça de processo): run_research_cycle, run_d2r_backfill,
  generate_d2r_summary, research_status, evaluate_r_outcomes, report_indicator_edge, weekly_review,
  enrich_indicator_outcomes, setup_watch_manager, evaluate_setup_outcomes, e1_replay, plot_today_signals,
  find_dream_demands, poc_scan_xau_4h + subdirs reports/ (L1 ≈45 ficheiros) e parity/ (L2, CP) pós-validação.
DEAD-CODE EMBUTIDO em daemon vivo: realtime_monitor.py loop de level-cross alimenta send_level_alert no-op.
LEGACY TRAVADO (manter, política): monitor_xau_4h_strategies, candle_reader, level_alerts_watcher,
  regime/archive/dead_regime_B_v3.
NEEDS_DECISION: ilha input_normalization+live_input_adapter (construída, nunca ligada); forward_outcome/*
  (ferramenta manual de qualidade forward); candidates/ (research).
FLAGS: E2_CONT_SIGNAL lida e nunca exportada (morta); RECLAIM_TELEGRAM/WATCHDOG_TELEGRAM = limpas (0 refs).

## F. ARCHITECTURE PROBLEMS (causas-raiz)
RC1 Centralização Telegram INCOMPLETA: e2_quality._tg_send ainda POSTa direto (linha 142) e é o transporte de
    4 daemons; L1/L2 telegram_notify* ainda enviam; auto_d2r_daily.send_telegram usado por 2; receiver usa
    HTML (formato divergente). 10 loaders de TELEGRAM_BOT_TOKEN.
RC2 Sem package: sys.path.insert sistémico (pior: regime_engine 4×), imports cruzados
    estratégia→alert-bridge, god module e2_quality (1004 linhas = reader+gates+sender), paths absolutos
    hardcoded em ficheiros live, config/paths.py IGNORADO por toda a produção.
RC3 Frescura não-uniforme (ver C1/C2) + side-effect no import do b_engine (ordem manual no router).
RC4 Múltiplas fontes de verdade: regime 3 ficheiros (current_layer1/current_regime/regime_l1_v4) com
    consumidores sobrepostos; SL-first 4 implementações vivas (scoreboard, router-B, journal resolve+capture);
    zonas OB 3 mecanismos (pine_boxes, ob_watch, polarity zones); 4 leitores de barras paralelos.
RC5 Legado não removido formalmente → foi a causa direta da confusão "AMD/L1" de 19/08.
RC6 Robustez: KeepAlive sem throttle, fail-open silencioso, envio-falhou-marca-enviado.
RC7 Docs stale: OPERATIONAL_INVENTORY as-of 25/05 ("8 agentes" vs 33 reais); 05_SYSTEM_ARCHITECTURE descreve
    fluxo pré-stack (receiver→recheck como canónico).

## G. DATA INTEGRITY / CAUSALITY
Corretos: single-writer de barras (bar_store), atomicidade, barra-fechada, close_s 23h 1D, DXY shift causal,
guard anti-truncamento RAW, _live_read E2. Problemas: RAW canónicos 1H/4H/DXY vivem SOB research/ mas são
dependência runtime (acoplamento frágil + escopo de cleanup pode ignorá-los); escritores concorrentes no RAW
4H (C7); retenção 30d do store faz o scoreboard esconder sinais antigos como unresolved (marcar
EXPIRED-NO-DATA ou resolver via raw_reader); RSI 15M da barra EM FORMAÇÃO entra no dossiê E0 (etiquetar);
derived (market_context/current_regime/current_layer1) sem source_poll_ts (linhagem).

## H. OPERATIONAL SAFETY
Secrets: limpos (0 tokens hardcoded; .env 600). Risco grupo-vs-pessoal concentrado nos senders fora do notify
(RC1). Crash-loop (C8). price-shock/gld-ws fora do DAEMONS do health_check (watchdog cobre). fj-ws e
realtime-monitor plists NOT-LOADED no disco (inconsistência com decisões: fj-ws desligado 31/07 OK mas sem
_disabled_; realtime-monitor cancelado 11/08 idem). 11 commits não pushados.

## I. TESTS & VALIDATION
21 módulos com --selftest; ZERO suite pytest do stack Python; run_safety_report agrega só 3 guards e sai
sempre 0 (nunca bloqueia); 6 guards XAU-15M fora do agregador. Sem verificação executável: router,
store_reader, tab_pin, scanner L1. Selftest do notify testa formato mas NÃO o routing (a invariante mais
crítica de 19/08 sem cobertura). Invariantes sem sanity-check: "único emissor", "INFRA nunca no chat",
"mute universal", "formato canónico".

## J. EFFICIENCY OPPORTUNITIES (reais)
ThrottleInterval nos 8 KeepAlive · decidir recheck-vs-E2 (custo LLM duplicado) · count=N nas leituras do
store + retain finito 60/240 (trava crescimento O(histórico) do re-parse; hoje custo baixo) · e2 consumir
dossiê pronto em vez de re-derivar secções · zone-watch/price-shock a 30s releem dados idênticos (barato; ok).

## K. PROPOSED TARGET ARCHITECTURE (incremental, sem reescrita total)
1. `notify.py` = ÚNICO transporte Telegram (com audience + hard-lock por parâmetro + loader .env central);
   exceções documentadas: receiver (HTML/ingress) e bridge (chunks). L1/L2/e2/auto_d2r migram.
2. `store_reader` = ÚNICA porta de leitura do store com fresh()/age_s obrigatórios; contextual_read, a1a2,
   level_alerts (se sobreviver), scoreboard passam por ela; fresh derivado do ficheiro lido (C2).
3. Regime: contrato escrito de autoridade — Layer1 1D = macro/router; v5-4H = auxiliar; regime_l1_v4 = gate
   interno L1. Um doc, três consumos explícitos (não fusão de código nesta fase).
4. `resolve_sl_first()` único (lib partilhada) — scoreboard/router-B/journal chamam o mesmo.
5. Package leve `tsys/` (ou sys.path único no wrapper) para matar os inserts — fase estrutural, mais tarde.
6. RAW canónicos: mover raw_1h/4h/dxy p/ core/bar_store/store/ OU documentar formalmente a dependência
   runtime→research (mexer nisto exige lockstep com bar_store+regime+layer1+consumidores research).

## L. CLEANUP PLAN (lotes pequenos, reversíveis; commit por lote; validação antes/depois)
LOTE 1 — fixes confirmados HIGH/MEDIUM (código, sem mudança de comportamento desejado):
  a1a2 fresh gate (C1b) · contextual_read via store_reader+age (C1a) · AMD ping2 send-fail (C4) ·
  choch stale gate (C6) · health DST (C5) · fresh 60/240 do ficheiro real (C2) · log no _route_to_file.
  Validação: selftests + 1 ciclo de cada daemon + infra_events. Rollback: git revert por commit.
LOTE 2 — semântica: D1-D9 (validador SHORT, timestamp L1, R real, TZ scoreboard, docstrings, renomear
  reclaim_location_gate→htf_location_gate com shim de import, zonas com validade, news_gate upcoming).
LOTE 3 — centralização Telegram final (RC1): e2._tg_send→notify · L1/L2 notifiers→notify (hard-lock
  preservado) · extrair send de auto_d2r p/ realtime_monitor/tg_trade_signal · matar loop morto do
  realtime_monitor · guard executável "único emissor" no run_safety_report (a falhar de verdade).
LOTE 4 — morto/arquivo: DELETE_CANDIDATES (4, após git grep final) · ARCHIVE cluster D2R (14 ficheiros,
  move p/ alert-bridge/archive/) · plists NOT-LOADED → _disabled_ · reports/parity das estratégias →
  archive pós-confirmação · decisão da ilha input_normalization/live_input_adapter.
LOTE 5 — fontes de verdade: resolve_sl_first único · contrato de regime escrito · fallback_ok em
  regime/price_shock · dono único do RAW 4H.
LOTE 6 — robustez/perf: ThrottleInterval 8 plists · count=N + retain 60/240 · price-shock/gld no health_check.
LOTE 7 — docs/org: OPERATIONAL_INVENTORY + 05_ARCH atualizados ao real · outputs gerados → pasta de
  artefactos · selftest de routing no notify.
(Ordem respeita: CRITICAL/HIGH → semântica → duplicação → morto → estrutura → perf → cosmética.)

## M. DELETE CANDIDATES (nenhum autorizado)
config_stack.py · arm_level.py · investinglive_news.py (dup) · scoreboard_dir_split.py (arquivável).
Tudo o resto de "morto" é ARCHIVE (move reversível), não delete.

## N. DO-NOT-TOUCH (durante toda a limpeza)
RAW canónicos e ledgers históricos (.router_state, alerted.jsonl, forward logs) · matemática congelada
aprovada (regime_l1_v4, scanner L1 V1, macro_structural_v3, cp_engine_live, a1a2 detect, l2_engine) ·
receiver/cloudflared/secrets/.env · Supabase (write-protocol próprio) · memória · pastas archive existentes ·
trader_map/zone_watch estado operacional do dia.

## O. QUESTIONS / DECISIONS REQUIRED (Cris)
O1. claude_recheck vs E2: manter os DOIS caminhos LLM ou desligar o recheck (receiver fica ingest-only)?
O2. L1/L2 notifiers migram para notify.py (toca em estratégia aprovada — pede a tua autorização explícita)?
O3. Cluster D2R (14 ficheiros) → archive? Ilha input_normalization/live_input_adapter → ligar ou arquivar?
O4. RAW canónicos: mover para core/bar_store/store/ (lockstep) ou documentar e deixar onde estão?
O5. Push dos 11 commits de 19/08?
O6. realtime-monitor e fj-ws: formalizar _disabled_?
