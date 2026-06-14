# NOTIFICATION POLICY — SPEC (Patch 3, design-only)

**Criado:** 2026-06-14 · **Estado:** SPEC apenas. Nenhum código, nenhuma policy ativa, nada conectado ao runtime. Terceiro pilar de governança, junto de `STRATEGY_REGISTRY_SPEC.md` e `STRATEGY_MODULE_CONTRACT_SPEC.md`.

## 1. Purpose

A **Notification Policy** é a camada **central** que decide quais saídas são permitidas para cada estratégia, **derivado do `status` no Strategy Registry**. Substitui no futuro a supressão por exceção (`NO_TELEGRAM_DISPATCH`), as regras hardcoded de Telegram e a classificação de envio espalhada entre receiver/recheck/monitor. Permissão por **desenho**, não por lista manual.

## 2. Core Rule

- Nenhuma estratégia decide sozinha se envia Telegram.
- Nenhum módulo usa lista hardcoded tipo `NO_TELEGRAM_DISPATCH`.
- A permissão vem **sempre** de: **Strategy Registry status + Notification Policy**.
- Sem grant explícito da policy para aquele status, **não existe rota**.

## 3. Allowed Outputs

- `log` — registro interno (event/decision log).
- `watch_note` — anotação interna de observação (sem Telegram).
- `telegram_review` — mensagem de revisão humana (não urgente).
- `telegram_urgent` — alerta urgente (reservado ao futuro).
- `execution` — rota para execution adapter (reservado ao futuro).

## 4. Current Phase Defaults

Nesta fase, sem exceção:
- `telegram_urgent = false` para **todos**.
- `execution = false` para **todos**.
- **Nenhuma automação de trade permitida.**

## 5. Status Matrix

Formato: status → log · watch_note · telegram_review · telegram_urgent · execution
- **RESEARCH** → log=true · watch_note=false · telegram_review=false · telegram_urgent=false · execution=false
- **WATCH_ONLY** → log=true · watch_note=true · telegram_review=false · telegram_urgent=false · execution=false
- **LIVE_REVIEW** → log=true · watch_note=true · telegram_review=true · telegram_urgent=false · execution=false
- **DISABLED** → log=true · watch_note=false · telegram_review=false · telegram_urgent=false · execution=false
- **REJECTED** → log=false (ou `historical_log_only=true`) · watch_note=false · telegram_review=false · telegram_urgent=false · execution=false
- **ARCHIVED** → log=false · watch_note=false · telegram_review=false · telegram_urgent=false · execution=false

## 6. Hard Safety Rules

- **REJECTED nunca envia Telegram.**
- **RESEARCH nunca envia Telegram live.**
- **WATCH_ONLY nunca envia Telegram review.**
- **LIVE_REVIEW** pode enviar **apenas** `telegram_review`, **nunca** `telegram_urgent`.
- **`telegram_urgent`** só pode existir em fase futura, com **aprovação explícita** + gate próprio.
- **`execution` adapter sempre disabled** nesta fase.
- A policy é **fail-closed**: status desconhecido/ausente → nenhuma saída além de `log` interno (ou nada).

## 7. Relationship With Other Specs

- `STRATEGY_MODULE_CONTRACT_SPEC.md` — o **módulo gera o sinal** (estado + gates + razões); não decide rota.
- `STRATEGY_REGISTRY_SPEC.md` + `strategy_registry.schema.json` — o **registry define o status** (fonte única).
- **Notification Policy** — **decide a saída permitida** a partir do status.

Fluxo: **Strategy Module → (signal) → Registry status → Notification Policy → saída permitida.**
Receiver/Recheck/Monitor **não** devem decidir permissões por conta própria no core futuro — apenas consultar Registry + Notification Policy.

## 8. Legacy Replacement

Esta policy substituirá no futuro:
- `NO_TELEGRAM_DISPATCH` (lista hardcoded em `monitor_xau_4h_strategies.py:52`).
- Lógica de Telegram hardcoded no monitor.
- Classificação `SETUP_VALIDO` indo direto para Telegram (`tv_webhook_receiver.py` / `claude_recheck.py`).
- Permissões de envio espalhadas em recheck/receiver (`should_send_claude_recheck_to_telegram`, caps, etc.).

## 9. Migration Note

Antes de remover a pause flag ou reativar operação (ordem obrigatória):
1. **neutralizar `recheck:931` / BREAKOUT_CONTINUATION ativo** (emitiria SETUP_VALIDO sem promoção validada);
2. **reconciliar `catalog.json` deploy** das REJECTED/RESEARCH ainda marcadas LIVE (DEMAND_BREAKOUT, CAPITULATION, DISCRETIONARY);
3. **garantir que qualquer rota futura consulte Registry + Notification Policy** (nenhuma rota fora desse caminho).

Ver auditoria de exposição 2026-06-14 em `docs/architecture/OPERATIONAL_INVENTORY.md`.

## 10. Não-objetivos desta fase

NÃO implementar a policy, NÃO popular registry, NÃO conectar a receiver/recheck/monitor, NÃO habilitar `telegram_urgent`/`execution`, NÃO tocar produção, NÃO remover pause flag.
