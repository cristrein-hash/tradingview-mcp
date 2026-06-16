# L1 · EMA21 CONTINUATION — módulo offline

Parte da suite **XAU 4H LONG — CONTINUATION**. Status: **governance USER_APPROVED_FINAL · HUMAN_DISCRETIONARY · CONTINUATION** · **evidence NOT_VALIDATED_OOS**.
Ver `STRATEGY.md` (banner de RECLASSIFICAÇÃO 2026-06-16 = fonte canônica; regra + métricas) e `MANIFEST.md` (proveniência).
> ⚠️ Números antigos = in-sample/research (não edge). Regime **unificado** (2026-06-16): scanner + runtime usam `regime_l1_v4`. Re-derivação sob regime live: 38/38 preservados + 25 novos candidatos → números antigos não representam o regime live; seguem research até RAW OOS. Gate é **RSI-only** (leg vol removido). Ver banner em `STRATEGY.md`.

## O que é
Estratégia de **continuação de alta no XAUUSD 4H**, dentro de tendência estabelecida (EMA21/SMA50,
regime D-1 BULL, BOS, zona de demanda Custom OB, F5 volume calmo). Um **scanner** gera o candidato base
e aplica o **gate de exaustão automático `rsi_vs_ma <= -9.35`** (RSI-only; o leg de volume foi REMOVIDO
2026-06-15 — ver STRATEGY.md). Se o gate dispara → `state=blocked_exhaustion`, **não-operacional**, sem
notificação. Se não dispara → candidato **operacional** → notificação Telegram imediata. **A revisão
humana filtra só a ENTRADA**, nunca o gate nem o sinal.

## Fluxo (scanner com gate + notifier real)
```
scanner.py (base + RSI gate)  →  [operacional?]  →  telegram_notify.py (candidate notification, allowlist L1)
                                       ↓ humano revisa chart e decide ENTRADA
                                  journal.py (signal_emitted + human_review_decision)  →  outcome.py (R post-hoc)
```
- **`telegram_notify.py`** envia a notificação real (allowlist = `L1_EMA21_CONTINUATION`; default dry-run; `--send` envia; só candidato `operational`). Mensagem = "CANDIDATE — revise o chart", **nunca** ordem de entrada.
- **`telegram_draft.py`** = render offline (não envia). `outcome.py` mede THEORETICAL/REAL.

## Runtime híbrido XAU-only (Production v2)
`runtime_xau.py` lê o chart XAU 4H via MCP (`my-strategy/core/tv_read_adapter.py`, **read-only, nunca dirige o chart**), aplica o gate, e dispara candidate notification só para candidato OPERACIONAL. Grupos em `my-strategy/core/group_model_xau.py`: **XAU_240 ativo** (consumidor L1); **XAU_60 / XAU_15 RESERVADOS** (preparação multi-TF; sem estratégia aprovada, sem Telegram). XAU-only — sem multi-ativo.
- Modos: `--once` · default **dry-run** · `--send-telegram` (opt-in real) · `--dedup-path` (1 envio por `signal_hash`).
- **Autoridade do gate-base = scanner** (RAW). O runtime orquestra (regime/precondição, dedup, journal, notify) — não duplica a regra.
- 🔴 **Dependência pendente p/ emissão LIVE:** o runtime usa **regime D-1 = `regime_l1_v4`** (fresco via `refresh_regime_l1_v4.py`; o `regime_B_v3` citado em versões antigas está morto). Além disso, o runtime **ainda não confirma a base-rule estrutural completa (EMA/SMA/BOS/OB/F5) ao vivo** → marca `needs_base_confirmation` e **não emite `operational_candidate`**. Regime atual BEAR → `no_candidate` (honesto, sem Telegram). **Emitir candidato operacional ao vivo exige (1) regime BULL e (2) confirmação da base-rule live (próximo bloco técnico).**
- Sem scheduler/daemon/LaunchAgent/broker/MCP-de-gestão neste estágio.

