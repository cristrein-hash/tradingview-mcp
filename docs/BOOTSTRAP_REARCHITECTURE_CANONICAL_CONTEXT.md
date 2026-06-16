# BOOTSTRAP — CONTEXTO CANÔNICO DA RE-ARQUITETURA (TRADING SYSTEM)

**Gerado:** 2026-06-16 · **Propósito:** permitir continuar o projeto mesmo após compactação total da conversa.
**Verificado contra:** repo (git log/status), código-fonte do novo core, `launchctl list`, receiver `/health`, event store, logs de runtime/D2R.
**Natureza deste doc:** estado canônico read-only. Onde docs divergem do sistema real, a **verdade canônica é o sistema + git** (ver §DIVERGÊNCIAS).

---

## 0. ONDE VIVE A AUTORIDADE
- **Docs de autoridade GPT (`00_*`…`10_*`) e skills (`SKILL_01`…`SKILL_07`, `09_SKILLS_INDEX`)** NÃO estão no repo. Vivem em `~/Desktop/TRADING/GPT_ trading_system_project_core_md_v1/` (+ subpasta `GPT.MD/` e `trading_system_project_skills_md_v1/`). São referência externa, não versionada. Aplicar silenciosamente (§13).
- **Memória canônica do assistente:** `~/.claude/projects/-Users-cristrein-tradingview-mcp/memory/` — ler `MEMORY.md`, `PRINCIPAL_1`, `PRINCIPAL_2` no início de sessão.
- **Estado operacional repo-side:** `docs/architecture/OPERATIONAL_INVENTORY.md`, este doc, e os docs L1 abaixo.

## 1. PRIMEIRA ESTRATÉGIA NOVA — STATUS (CONFIRMADO)
Única estratégia aprovada e operacional na nova arquitetura:
**XAU 4H LONG — CONTINUATION / L1 · EMA21 CONTINUATION** · `PEPPERSTONE:XAUUSD` · 4H/240 · LONG · `group_id: XAU_240`.
- **XAU_60 / XAU_15** = reservados, **inativos**, sem Telegram, preparação estrutural futura. **Não ligar sem autorização.**
- Por ≥3 meses: somente XAU. **Não criar multi-ativo agora.**
- Módulo: `my-strategy/strategies/xau_4h_long/continuation/L1_EMA21_CONTINUATION/` — arquivos: `STRATEGY.md`, `MANIFEST.md`, `README.md`, `OPERATING.md`, `AUDIT_CLEANUP_REPORT.md`, `scanner.py`, `runtime_xau.py`, `run_l1_cycle.py`, `journal.py`, `outcome.py`, `telegram_draft.py`, `telegram_notify.py`, `com.cristrein.xau-l1-cycle.plist`.

## 2. ARQUITETURA NOVA (modelo aprovado)
TradingView/Pine = **fonte visual/indicadores** (não decide, não envia Telegram) · MCP = **leitura controlada do chart** (não executa trade) · Python scanner/runtime = **autoridade da estratégia** · Telegram = **notificação de candidato** (não é ordem) · Humano = **decisão de entrada** · Journal/outcome = **auditoria** (manual) · Broker/Pepperstone = **inativo** · MCP trade management = **inativo**.

## 3. FLUXO OPERACIONAL ATIVO (CONFIRMADO RODANDO)
Scheduler: **`com.cristrein.xau-l1-cycle` — CARREGADO E DISPARANDO** (confirmado em `launchctl list` + runtime log: runs às 02:05Z/06:05Z = local Lisboa 03:05/07:05 no verão).
- TZ máquina = **Europe/Lisbon**. Grade local fixa o ano todo (DST-robusta): **03:05 / 07:05 / 11:05 / 15:05 / 19:05 / 23:05** (5 min pós-fechamento 4H).
- Fluxo: `LaunchAgent → run_l1_cycle.py → refresh_regime_l1_v4.py --write → runtime_xau.py --once --send-telegram → scanner/gate → Telegram SE operational_candidate → dedup por signal_hash → humano revisa chart → humano decide entrada → journal/outcome manuais`.
- Logs do ciclo: `.runtime_state/l1_cycle.log` (gitignored) · dedup `.runtime_state/l1_dedup.txt`.
- **Estado recente real (2026-06-16):** runtime OK, `refresh=already_fresh`, `state=no_candidate`, `notify_sent=false` (motivo: `não-operacional (no_candidate)`). **Correto:** regime D-1 = BEAR → sem candidato → sem Telegram. Sem stale.

