# FUTURE CORE BOUNDARY

**Criado:** 2026-06-14 · **Modo:** marcação/governança (read-only; nada deletado/movido/produção).

**Inputs:** `docs/LEGACY_KNOWLEDGE_REGISTER.md` · inventário read-only desta sessão (Architecture Truth) · MASTER files (00/02/05/06/10) · OPERATIONAL_INVENTORY.

## 1. Purpose

Definir a **fronteira oficial** da nova arquitetura do Trading System, separando todo componente/estratégia/dado/artefato em 4 baldes: **FUTURE_CORE · QUARANTINE · DELETE_CANDIDATE · REVIEW_LATER** (+ `UNKNOWN/NEEDS_AUDIT` quando incerto).

O novo sistema nasce **mínimo, limpo, RAW-first, auditável, escalável, comercializável e preparado para automação futura**. O sistema velho **não é a fundação** — vira fonte de dados, histórico e peças aprovadas. Nada é deletado agora.

## 2. Boundary Rules

1. Sistema velho ≠ fundação. Core novo puxa apenas peças aprovadas.
2. Estratégias antigas **não entram** no core como estratégia válida.
3. Aprendizado útil já preservado em `LEGACY_KNOWLEDGE_REGISTER.md` — não re-extrair aqui.
4. Toda estratégia anterior à XAU 4H LONG → QUARANTINE ou DELETE_CANDIDATE. Exceção: **XAU 1H LONG → REVIEW_LATER**.
5. XAU 4H LONG / L2-BPT RAW-traced → **FUTURE_CORE_CANDIDATE** (sem produção ainda).
6. Alarmes arquivados = **event history**, nunca validação.
7. "Eliminar" = 3 níveis: eliminar-do-core / quarentenar-rotulado / deletar-só-após inventário+backup/checksum+aprovação explícita.
8. Na dúvida → UNKNOWN/NEEDS_AUDIT, nunca delete.

## 3. FUTURE_CORE Register

Formato: **nome/path** — sub-balde · razão · risco-se-não-marcado · próxima-ação · autorização-antes-de-mudar?

