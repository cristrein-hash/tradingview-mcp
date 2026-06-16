# FORWARD OUTCOME LAYER — SPEC (2026-06-16, design-only)

**Estado:** SPEC apenas. Nenhum código operacional, nada conectado ao runtime, nada agendado.
Substitui **conceitualmente** o D2R legacy (live signal → R realizado) **sem copiar a implementação**.

## 0. Propósito (uma frase)
Transformar **eventos live + candidatos da L1** em **evidência forward mensurável** e comparável ao backtest (RAW), para medir o **gap edge-histórico vs operação-real** — **sem** validar edge sozinha, **sem** gerar ordem, **sem** enviar Telegram de trade.

## 1. Perguntas que a camada responde
1. O que aconteceu após um sinal live? 2. O sinal existia como candidato equivalente no backtest? 3. Payload completo/fiel? 4. Chegou no tempo certo? 5. Geraria trade se operado? 6. Humano bloquearia/aprovaria? 7. Qual R posterior sob SL/TP definidos? 8. Forward-R confirma/diverge/contradiz backtest-R? 9. Revela problema de estratégia/indicador/alerta/dedup/regime/timing/humano? 10. Deve virar hipótese futura?

## 2. Hard-stop preconditions (verificadas 2026-06-16, todas PASS)
event store vivo (16.1M, última 2026-06-16T07:15, schema_v1.0, signal_hash) · receiver vivo (PID 841) · D2R dormant (não escreve) · `outcome.py` read-only por default · sem secrets versionados · broker inativo · signal_hash canônico no fluxo. **Se qualquer uma falhar no futuro → parar e reportar antes de implementar.**

## A. Entidades
- **RawIndicatorSignal** — evento bruto do receiver (`indicator_signals.jsonl`): ts_signal, base_symbol, timeframe, indicator_name, signal_type, price, signal_hash(do receiver), payload_full.
- **StrategyCandidate** — saída do scanner L1: candidate/operational/exhaustion_gate/state/signal_hash(estratégico)/rsi_vs_ma.
- **CandidateNotification** — evento `signal_emitted` (journal): signal_sent, signal_channel, telegram_allowed.
- **HumanReviewDecision** — `human_review_decision` (journal): KEEP/BLOCK, reason, reviewed_by.
- **EntryObservation** — entry_taken + entry_ts/price/stop/execution_mode (journal).
- **ForwardOutcome** — R realizado posterior do sinal/candidato, calculado read-only sobre RAW/forward (THEORETICAL ou REAL).
- **BacktestOutcome** — R esperado do candidato equivalente no backtest (RAW).
- **OutcomeComparison** — forward-R vs backtest-R (agree/diverge + dimensão da divergência).
- **SignalQualityIssue** — payload incompleto, latência, repaint, duplicata, quarantine, campo ausente.
- **ForwardHypothesis** — padrão observado no live (cluster/recorrência/falso-positivo) marcado p/ validação futura em RAW.

## B. Identidades (regra dura)
- **ingestion_hash** = identidade do evento bruto (receiver/input-layer; dedup de ingestão).
- **signal_hash** = identidade canônica do **candidato estratégico** (liga estratégia ↔ candidato ↔ Telegram ↔ journal ↔ outcome).
- **outcome_id** = outcome calculado. **review_id** = decisão humana. **comparison_id** = forward vs backtest.
- **`ingestion_hash` NUNCA substitui `signal_hash`.** Evento live sem estratégia aprovada → pode gerar **hipótese**, nunca trade signal.

## C. Estados
`raw_signal_received` · `raw_signal_quarantined` · `candidate_matched` · `candidate_unmatched` · `candidate_emitted` · `candidate_notified` · `human_review_pending` · `human_keep` · `human_block` · `entry_taken` · `entry_not_taken` · `forward_outcome_pending` · `forward_outcome_ready` · `forward_agrees_backtest` · `forward_diverges_timing` · `forward_diverges_payload` · `forward_diverges_outcome` · `hypothesis_only` · `invalid_signal` · `stale_context` · `missing_raw_for_outcome`.

## D. Métricas
Contagens: live signal · candidate · candidate/live match rate · payload completeness rate · latency estimate · duplicate rate · quarantine rate · operational_candidate rate · blocked_exhaustion rate · regime-block rate · Telegram sent · Telegram dedup skip · human keep/block rate · entry_taken rate.
Outcome: forward R distribution · forward-vs-backtest agreement · false-positive clusters · hypothesis clusters · missing-negative flag · data-quality errors.