## 4. REGIME CANÔNICO ATUAL — regime_L1_v4 (CONFIRMADO NO CÓDIGO)
Legacy **regime_B_v3 está MORTO como autoridade** — NÃO usar para a L1.
Operacional: **`my-strategy/core/regime_l1/regime_l1_v4.py`** · `classify(close, ma_50, ma_200, slope_20_pct, rsi_14, rsi_ma_14)`:
- **BULL** se `close>ma_200 AND (ma_50≥ma_200 OR slope_20_pct>0) AND (rsi_14≥rsi_ma_14 OR rsi_14≥50)`
- **BEAR** se `close<ma_200 AND slope_20_pct<0`
- **TRANSITION** caso contrário.
- A L1 usa **regime D-1 == BULL** (SHIFT1, close-only-causal) como gate-base de contexto.

Dados: features diárias por `core/regime/build_daily_features.py` (ma_50/ma_200=SMA; rsi_14=Wilder; rsi_ma_14=SMA(rsi,14); slope_20_pct=linreg_slope/mean*100; atr_14=Wilder).
- Histórico até 2026-05-25 + barras novas 2026-05-26→**2026-06-14** via MCP D read-only; barra incompleta excluída; manifest `xau_daily_l1v4.manifest.json` gravado; refresh incremental on-demand `refresh_regime_l1_v4.py --write`.
- **Última classificação real: 2026-06-14 = BEAR** (close 4309.28 < ma_200 4444.45, slope −0.43). Última barra diária = 2026-06-14.
- Arquivos: `xau_daily_l1v4.jsonl`, `regime_l1_v4_classifications.jsonl` (⚠️ nome real, não `classifications.jsonl`), `README.md`.
- Hard stops do refresh: nunca barra diária incompleta; validar símbolo/TF D/OHLCV/monotonicidade/sem duplicatas; restaurar chart 240.

## 5. GATE CANÔNICO DA L1 (CONFIRMADO NO CÓDIGO)
- **Volume leg REMOVIDO** (2026-06-15): `vol_entry_z>=1.993` não existe operacionalmente (matriz antiga bugada + estruturalmente morto sob F5 `vol_ratio_med50≤1.0`).
- **Gate canônico:** `exhaustion_gate = round(rsi_vs_ma, 2) <= -9.35` (`RSI_VS_MA_THR = -9.35` em `scanner.py`). Automático, não é flag, não é revisão humana, bloqueia **antes** do Telegram.
- Estados do scanner: `operational_candidate` · `blocked_exhaustion` · `no_candidate`.
- Históricos bloqueados pelo gate: #3 (−12.91), #15 (−9.35), #18 (−11.32), #32 (−12.39). Preservados: #36 (2.83), #38 (−6.62), #11 (4.42), #1 (−0.56). **#36/#38 são monumentais — devem permanecer operacionais.**
- Base-rule L1: regime BULL D-1 + close>EMA21>SMA50 + slopes + BOS + Custom OB v11 zone touch + body_pct≥0.35 + F5 vol_ratio_med50≤1.0; exit V_stair_A (BE@2R→…→+20R, time_stop 60); stop estrutural largo (R_CEIL removido).

## 6. TELEGRAM
- Sinal **só** em `operational_candidate`. Human review **não** filtra o envio (filtra só a ENTRADA).
- Mensagem deve conter: **CANDIDATE · revise chart · NÃO É ORDEM · entrada é decisão humana · signal_hash**.
- **NUNCA** pode dizer: "entre", "entrada aprovada", "trade validado", "ordem", recomendação direta. (`telegram_notify.py` tem guard de frases proibidas + allowlist L1 + dedup.)
- Telegram de manutenção = **canal separado** no futuro. Nunca misturar signal com maintenance.