- **RAW data + manifests/checksums** (`/Volumes/GUTS_ LACIE/TradingData/...`) — KEEP_AS_IS · fundação imutável · risco: confundir com derivado · ação: nenhuma (preservar) · autorização: SIM p/ qualquer toque.
- **Dataset registry** (`docs/data/dataset_registry.json`, 21 datasets) — KEEP_AS_IS · inventário canônico · risco: fonte de dados perdida · ação: manter · autorização: SIM.
- **Receiver** (`alert-bridge/tv_webhook_receiver.py`) — KEEP_BUT_SIMPLIFY · ingestão+normalização viva · risco: quebrar ingestão · ação: reduzir ao mínimo, desacoplar recheck · autorização: SIM (produção).
- **Cloudflared tunnel** (`com.cristrein.cloudflared-tunnel`) — KEEP_AS_IS · ingress público · risco: outage webhook · ação: reavaliar se core usar ingest local · autorização: SIM.
- **Event normalization** (`_normalize_indicator_parsed` + PEPPERSTONE gate + whitelist) — REBUILD_CLEAN (extrair módulo) · lógica boa acoplada ao receiver · risco: contaminação provider/ticker · ação: isolar como módulo testável · autorização: SIM.
- **Clean event store** (`indicator_signals.jsonl` 14.983 + schema_version + dedup_index) — KEEP_BUT_SIMPLIFY · journal canônico de sinais · risco: perder histórico de eventos · ação: formalizar schema append-only · autorização: SIM.
- **Custom OB Pine v11/v12** (`my-strategy/pine_alerts/11,12*.pine`) — KEEP_AS_IS (indicador, não estratégia) · fonte de `pine_boxes` no RAW · risco: perder fonte de zonas · ação: manter como indicador-fonte · autorização: SIM.
- **Signal Outcome Lab** (`alert-bridge/logs/signal_outcomes_lab/` evaluator + `outcomes_current.jsonl` 72 CLEAN) — FUTURE_CORE_CANDIDATE / REBUILD_CLEAN · seed limpo do outcome engine · risco: reconstruir do zero sem base · ação: virar outcome engine (manual primeiro) · autorização: SIM.
- **Governance/status registry** (a criar; hoje fragmentado em catalog+status-doc+memória+MASTER) — REBUILD_CLEAN · fonte única de status · risco: status ambíguo · ação: unificar num registry · autorização: SIM.
- **Notification layer** (Telegram) — KEEP_BUT_SIMPLIFY · dispatch humano · risco: alerta de estratégia rejeitada vazar · ação: 1 canal + gate por status · autorização: SIM.
- **Monitoring/health** (`weekly_review.py`, `/health`) — KEEP_BUT_SIMPLIFY · health do stack · risco: cego a falhas · ação: simplificar checks · autorização: SIM.
- **Governance docs** (`LEGACY_KNOWLEDGE_REGISTER.md`, este arquivo, MASTER files) — KEEP_AS_IS · espinha de governança · risco: perder fronteira/lição · ação: completar MASTER 04/07/09+SKILL · autorização: não p/ docs novos.
- **Safety pack** (`~/Desktop/TRADING/L2_REBOOT_SAFETY_PACK_2026-06-09/`, 366) — KEEP_AS_IS · governança de pesquisa RAW · risco: perder evidência válida · ação: manter · autorização: SIM.
- **Helpers** (`repo_root()`, `price_to_ticks_offset()`) — REUSE_AS_IS · utilidades limpas · risco: re-escrever desnecessário · ação: reusar · autorização: não.
- **XAU 4H LONG layer stack** (L1 H1 aprovado + L2 opcional; pack `L2_BPT_LAYER_STACK_STATE`) — FUTURE_CORE_CANDIDATE · único RAW-traced/monumental-safe · risco: confundir com Caminho A antigo contaminado · ação: base do strategy engine (sem produção) · autorização: SIM p/ produção.
- **L1 EMA21 Continuation — módulo offline** (`my-strategy/strategies/xau_4h_long/continuation/L1_EMA21_CONTINUATION/`: STRATEGY/MANIFEST/README + scanner/journal/outcome/telegram_draft) — **FUTURE_CORE / REALIZADO (2026-06-15)** · primeiro módulo do core novo, USER_APPROVED_FINAL/HUMAN_DISCRETIONARY, 100% offline (sem live/daemon/Telegram real) · risco: alguém ligar em produção sem Registry/lookahead-audit · ação: manter offline; ligar runtime só no Production v2 · autorização: SIM p/ produção. Ver OPERATIONAL_INVENTORY §12 (consolidação 2026-06-15).
- **L2-BPT RAW chain** (`/tmp/L2_BPT_*` persistidos no pack) — FUTURE_CORE_CANDIDATE (RESEARCH_CORE) · pesquisa RAW válida · risco: misturar com labs contaminados · ação: manter como research core · autorização: SIM p/ promoção.
- **Future execution adapter** — DESIGN_LATER (disabled by default) · ainda não existe · risco: automação prematura · ação: stub sem credenciais, desabilitado · autorização: SIM (crítico).

## 4. QUARANTINE Register (preservar como lição/contaminação)

