-- ============================================================================
-- SUPABASE MEMORY — DELTA SEED · seed:memory_delta_20260716_realtime_monitoring_session
-- ============================================================================
-- Sessao 2026-07-16: teste trade ao vivo (licoes); janelas de sessao; formato Telegram;
-- arquitetura monitoracao realtime (Camada 1 aprovada + E2 redesenhado + P1 daemon LIVE);
-- infra producao nova (news lane InvestingLive + ponte Telegram<->Claude).
-- Aplicar via scripts/supabase/apply_memory_delta.py. Idempotente. Total: 5 rows.
-- ============================================================================
begin;
insert into memory_items (id, scope, visibility, category, title, body, tags, source_ref, status) values
(
  md5('seed:memory_delta_20260716_realtime_monitoring_session:memory_items:live-trade-test')::uuid,
  'private', 'internal', 'feedback',
  'TESTE TRADE AO VIVO XAUUSD (2026-07-16) = -1R stopado; execucao/disciplina SOLIDAS, perda por CONTEXTO',
  'Desafio Cris: 1 trade real XAUUSD Pepperstone via proxy (Claude sinaliza, Cris clica), SL ~100 EUR, TP 2-3R. Resultado: LONG @4035.3 -> SL 4027 = -1R (~-100 EUR). ACERTOU (o objetivo): paciencia ~1h30 atraves de 6 rejeicoes em 4034 + 4 recuperacoes falhadas (nao perseguiu nenhuma); entrada so na confluencia COMPLETA (break+hold 4034 + 15m RSI cruzou MA + duplo-fundo + absorcao); retest aguentou; alarmes Telegram + plot + 2 avisos de gestao atempados. LICOES (o que correu mal): (1) TIMING/SESSAO = filtro 1a classe (entrou em vacuo fim-de-Asia sem catalisador; ADX colapsou ~15 = sem combustivel; erodiu antes de a liquidez europeia chegar); (2) REGIME domina (mean-reversion LONG contra bear/risk-off = baixa continuacao); (3) ADX morto ~15 = red flag. Stopout NORMAL de entrada bem construida que o mercado nao seguiu na janela morta, NAO erro de processo. Proxy = tg_trade_signal.py + investinglive_news.py.',
  array['seed:memory_delta_20260716_realtime_monitoring_session','live-trade-test','xauusd','timing-session','regime','adx-sem-combustivel','execucao-disciplina'],
  'memory/project_live_trade_test_20260716 · alert-bridge/{tg_trade_signal.py,investinglive_news.py} · commit 1bab1f7',
  'active'
),
(
  md5('seed:memory_delta_20260716_realtime_monitoring_session:memory_items:session-windows')::uuid,
  'private', 'internal', 'reference',
  'Janelas de sessao/volatilidade FX/ouro (percepcao Cris, PT+UTC, a VALIDAR)',
  'Horas Portugal (WEST=UTC+1 verao) + UTC. Percepcao do Cris, a mapear com precisao numa sessao dedicada futura. ASIA liquidez ~01:00-02:00 PT (00:00-01:00 UTC). LONDRES mais forte ~12:00-14:30 PT (11:00-13:30 UTC) na convergencia com abertura NY. NY volatilidade inicial ~14:30-15:30 PT (13:30-14:30 UTC). NY reacao fim-de-dia ~18:30-20:30 PT (17:30-19:30 UTC). ZONA MORTA = vacuo entre fim-da-Asia e Londres forte ~02:00-12:00 PT (01:00-11:00 UTC) = onde o trade 2026-07-16 apodreceu (entrou ~04:45 PT). TAREFA FUTURA: construir mapeador empirico de volatilidade/horarios (ATR/range/volume por hora UTC, resolver DST US/UK/PT, validar p/ ouro, integrar como gate de timing nos engines). Percepcao = ponto de partida, NAO verdade.',
  array['seed:memory_delta_20260716_realtime_monitoring_session','session-windows','volatility','timing-gate','future-mapper','reference'],
  'memory/reference_session_volatility_windows',
  'active'
),
(
  md5('seed:memory_delta_20260716_realtime_monitoring_session:memory_items:telegram-concise')::uuid,
  'private', 'internal', 'feedback',
  'Ponte Telegram = resposta CURTA/objetiva/concisa (NAO formato terminal), detalhe persistido (Cris 2026-07-16)',
  'Ao responder pela ponte Telegram (@Cristrein_Trading_bot, canal de trabalho), as mensagens DEVEM ser curtas, objetivas, claras e concisas, com info de qualidade persistida p/ o Cris decidir e ajudar eficiente. NAO o formato longo de terminal (tabelas exaustivas, preambulo). Why: le no telemovel em movimento; respostas longas sao inutilizaveis. How: liderar com decisao/achado + numeros-chave + a UMA coisa a decidir/fazer; cortar survey de opcoes; persistir detalhe em disco/memoria; se precisar de escolha, pergunta curta + opcoes curtas. Disciplina (null-first, lookahead, estrutura-primeiro) MANTEM-SE; muda o FORMATO da saida, nao o rigor. Aplica-se ao canal Telegram; no terminal o formato detalhado mantem-se quando util.',
  array['seed:memory_delta_20260716_realtime_monitoring_session','telegram-bridge','communication-format','feedback'],
  'memory/feedback_telegram_concise_format',
  'active'
),
(
  md5('seed:memory_delta_20260716_realtime_monitoring_session:memory_items:realtime-arch-camada1')::uuid,
  'product', 'internal', 'architecture',
  'ARQUITETURA MONITORACAO REALTIME XAU: Camada 1 APROVADA + E2 redesenhado + P1 daemon LIVE (Cris 2026-07-16)',
  'Motivada por 2 erros opostos (short XAU perdido = OMISSAO por gap de monitoracao ~19min; SL apressado = COMISSAO por vacuo/contra-regime). Arquitetura hibrida: 1 daemon rapido DETERMINISTA (24h, CDP-only via MCP, 0 tokens) + reusa daemons EF/news + bridge de juizo Claude (ensemble) SO no gatilho. CAMADA 1 APROVADA (entries alerta-only, ZERO auto-trade): A1/A2/B/Cp/5ATR-STACK(N181)/CASCEX 15M + L1/L2 4H LONG. Painel in-sample verificado POS Devil-Advocate (consolidate_entry_metrics): DA corrigiu proveniencia do 5ATR (STACK aprovado N181 WR65.2 +75.6R DD-3 streak-3, NAO o CSV256 baseline); exits mistos marcados; ressalvas surfacadas (Cp so bear2026; CASCEX NET confinado a janela vista; A1/A2 N minusculo). CAMADA 2 (detetor 24h oportunidades LONG/SHORT convergentes) NAO aprovada ainda. E2 REDESENHADO (resolve risco de veto): vetos DETERMINISTICOS auditaveis fora do LLM (vacuo/catalisador/RR/perseguicao/stale); contra-regime CONDICIONAL a ausencia de exaustao (nao a direcao = licao Cp); ensemble ADVERSARIAL 3-lentes (refuta com razao concreta, nao vota); saida GRADUADA (forte/watch/descarta); calibracao EMPIRICA no shadow-run (2 testes: short-hoje passa, SL-ontem veta). Questoes resolvidas: cadencia event-driven+60s piso, limiares do shadow, 3-lentes, MCP-first. Build 6 fases, autorizacao por fase. P1 LIVE: realtime_monitor.py (launchd KeepAlive + caffeinate, alerta de nivel armado, watchdog MONITOR CEGO, kill-switch, guarda de simbolo). Fix pos-ativacao: watchdog flapping (staleness por bar-time) removido + cooldown 180s.',
  array['seed:memory_delta_20260716_realtime_monitoring_session','realtime-monitoring','camada1-approved','e2-redesign','p1-daemon-live','xau','user-approved','zero-autotrade'],
  'docs/superpowers/specs/2026-07-16-realtime-monitoring-architecture-design.md · my-strategy/research/revalidation/consolidate_entry_metrics_20260716.py · alert-bridge/realtime_monitor.py · docs/architecture/REALTIME_MONITOR_P1_RUNBOOK.md · commits 5ccb368/23c80bd/f8c3cd0',
  'active'
),
(
  md5('seed:memory_delta_20260716_realtime_monitoring_session:memory_items:prod-infra-news-bridge')::uuid,
  'product', 'internal', 'architecture',
  'INFRA PRODUCAO NOVA (2026-07-16): news lane InvestingLive + ponte Telegram<->Claude LIVE',
  '(1) NEWS LANE RAPIDA: LaunchAgent com.cristrein.external-factors-news @240s -> collectors/investinglive_news_collect.py (RSS keyless, atomico, no-op honesto em falha) -> snapshots/investinglive_news.json (single-writer, evita corrida em latest.json); monitor macro espelha campo news_live em latest.json; escalada Telegram ARMADA (runtime/news_escalate.py, dedup + cooldown 10min, gated NEWS_ALERTS_AUTHORIZED); helper advisory alert-bridge/news_gate.py = gate determinista (high_impact_now + session UTC + ff_event_le_min) que NUNCA bloqueia, consumir no workflow de monitoracao live. Session buckets = percepcao Cris (a afinar por mapeador empirico). (2) PONTE TELEGRAM<->CLAUDE: LaunchAgent com.cristrein.telegram-assistant-bridge (KeepAlive) -> Cris manda msg ao @Cristrein_Trading_bot (chat privado 7073657039, WHITELIST dura) -> corre claude -p --dangerously-skip-permissions --resume (AUTONOMIA TOTAL aprovada, sessao persistente, cwd=repo, sem ANTHROPIC_API_KEY=subscricao Max) -> responde no chat. Comandos /new /stop /start /status; kill-switch 3 camadas. Sinais continuam a parte no grupo (TELEGRAM_CHAT_ID). Workflow via Telegram provou-se nesta sessao (Cg + arquitetura desenhados por mensagem).',
  array['seed:memory_delta_20260716_realtime_monitoring_session','news-lane','telegram-bridge','production-infra','external-factors','news-gate'],
  'external_factors_v2/collectors/investinglive_news_collect.py · external_factors_v2/runtime/news_escalate.py · alert-bridge/{news_gate.py,telegram_assistant_bridge.py} · commits 25e60d2/b33ba2c',
  'active'
)
on conflict (id) do nothing;
commit;