## 7. IDENTIDADE DE SINAL
- **signal_hash** = identidade canônica do candidato estratégico. Liga candidate → Telegram → `signal_emitted` → `human_review_decision` → outcome. (sha256[:16] de `ts|base|tf|L1_EMA21_CONTINUATION|continuation`.)
- **ingestion_hash** = identidade de evento bruto/input-layer (entrada/quarantine/dedup bruto).
- **NUNCA substituir signal_hash por ingestion_hash** em journal/outcome/Telegram.

## 8. JOURNAL / OUTCOME
- `journal.py` distingue: candidato · decisão humana (KEEP/BLOCK) · execução real · `entry_taken` true/false. **KEEP ≠ entrada automática.**
- Campos de execução existem mas broker inativo: entry_taken, execution_mode, entry_ts, entry_price, stop_price, target_plan, position_size, execution_note, broker, broker_order_id, monitoring_mode.
- Modos outcome (`outcome.py`, read-only RAW por default): `THEORETICAL_CANDIDATE` · `REAL_MANUAL_ENTRY` · `BLOCKED_NO_OUTCOME` · `REJECTED_MISSING_EXECUTION_FIELDS`.
- Outcome automático **não** roda no scheduler. Journal/outcome permanecem **manuais** após decisão humana.

## 9. LEGACY — ESTADO ATUAL (CONFIRMADO)
- **weekly-review:** decommissionado reversível. Commit `e1fdaf1`. Plist movida (não deletada) para `backups/launchagents_archive/com.cristrein.weekly-review.plist.deprecated_2026-06-16`. **Não aparece em `launchctl list`** (✓ desativado). `OPERATIONAL_INVENTORY` atualizado. Não recarrega em login/reboot.
- **D2R / enrich:** **dormant, intocados** (sem processos; último log `auto_d2r_2026-06-14.log`). Não tocar ainda. Conceito renasce como **Forward Outcome Layer** (§16). Código legacy = referência/arquivo; não reativar.
- **Receiver / event store:** **VIVO — HARD_STOP / KEEP_AS_FORWARD_DATA.** Receiver PID **841**, `/health ok:true`, `claude_recheck:true`, `secret_configured:true`, `legacy_endpoint_enabled:false`. `indicator_signals.jsonl` = **16.1MB, fresco (último 2026-06-16T07:30Z)**, source-of-truth do comportamento live de indicadores/alertas. **Não desligar, não apagar.** Não confundir live signals com edge validation.
- **cloudflared-tunnel:** vivo (PID 1033). **archive-weekly:** carregado (retenção, inofensivo).
- **pause_flag_present: true** (estado de pausa MANTIDO — `/health` confirma). **NÃO remover** (hard stop §15).
- **RAW/source data:** verdade de backtest. Não apagar/modificar; não validar estratégia por proxy/research.
- **External Factors:** cancelado, não reativar.
- **strategy_rules / catalog / recheck / monitor legacy:** não usar na nova L1, não tocar sem autorização. Estratégias pré-XAU-4H-LONG = contaminadas/eliminadas para produção, **exceto XAU 1H LONG** (revisável depois).

## 10. LIVE SIGNALS — DECISÃO ESTRATÉGICA
- RAW/backtest valida **edge histórico**. Live event store valida **operação real** (sinal dispara? timing/latência, completude payload, repaint/alert fidelity, densidade/ruído, dedup, candidato-backtest vs sinal-real, forward evidence, comportamento humano, gap edge↔operação).
- Live signals **não validam edge sozinhos** (amostra curta, missing negatives, drift de indicador, cherry-picking). Podem gerar **hipótese + forward evidence**; hipótese precisa validar em **RAW** antes de virar estratégia.
- Detalhe: `docs/LIVE_SIGNALS_STRATEGIC_VALUE_REVIEW.md`, `docs/LEGACY_TO_NEW_CORE_STRATEGIC_REVIEW.md`.