### Fluxo de sinal imediato (alvo, ativação futura autorizada)
O sinal Telegram deve ser **imediato quando o candidato/alarm é emitido** — é uma
**notificação de candidato** ("revise o chart"), NÃO uma ordem de entrada. A **revisão
humana filtra a ENTRADA, não o envio do sinal**. Hoje tudo é draft (`telegram_allowed:false`);
o envio real será ativado só em fase futura autorizada.

O journal tem **dois eventos append-only ligados pelo mesmo `signal_hash`** (nunca mutados):
1. `signal_emitted` — candidato gerado/notificado (signal_generated=true, signal_sent=false, signal_channel=TELEGRAM_DRAFT).
2. `human_review_decision` — KEEP/BLOCK + `entry_taken` (a entrada real é registrada aqui, separada).

`signal_hash` é gerado pelo scanner e propagado: candidato → notificação → decisão → outcome.

**Identidade canônica (signal_hash vs ingestion_hash):**
- **`signal_hash`** = hash do **scanner/candidato estratégico** (canônico). É o que `journal`, `outcome` e `telegram_draft` usam para ligar candidato → notificação → decisão → outcome.
- **`ingestion_hash`** = hash do **`live_input_adapter`** (identidade do evento bruto recebido). Domínio separado, para gate/quarantine/dedup de ingestão — **não** substitui o `signal_hash` no pipeline L1.
- Quando o runtime live ligar `adapter → scanner`, o `signal_hash` do scanner permanece a chave canônica do pipeline; o `ingestion_hash` fica só na camada de entrada.

**Fluxo correto (alvo):**
1. Candidato/alarm **emitido** (scanner / live_input_adapter → scanner).
2. **Notificação Telegram imediata de candidato** ("L1 candidate — review chart"). *(hoje draft; ativação futura autorizada.)*
3. Humano **revisa o chart**.
4. Humano **decide a entrada** (entrar / não entrar / monitorar).
5. Journal registra `human_review_decision` (KEEP/BLOCK) e `entry_taken` true/false.
6. Outcome mede `THEORETICAL_CANDIDATE` (sem entrada) ou `REAL_MANUAL_ENTRY` (entrada real).

**Regras de princípio:**
- **Telegram signal ≠ ordem de entrada.** A notificação diz "revise", nunca "entre comprado".
- **A revisão humana filtra a ENTRADA, não o alerta** — o sinal é enviado sempre que há candidato; só a entrada é discricionária.
- `MCP_MONITORED` (acompanhamento visual) e `BROKER_AUTHORIZED` (execução via broker) são **camadas futuras permitidas com autorização** — não ativadas.
- **Nada live é ativado** neste estágio: sem Telegram real, sem receiver conectado, sem MCP/broker.

## Comandos básicos
```bash
# 1. Scanner — gera candidato (último bar do RAW, ou --at <unixts>)
python3 scanner.py
python3 scanner.py --at 1756317600

# 2. Journal — registra decisão humana (append-only; sem --journal-path = só stdout)
python3 scanner.py --at 1756317600 \
  | python3 journal.py --decision KEEP --reason "continuation clean" \
        --reviewed-by cris --journal-path ./l1_journal.jsonl

# 3. Outcome — mede R post-hoc, read-only sobre RAW (não altera o journal)
python3 outcome.py --journal-path ./l1_journal.jsonl --outcome-path ./l1_outcome.jsonl

# 4. Telegram draft — gera SÓ o texto do sinal (NÃO envia)
python3 scanner.py --at 1756317600 \
  | python3 journal.py --decision KEEP --reason "..." --reviewed-by cris \
  | python3 telegram_draft.py
```

## candidate ≠ trade (verdade operacional)
- **candidate ≠ trade** e **decisão humana ≠ entrada executada.** Um KEEP aprova o candidato; não significa que uma entrada real aconteceu.
- `entry_taken=false` (default) → KEEP é só **candidato aprovado**; outcome é **teórico/monitorado** (`THEORETICAL_CANDIDATE`, entry/stop estruturais da estratégia).
- `entry_taken=true` → houve **entrada real** (manual ou, no futuro, automatizada autorizada); outcome usa `entry_ts`/`entry_price`/`stop_price` reais (`REAL_MANUAL_ENTRY`).
- `BLOCK` → `BLOCKED_NO_OUTCOME` (nunca gera trade outcome).