## E. O que a camada NÃO faz
Não valida edge sozinha · não substitui RAW backtest · não gera ordem · não recomenda entrada · não envia Telegram de trade · não altera receiver/event store · não modifica `indicator_signals.jsonl` · não limpa dados · não reativa D2R legacy · não mistura canal de manutenção com canal de sinal.

## F. Saídas futuras (em `my-strategy/core/forward_outcome/`)
`forward_outcomes.jsonl` · `forward_signal_quality.jsonl` · `forward_hypotheses.jsonl` · `forward_outcome_summary.md` · (futuro) relatório periódico em **canal de manutenção separado** · manifest/checksum por run.

## G. Módulos futuros (NÃO implementar agora)
`my-strategy/core/forward_outcome/` (consistente com `core/regime_l1`, `core/regime`):
- `ingest_live_signals.py` — lê `indicator_signals.jsonl` read-only, normaliza, filtra XAU.
- `match_candidates.py` — junta RawIndicatorSignal ↔ StrategyCandidate (por bar/ts/símbolo); marca matched/unmatched.
- `compute_forward_outcomes.py` — R realizado read-only sobre RAW (reusa a exit policy do `outcome.py`).
- `compare_backtest_forward.py` — OutcomeComparison (agree/diverge + dimensão).
- `report_forward_quality.py` — métricas D + summary.md (sem Telegram).
- `README.md`.

## H. Política de fontes (nenhuma sobrescreve a outra)
RAW/source = backtest + outcome histórico (read-only) · Live event store = comportamento operacional real (read-only) · Journal = decisão humana + entry_taken · Runtime state = dedup/runs · Telegram = delivery/notification. **A camada só LÊ; escreve apenas seus próprios `forward_*` outputs.**

## I. Relação com a nova L1
Lê: candidate emissions (journal `signal_emitted`), `human_review_decision`, `outcome.py` (quando aplicável), dedup (`.runtime_state/`). Mede: se `signal_hash` teve Telegram, se houve decisão humana, R posterior (THEORETICAL se sem entrada; REAL se entry_taken), e compara com backtest quando houver referência. **Observa, não interfere.**

## J. Alarmes legacy — classificação para esta camada
- Ingestão `indicator_signals.jsonl` → **KEEP_AS_FORWARD_DATA**.
- Sinais de indicadores sem estratégia aprovada → **HYPOTHESIS_GENERATION_ONLY**.
- Sinais fora do escopo XAU L1 → **IGNORE_FOR_TRADING** (podem servir QUALITY_MONITOR_ONLY).
- recheck→SETUP_VALIDO→Telegram (trade) → **DECOMMISSION_CANDIDATE** (já neutralizado).
- **Regra:** alarme legacy pode gerar hipótese/evidência forward, **nunca** trade sem passar pela nova arquitetura + RAW validation.

## K. Relação com D2R
- D2R legacy = **implementação arquivável** (não reativar, não copiar).
- D2R **concept** = esta camada (live signal → R; outcome posterior; divergência; resumo por estratégia/sinal).
- **Reaproveitar conceito:** ligação sinal→R, outcome posterior, divergência, summary. **Não reaproveitar:** dependências legacy, logs stale, Telegram antigo, qualquer path de sinal operacional antigo.

## L. Retenção
Event store vivo ≥ 30–90 dias (não apagar) · RAW/manifests nunca apagar · `forward_*` outputs nunca apagar (append + manifest) · eventual compressão/arquivamento com manifest · logs operacionais com rotação.

## M. Riscos
cherry-picking · survivorship bias · **missing negatives** (event store loga o que disparou, não o que deveria) · indicator version drift · live payload drift · timezone/alignment (4H DST — já tratado no scheduler) · repaint · duplicate signals · human review bias · **conflating signal with strategy** · overfitting em amostra forward curta. **Mitigação central:** forward = evidência/hipótese; **edge só se valida em RAW**.

## N. Decisão de design
- **A camada deve existir? SIM** — preenche um gap real (forward outcome / gap edge↔operação) que o `outcome.py` atual não cobre (ele mede candidato L1 post-hoc sobre RAW; não junta o event store live).
- **Prioridade: MÉDIA** — só faz sentido depois que a L1 acumular candidatos/sinais forward reais (regime atual BEAR → poucos candidatos). Não há urgência.
- **Versão inicial: XAU-only, read-only, sem scheduler.**
- **Primeiro MVP:** ver ROADMAP — começar por `report_forward_quality` (métricas D sobre o event store XAU + journal L1), o mais barato e seguro, sem cálculo de R.
- **Hard stops antes de implementar:** os da seção 2 + ter ≥ N candidatos L1 forward reais para medir (senão a camada roda vazia).