## 11. XAU LEGACY KNOWLEDGE
Índice repo-side: **`docs/XAU_LEGACY_KNOWLEDGE_INDEX.md`** + `my-strategy/strategies/xau_legacy_preservation_audit.md`. Famílias preservadas: L1 nova (operacional), continuation antiga (superseded), DEMAND_BREAKOUT (rejected), REVERSAL_CAPITULATION (rejected, PF 0.47 RAW), SWEEP/discretionary (watch), BB (revalidation), L2/BPT/Reason Atlas (research), regime_B v1/v2/v3 (morto, arquivado `dead_regime_B_v3/`), Caminho A/B (A invalidado look-ahead; B v1.5/v1.6 oficial em memory, não migrado), XAU 1H (pausado), XAU 15M/30M (potencial).
- Preservação repo-side suficiente para arquivar legacy morto, MAS: não apagar RAW; não apagar research antes de inventário; **XAU 1H/15M/30M = KEEP_FOR_REVALIDATION**; DEMAND/CAPITULATION rejeitadas mas preservadas como conhecimento.

## 12. PLOTAGEM CANÔNICA / VISUAL REVIEW
- **Validar estrutura visual = plotar 100%** dos trades/candidatos relevantes (nunca amostragem).
- Preferência: caminho curto, simples, objetivo, seguro; sem arquitetura exagerada para tarefa simples.
- Plotagem TV = operação prática: pausar só processo chart-controlling se risco real; confirmar símbolo+timeframe; usar `PEPPERSTONE:XAUUSD`; não trocar símbolo sem autorização; não apagar/deslocar desenhos existentes sem autorização; deixar visível p/ inspeção manual; restaurar só quando autorizado/segurança exigir.
- **Não** forçar screenshots se só pediram plotagem; **não** criar pipeline screenshot/manifest sem pedido explícito (memória: nunca capturar screenshot sem ser pedido).
- Formato canônico: Long/Short Position quando aplicável + label simples com nº do trade + timestamp/ref; sem linhas improvisadas. (Convenção: `draw_xau_4h_trades.py` — long_position com stopLevel/profitLevel em **TICKS**, label `#ID`.)
- Se MCP chart tools disponíveis → leitura/plotagem controlada; se não → **hard stop honesto, não fingir que plotou**, não usar OCR como substituto ruim; helper script só após auditar read-only.

## 13. SKILLS CANÔNICAS (aplicar silenciosamente)
- **SKILL_01 Minimum Safe Execution** — fazer exatamente o pedido; menor passo reversível; parar em hard stop real; não expandir escopo.
- **SKILL_02 RAW Backtest Protocol** — RAW é fonte de verdade; nunca SLIM/proxy como validação; backtest sério = manifest + mapping RAW + predicates exatos + sanity checks.
- **SKILL_03 Visual Review / Auction Theory** — respeitar estrutura de mercado; 100% quando a decisão exige; plotagem clara/auditável.
- **SKILL_04 Strategy Governance** — nunca confiar em nome de variante; verificar gates reais; separar validação/deployment/pesquisa; nada alerta trader live sem validação no padrão novo.
- **SKILL_05 Production Safety** — não tocar produção sem autorização; cuidado com LaunchAgents/daemons/receiver/chart/Telegram/broker; pause flag preservada.
- **SKILL_06 Cleanup Governance** — arquivar antes de deletar; source-of-truth não se apaga; limpeza só se reduz risco/complexidade real.
- **SKILL_07 Prompt Discipline** — prompts completos/agregados; sem microvalidações; se seguro executar bloco fechado; se risco real, hard stop.
- Skills de projeto/MCP correlatas: `replay-backtest-manager`, `trading-system-operator`, `incident-response`, `repo-governance-cleanup`, `strategy-research-analyst`, `sequential-thinking`. Routing em CLAUDE.md.

## 14. COMMITS RECENTES (linha do tempo, confirmada em git log)
`4ac8e3f` Design forward outcome layer · `e1fdaf1` Decommission legacy weekly review LaunchAgent · `fd299be` Review strategic value of live signals · `563c644` Review legacy maintenance tools before decommission · `4f7c185` Consolidate XAU legacy knowledge index · `7f9a0ab` Audit XAU legacy strategy preservation · `10fd298` Clean up XAU L1 dead regime artifacts and rotate logs · `92421ac` Audit XAU L1 system cleanup candidates · `4010e41` Enable XAU L1 scheduled cycle · `113b3bf` Add minimal scheduled XAU L1 cycle · `4f6b611` Add on-demand L1 v4 regime refresh · `a42bf5b` Add explicit L1 v4 regime source for XAU runtime · `4382365` Document v1 B regime classifier recovery hard-stop · `d827f0d` Reconstruct canonical daily regime pipeline offline · `4ea9886` Add XAU-only MCP read runtime for L1 · `5c1b1fd` Enforce L1 RSI gate and enable candidate notification test.