### Registrar KEEP **sem** entrada (candidato aprovado)
```bash
python3 scanner.py --at <ts> | python3 journal.py --decision KEEP --reason "..." \
  --reviewed-by cris --journal-path ./l1_journal.jsonl     # entry_taken=false (default)
```
### Registrar KEEP **com** entrada real (manual)
```bash
python3 scanner.py --at <ts> | python3 journal.py --decision KEEP --reviewed-by cris \
  --entry-taken --execution-mode MANUAL \
  --entry-ts 2025-08-27T18:00:00 --entry-price 3380.5 --stop-price 3350.0 \
  --journal-path ./l1_journal.jsonl
# outcome.py distingue automaticamente teórico vs real e mede cada um.
```

## Execution / Monitoring Modes (contrato)
`execution_mode` no journal: `NONE` | `MANUAL` | `MCP_MONITORED` | `BROKER_AUTHORIZED`. **Nenhum ativa nada hoje** — são apenas registrados como verdade operacional no journal; nada é conectado/disparado silenciosamente.

- **NONE** (default) — candidato aprovado **sem entrada** (`entry_taken=false`). Outcome = `THEORETICAL_CANDIDATE` (entry/stop estruturais).
- **MANUAL** — humano entra manualmente. Journal registra `entry_ts`, `entry_price`, `stop_price`. Outcome = `REAL_MANUAL_ENTRY` (mede a entrada real).
- **MCP_MONITORED** — humano autoriza Claude/AI a **acompanhar visualmente** o trade aberto via TDW/MCP/chart. MCP é **leitura/monitoramento**, NÃO execução por si só. Journal registra `execution_mode=MCP_MONITORED` + `monitoring_mode`. **Nenhuma ação operacional automática sem autorização.** Outcome = `REAL_MANUAL_ENTRY` (a entrada continua sendo a real registrada).
- **BROKER_AUTHORIZED** — futuro Pepperstone/broker, **só com autorização explícita**. Journal registra `broker`, `broker_order_id`, `entry_price`, `stop_price`, `position_size`. **Nenhuma ordem enviada silenciosamente.**

Notas do contrato:
- **candidate ≠ trade** · **KEEP ≠ entrada executada.** `BLOCK` → `BLOCKED_NO_OUTCOME` (sem trade outcome).
- `entry_taken=true` exige no mínimo `entry_ts`+`entry_price`+`stop_price` (senão `journal.py` rejeita e nada é escrito; outcome → `REJECTED_MISSING_EXECUTION_FIELDS`).
- **Telegram = draft-only** (`telegram_allowed:false`) até autorização futura.
- O **journal é a fonte de auditoria operacional**; dados de broker futuros podem virar fonte de execução **quando autorizado**.
- **MCP/chart e broker NÃO são proibidos** — são **camadas autorizadas futuras**, hoje inertes (campos só registrados).

## O que NÃO faz (hoje)
- **Não** é live. **Não** envia Telegram (apenas rascunho; `telegram_allowed: false`).
- **Não** roda como daemon. **Não** conecta MCP/broker nem executa ordens — essas são camadas futuras autorizadas, não ativas.
- **Não** toca receiver, monitor, recheck, strategy_rules, catalog, registry, secrets.
- Tudo headless; outcome read-only sobre o RAW canônico; nenhuma escrita em produção/logs vivos.

## Próximo (fora do escopo deste módulo)
Ligar Production v2 runtime, permissão de envio via Strategy Registry, MCP monitoring autorizado e broker integration são
**frentes separadas**, cada uma com autorização explícita. Por enquanto: scanner → revisão humana → journal → outcome → draft.
