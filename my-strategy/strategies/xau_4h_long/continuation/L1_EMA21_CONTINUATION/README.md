# L1 · EMA21 CONTINUATION — módulo offline

Parte da suite **XAU 4H LONG — CONTINUATION**. Status: **USER_APPROVED_FINAL · HUMAN_DISCRETIONARY · CONTINUATION**.
Ver `STRATEGY.md` (regra + métricas) e `MANIFEST.md` (proveniência).

## O que é
Estratégia de **continuação de alta no XAUUSD 4H**, dentro de tendência estabelecida (EMA21/SMA50,
regime D-1 BULL, BOS, zona de demanda Custom OB, F5 volume calmo). Um **scanner** gera o candidato;
a **decisão final é humana**. O filtro `vol_entry_z≥1.993 OR rsi_vs_ma≤−9.35` sinaliza **exaustão**
(BLOCK/REVIEW), confirmado visualmente. **Não é mecânica total, não é automação.**

## Fluxo mínimo (offline, headless)
```
scanner.py  →  journal.py  →  outcome.py  →  telegram_draft.py
(candidato)    (KEEP/BLOCK)    (R post-hoc)    (rascunho, NÃO envia)
```

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