- **`slim_features/`** (HD externo) — razão: SLIM infla 5-10× · risco: validar por slim de novo · ação: rótulo de contaminação, não usar · autorização: SIM p/ deletar.
- **Outcomes contaminados** (`indicator_signals_outcomes.*.contaminated_pre_pepperstone` 330 + `.before_synthetic_cleanup`) — razão: bare-ticker→OANDA · risco: outcome falso como verdade · ação: normalizar+RAW-match antes de qualquer uso · autorização: SIM.
- **Caminho A antigo** (A1/A1'/BALANCE; `candidates/xau_4h_reversal_v1_4g_rws_a6*`) — razão: SLIM + look-ahead (2 mecanismos) · risco: ressurgir como "oficial" · ação: quarentena rotulada (caso-escola) · autorização: SIM.
- **Caminho B antigo** (`candidates/xau_4h_caminho_b_long/`) — razão: SLIM inflado · risco: idem · ação: quarentena · autorização: SIM.
- **Auction labs antigos pré-RAW** — razão: sem trace RAW · risco: confundir com BPT RAW atual · ação: quarentena · autorização: SIM.
- **`enrich_indicator_outcomes.py`** (decommissionado, banner DEPRECATED) — razão: bare-ticker bug · risco: re-executar · ação: não executar; reusável só pelo Outcome Lab · autorização: SIM.
- **`backups/legacy_logs/`, `backups/research_logs_*`, `backups/launchagents_archive/`** — razão: histórico de decisão/decommission · risco: apagar lição/rollback · ação: manter como registro · autorização: SIM.
- **Capitulation 4H + Demand Breakout 4H** (no `monitor_xau_4h_strategies.py`) — razão: rejeitadas (R-real / visual) com rota técnica viva · risco: estratégia rejeitada alcançável · ação: **REMOVER ROTA TÉCNICA primeiro**, depois quarentena · autorização: SIM (produção).

## 5. DELETE_CANDIDATE Register (delete só após segurança; NADA agora)

Cada: precisa backup/checksum? · dependência produção? · aprovação? (todos = SIM aprovação)

- **`/tmp/L2_BPT_*` não-persistidos (≈92), `/tmp/_camA_*`, `/tmp/draw_*.py`** — scratch de pesquisa · backup: os do core já no pack · dep prod: não · ação: inventário→delete após aprovação.
- **`eval_tmp/_b_*.json`** — backtest scratch non-XAU · backup: não · dep: não · ação: delete após inventário.
- **Backups redundantes** (`operational_prompt.md.backup.*` + `strategy_rules.json.backup.*` + `watchlist_scan_prompt.md.backup.*`) — ruído de versão (git versiona) · backup: git · dep: não (não lidos). **DELETED 2026-06-15** — 14 snapshots intermediários abr/27-28 removidos (todos IGNORED, sem ref em código, vivos `operational_prompt.md`/`strategy_rules.json`/`watchlist_scan_prompt.md` são TRACKED no git). **PRESERVADOS como ARCHIVE_CANDIDATE** (rollback recente, decisão futura): `strategy_rules.backup_20260518_130015.json` (79K) + `strategy_rules.json.backup.20260521-cleanup` (80K).
- **Pine alerts não-XAU** (`pine_alerts/02,03,04,06,07,08,09*.pine`) + **`05_body60`** — legacy/rejeitado fora do core · backup: arquivar · dep: verificar alerta TV ativo · ação: arquivar→delete.
- **`bars_US500_30.json`** (root, untracked) — órfão · **DELETED 2026-06-14** (untracked; SHA256 pré-delete `0da04072792ac69856a417853eb7156a1519656a14e8b70b44b70c3345f45ba0`; zero dependência de produção; era citado só neste register).
- **`backups/screenshots_archive` (7.5M), `backups/bak_archive` (5.5M)** — possivelmente obsoletos · backup: é backup · dep: não · ação: amostrar→decidir.
- **Blocos stale de config** (`strategy_rules.json` BODY60 "active" ~530, rejection-execution replacement ~408) — config morta · backup: git · dep: lido como JSON ref · ação: patch governança 1-a-1 (NÃO nesta fase).

## 6. REVIEW_LATER Register

- **XAU 1H LONG** (Demand/Reclaim/Reentry; memória + `candidates/xauusd_*_pending.md` + `/tmp/xau_*`) — razão: exceção explícita; promissor, precisa rebuild RAW · risco: perder features fortes (drop_20_atr, BE@2R) · ação: **preservar integralmente**; revisão futura RAW-first · autorização: SIM (não destruir).
- **XAU 4H Breakout Continuation D1a** (`pine_alerts/01*.pine` + `revalidation/.../v1/`; `claude_recheck.py:931` "Módulo ATIVO") — UNKNOWN_NEEDS_AUDIT · RAW-traced mas anterior ao core; rota recheck stale · risco: emitir SETUP_VALIDO se canal voltar · ação: **remover rota técnica**, depois decidir REVIEW_LATER vs ELIMINATE · autorização: SIM.
- **Regime Classifier B v3** (`candidates/regime_classifier_v3/`) — NEEDS_AUDIT · OHLC+MA (não pine_boxes) mas bias residual 10.68% · risco: reusar com look-ahead · ação: SHIFT1 audit antes de qualquer reuso · autorização: SIM.
- **Catálogo 30 hipóteses** (19 não testadas: DXY/FOMC/1H stabilization) — REVIEW_LATER (IDEA_ONLY) · features ortogonais candidatas · risco: esquecer · ação: fila de pesquisa RAW-first · autorização: não (só pesquisa).

## 7. Strategy Boundary (todas as estratégias → balde)

- **FUTURE_CORE_CANDIDATE:** XAU 4H LONG layer stack (L1/L2) · L2-BPT RAW chain.
- **REVIEW_LATER:** XAU 1H LONG (exceção) · Breakout Continuation D1a (NEEDS_AUDIT).
- **QUARANTINE:** Caminho A antigo · Caminho B antigo · Auction labs antigos · Capitulation (após remover rota) · Demand Breakout (após remover rota) · Reversal Discretionary (após remover rota) · FAMILY_A BigBeluga (remover injeção recheck).
- **DELETE_CANDIDATE (após segurança):** Body60 1H · 9 Pine não-XAU · legacy rejection swing 4H · 1H rejection execution.
- Regra reafirmada: nenhuma estratégia antiga valida-se; só features/processos via `LEGACY_KNOWLEDGE_REGISTER`.

## 8. Data / Logs / Archived Alerts Boundary

- **SOURCE_OF_TRUTH (FUTURE_CORE):** RAW replay · manifests/SHA · dataset_registry.
- **FUTURE_CORE (event store):** `indicator_signals.jsonl` (journal, RAW-linkável: ts_signal/symbol/base_symbol/alert_type/timeframe/price/signal_hash) · `tradingview_alerts.jsonl` (confirmar normalização).
- **USEFUL_EVENT_HISTORY (não validação):** journal acima + `outcomes_current.jsonl` (72 CLEAN) + `schema_warnings`/`watchlist_rejections`/`deprecated_alert_types_counter`. Uso: event mining, frequência, sessão, sequência, qualidade vs RAW — só após normalização+RAW-match+tag.
- **QUARANTINE (contaminado mas útil):** outcomes pré-pepperstone (330) · `strategy_eval_log`/`setup_*_log`/`d2r_*` (dependem de outcomes contaminados) · `backups/legacy_logs`.
- **Regra:** archived alerts são histórico de candidatos/eventos, NUNCA verdade de validação.
- **PDFs** em `~/Desktop/TRADING/` = planos de trading/specs legítimos → **KEEP_AS_REFERENCE** (não quarentena; nenhum PDF de premissa inválida achado no repo).

## 9. Production Component Boundary (estado live vs balde)

- **FUTURE_CORE / ATIVO:** receiver (PID 841) · cloudflared (PID 1033) · claude_recheck (spawn, REBUILD_CLEAN) · external-factors-heartbeat (PID 855, KEEP_BUT_SIMPLIFY) · weekly-review/archive-weekly (agendados, KEEP).
- **REVIEW/NEEDS_AUDIT:** d2r-daily (LOADED live mas doc diz PAUSED — reconciliar) · monitor XAU daemon/cron (UNLOADED live mas doc diz loaded — reconciliar; reativável controla chart).
- **DECOMMISSIONED (quarantine):** enrich-indicator-outcomes (plist arquivado).
- **Não tocar sem autorização:** todos os LaunchAgents, receiver, cloudflared, claude_recheck, strategy_rules.json, operational_prompt.md, monitor (mesmo dormente), .env, RAW externo, logs ativos.
- **pause flag** `/tmp/claude_recheck.paused` presente.

## 10. Commercialization & Automation Blockers

1. Status fragmentation (sem fonte única) — bloqueia escala/governança.
2. Estratégias REJECTED tecnicamente alcançáveis (Demand Breakout loop; recheck:931 SETUP_VALIDO) — só protegidas por canal dormente.
3. Código dormente reativável (daemon XAU controla chart via CDP).
4. Divergência live↔doc (daemon / d2r-daily / external-factors).
5. Dados contaminados misturados com válidos (SLIM + outcomes pré-fix perto de RAW/clean).
6. Camada outcome antiga decommissionada sem substituto produtivo.
7. Chart/MCP coupling (chart-lock não unificado).
8. Backups/prompt duplicados (10+) = ruído/risco de editar errado.
9. Governança incompleta (MASTER 04/07/09 + SKILL ausentes).
10. Absolute-path frágil (10 plists hardcoded).

## 11. Next Smallest Safe Action

**Proposta (sem executar; só marcação ou read-only):** **reconciliação docs↔live** das 3 divergências de produção (daemon XAU, d2r-daily, external-factors) num único anexo read-only — porque qualquer movimento de re-arquitetura (remover rota técnica, simplificar receiver, unificar status) depende de saber o **estado real vs documentado** de cada LaunchAgent. Zero mudança; alinha o mapa antes de qualquer ação destrutiva.

Não fazer agora: nenhum delete (só registrado como candidato) · nenhuma remoção de rota técnica · nenhum refactor amplo · nenhum patch de config. Cada uma dessas é fase seguinte com autorização própria.

**Boundary Rule final:** este arquivo define a fronteira, não autoriza execução. Toda transição de balde (especialmente DELETE_CANDIDATE→delete e remoção de rota técnica de estratégias QUARANTINE) exige inventário + backup/checksum quando aplicável + **aprovação explícita do Cris**.

## 12. Candidates/ Directory Classification (refinada 2026-06-14)

Inventário read-only dos 4 diretórios `my-strategy/strategies/candidates/` (todos **untracked**; nenhum deletado/movido/versionado nesta etapa).

1. **`candidates/regime_classifier_v3/`** (2.6M) — **REVIEW_LATER / NEEDS_SHIFT1_AUDIT.** Útil como input de regime (BULL/TRANSITION/BEAR, macro_broken); usa OHLC/MA (não SLIM/pine_boxes), MAS tem bias residual/look-ahead reportado (~10.68%). Não pode validar core antes de audit ORIG-vs-SHIFT1. É o input do gate L2.
2. **`candidates/xau_4h_caminho_b_long/`** (1.5M) — **QUARANTINE.** Caminho B antigo contaminado por SLIM/proxy (slim inflava ~10×); lições preservadas em `LEGACY_KNOWLEDGE_REGISTER.md`; não validar.
3. **`candidates/xau_4h_reversal_v1_4g_rws_a6/`** (2.0M) — **QUARANTINE / SUPERSEDED.** Caminho A antigo, contaminado/superseded por a6_a7; manter só como histórico até decisão futura.
4. **`candidates/xau_4h_reversal_v1_4g_rws_a6_a7/`** (180K, 1 arq) — **PROTECTED_REFERENCE / CORE_CANDIDATE_INPUT / NEEDS_LOOKAHEAD_AUDIT.** É a ponte usada pelo XAU 4H LONG / L2-BPT, mas o detector base ainda precisa audit de look-ahead antes de virar core real. **NÃO chamar de FUTURE_CORE ainda.**

**Nota:** nenhum candidate directory deve ser deletado, movido ou promovido sem etapa própria. O próximo passo técnico para `a6_a7` é **audit de look-ahead/SHIFT1**, NÃO promoção.

## 13. Reusable Legacy Primitives — REUSE map (2026-06-15)

Extração de **valor funcional** do legacy (não migração de código). O quê presta para o core novo, sem carregar o monólito. Nenhum código movido/alterado; arquivos centrais intactos.

**REUSE_NOW** (seguro, simples; já em uso ou portável trivial):
- `append_jsonl(path, obj)` (`monitor:628`) — writer JSONL append-only. Já reusado em `journal.py`/`outcome.py`.
- `_compute_signal_hash` (`receiver:1405`, sha256[:16] de chave canônica) + `event_id` pattern (`receiver:1184`, `{received_at}_{symbol}_{tf}_{alert_type}`) — id estável de sinal/evento.
- **Lição catalog:** 2 eixos ortogonais `validation_status` (metodológico) vs `deployment_status` (operacional) — já refletido em L1 `STRATEGY.md`. Campos úteis de metadata: id/archetype/symbol/tf/direction/validation/deployment/requires_human_decision.
- Padrão `/health` (ok + secret_configured sem expor segredo) — observabilidade do core novo.

**REUSE_LATER** (só quando Production v2 runtime existir):
- `_normalize_indicator_parsed` + `ALLOWED_PROVIDER` whitelist HARD GATE (`receiver:1437/1454`) — símbolo → `PEPPERSTONE:<BASE>` com whitelist; rejeita não-autorizado (não inventa autorização).
- quarantine pattern (`_write_indicator_quarantine`, `receiver:1543`) — rejeitar-para-log-de-auditoria em vez de drop silencioso.
- dedup idempotente (`_load/_persist_indicator_dedup_set`, `receiver:1415/1429`) — ingestão sem duplicar.
- `send_telegram` + `fmt_*` (`monitor:117/585-628`) — como **renderers de DRAFT** (já conceito em `telegram_draft.py`); envio live só via permissão do Registry.
- `acquire/release_chart_lock`, `get_macro_events_check` (`monitor`) — só se o core novo dirigir chart/macro (não no headless atual).

**KEEP_REFERENCE:**
- Vocabulário de rejection reasons do recheck: `NO_TRADE`, `RR_BELOW_2`, `ENTRY_LATE_CHASING`, `FALLING_KNIFE`, `ASSET_DIRECTION_BLOCKED`, `NO_OBJECTIVE_TRIGGER` — boa taxonomia para human-review/journal `reason`.
- Linguagem de risco universal em `strategy_rules.json`: `min_risk_reward`, `target_risk_reward_range`, `human_confirmation_required`, `accepted_price_structures`, `risk_per_trade_guidance`.
- 4 specs de governança (Registry/Module Contract/Notification/Outcome) — espinha de design; extrair conceito mínimo, **não** construir framework pesado agora.
- Signal Outcome Lab (`outcomes_current.jsonl` CLEAN) — seed do outcome engine.

**MIGRATE_CAREFULLY** (valor existe, mas acoplado — extrair como módulo puro, sem trazer o acoplamento):
- normalização+whitelist+quarantine (acoplada a globals/logs do receiver).
- `fmt_*` (acoplados ao shape do `state` do monitor) — re-derivar limpo p/ o schema do candidato novo.
- hard gates (vivem como texto no prompt do recheck) — re-expressar como **regras de código explícitas** no core novo, NÃO como prompt de LLM.

**DO_NOT_REUSE** (contaminam o core novo):
- `strategy_rules.json` monólito como fonte runtime.
- auto-promotion / `SETUP_VALIDO` automático do recheck (neutralizado).
- prompt monolítico / classificação por LLM do recheck.
- dispatch automático por match (loop do daemon do monitor) — substituído por allowlist default-deny + revisão humana.
- status antigos do `catalog.json` como fonte runtime; estratégias contaminadas.
- daemon loop + acoplamento chart/MCP.