## 15. HARD STOPS GERAIS (parar e reportar se a ação exigir)
broker/Pepperstone · MCP de execução/gestão de trade · strategy_rules · catalog · claude_recheck · monitor legacy · mutação RAW/v6 · remover pause flag · alterar LaunchAgents ativos sem autorização · Telegram fora do fluxo de candidato · mexer no receiver/event store · apagar research sem inventário · apagar manifests/checksums · operar multi-ativo · ativar XAU_60/XAU_15 · usar regime_B_v3 como autoridade · gerar ordem · alterar produção sem gate.

## 16. PRÓXIMA FRENTE — FORWARD OUTCOME LAYER (⚠️ JÁ DESENHADA)
**A spec já existe** (commit `4ac8e3f`): `docs/FORWARD_OUTCOME_LAYER_SPEC.md` (seções A–N) + `docs/FORWARD_OUTCOME_LAYER_ROADMAP.md` (5 fases). Substituto conceitual do D2R. Decisão: SIM, prioridade MÉDIA, XAU-only, read-only, sem scheduler, sem Telegram, sem broker, sem alterar event store, sem D2R legacy ativo.
- Entidades: RawIndicatorSignal, StrategyCandidate, CandidateNotification, HumanReviewDecision, EntryObservation, ForwardOutcome, BacktestOutcome, OutcomeComparison, SignalQualityIssue, ForwardHypothesis.
- Identidades: ingestion_hash, signal_hash, outcome_id, review_id, comparison_id.
- Outputs futuros: forward_outcomes.jsonl, forward_signal_quality.jsonl, forward_hypotheses.jsonl, manifest/checksum, digest de manutenção em canal separado.
- Módulo futuro (não criado): `my-strategy/core/forward_outcome/`. MVP = Fase 1 `report_forward_quality` (qualidade, sem R).
- **Não implementar código ainda** sem autorização explícita por fase.

---

## DIVERGÊNCIAS ENCONTRADAS (reportar)
1. **OPERATING.md §Scheduler está STALE.** Diz "⚠️ NÃO CARREGADO (template)", mas o scheduler **está carregado e disparando** (`launchctl list` mostra `com.cristrein.xau-l1-cycle`; runtime log tem runs 02:05Z/06:05Z; plist já tem header Lisbon DST-robusta 2026-06-16; commit `4010e41 Enable XAU L1 scheduled cycle`). **Verdade canônica = ATIVO.** Recomendado: atualizar OPERATING.md §Scheduler em bloco futuro.
2. **Docs de autoridade `00-10` + `SKILL_0x` não estão no repo** — vivem em `~/Desktop/TRADING/GPT_ trading_system_project_core_md_v1/`. Não é erro; é referência externa. Considerar versionar/linkar se quiser blindagem repo-side.
3. **Forward Outcome Layer já desenhada** (§16) — a "próxima frente desejada" do pedido de bootstrap já foi entregue no commit anterior.
4. **Nome de arquivo:** o classifications é `regime_l1_v4_classifications.jsonl` (não `classifications.jsonl` como citado no pedido).

## VERIFICAÇÃO DE ESTADO (snapshot 2026-06-16)
| Item | Estado |
|---|---|
| Scheduler `xau-l1-cycle` | **CARREGADO e disparando** (Lisbon grid); estado atual `no_candidate` (BEAR) |
| `weekly-review` | **DECOMMISSIONADO** (fora do launchctl; plist arquivada) |
| Receiver | **VIVO** PID 841, /health ok |
| Event store `indicator_signals.jsonl` | **VIVO** 16.1MB, último 2026-06-16T07:30Z |
| cloudflared-tunnel | vivo PID 1033 |
| D2R / enrich | **dormant** (sem processo; último log 06-14) |
| pause flag | **presente (mantido)** — não remover |
| regime_L1_v4 último | **2026-06-14 = BEAR** |
| Broker / MCP-exec | **inativo** |
