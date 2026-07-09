# L1 EMA21 4H LONG Continuation — REGRAS DE CAPACIDADE / RISCO / POSIÇÕES (pré-produção)

**Data:** 2026-07-09 · **Status:** `FROZEN_PROPOSAL_NOT_WIRED` · **Produção:** `NOT_AUTHORIZED`

Regras congeladas ANTES de qualquer go-live. **Não integradas em produção** (documento; broker não conectado; execução manual). Auditadas contra o código existente, não wired.

## Regras congeladas
| parâmetro | valor | nota |
|---|---|---|
| `max_open_l1_positions` | **3** | máx. posições L1 abertas simultâneas |
| `max_same_symbol_l1_positions` | **3** | máx. no mesmo símbolo (XAUUSD) |
| `max_total_l1_open_risk` | **1.0R** | risco agregado máximo a nível de conta |
| `position_risk_mode` | `equal_split` | risco dividido igualmente pelos slots ativos |
| `each_position_risk` | **0.33R** (com 3 slots) | 3 × 0.33R = ~1.0R agregado |
| `duplicate_same_bar_signal` | **BLOCK** | 1 sinal por barra/`signal_hash` (dedup) |
| `opposite_position_hedge` | **NOT_ALLOWED_FOR_L1** | L1 é LONG-only; sem hedge |
| `broker_execution` | **MANUAL_APPROVAL_ONLY** | toda execução humana/manual-approved |
| `telegram_signal` | **HUMAN_REVIEW_ONLY** | sinal = revisão humana, não auto-ação |
| `auto_broker_execution` | **NOT_AUTHORIZED** | automação de broker proibida |

## Notas operacionais
- Pepperstone pode permitir múltiplas posições/hedging, mas **a L1 permanece LONG-only**.
- **3 posições XAUUSD = uma única exposição direcional concentrada** — o teto de 1.0R agregado reflete isso (não é 3×1R independente).
- Antes de qualquer automação de broker, **todas as execuções devem ser humanas/manual-approved**.
- O **journal deve tratar cada sinal como `trade_id` separado**, mesmo se a plataforma agregar visualmente.

## Auditoria do código existente (não alterado)
- `journal.py` já modela camadas de execução como **FUTURAS não-ativadas**: `--execution-layer` ∈ `{NONE, MANUAL, MCP_MONITORED, BROKER_AUTHORIZED}` (default **NONE**); `--broker`/`--broker-order-id` = "camada futura". Nenhuma escrita de produção ativada.
- `run_l1_cycle.py`: "nunca toca broker, nunca desenha, nunca troca símbolo".
- `runtime_xau.py`: dedup por `signal_hash` (1 envio/sinal) já implementado; `_production_authorized()` (novo) exige env explícito para envio.
- **Nada destas regras está wired a execução real.** Integração (capacity enforcement + broker) = trabalho futuro que requer autorização explícita do Cris.

## Status
`FROZEN_PROPOSAL_NOT_WIRED` — regras aprovadas como proposta congelada; **enforcement em runtime + broker = NÃO implementado, NÃO autorizado.** Qualquer wiring futuro requer autorização explícita separada.
