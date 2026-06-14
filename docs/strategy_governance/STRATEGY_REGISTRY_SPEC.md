# STRATEGY REGISTRY — SPEC (Patch 1, design-only)

**Criado:** 2026-06-14 · **Estado:** SPEC + SCHEMA apenas. Nenhuma estratégia migrada, nenhum registry populado, nada conectado ao runtime.

## 1. Objetivo

O **Strategy Registry** é a **fonte única de verdade** de status, validação e permissão de rota de cada estratégia. Toda saída operacional (log, nota, Telegram, execução) só existe se o registry conceder — permissão é **central e enforçada pelo core**, nunca por listas hardcoded ou flags espalhadas.

## 2. Por que substitui o sistema antigo

Hoje o status/permissão vive fragmentado e divergente:
- `catalog.json` (status que diverge do comportamento real: REJECTED/RESEARCH com `deploy=LIVE`),
- `claude_recheck.py` (flags `Módulo ATIVO`/`DESATIVADO`, classificação SETUP_VALIDO embutida),
- `strategy_rules.json` (monolito de regras + status),
- `monitor_xau_4h_strategies.py` (`NO_TELEGRAM_DISPATCH` hardcoded).

O Registry consolida isso num **único contrato de dados**: status + permissão de saída por estratégia, auditável, sem duplicação. Elimina estruturalmente o `recheck:931` (módulo ativo) e o `NO_TELEGRAM_DISPATCH` (supressão por exceção vira permissão por desenho).

## 3. Princípios

- **Status único** — uma estratégia tem exatamente um `status` no registry; nenhuma outra fonte decide.
- **Permissão central** — nenhuma rota existe sem grant explícito derivado do status.
- **Rejeitada nunca emite** — `REJECTED`/`ARCHIVED`/`DISABLED` não têm rota de Telegram nem execução, por construção.
- **Research nunca envia Telegram live** — `RESEARCH`/`WATCH_ONLY` no máximo logam/anotam; nunca Telegram review/urgent.
- **Execução sempre desabilitada nesta fase** — `execution=false` para todos, sem exceção.

## 4. Status model

- **RESEARCH** — em estudo; só log/dashboard.
- **WATCH_ONLY** — observação; log + nota interna; sem Telegram.
- **LIVE_REVIEW** — operável por revisão humana; Telegram review (não urgente).
- **DISABLED** — desligada (silenciosa); só log.
- **REJECTED** — refutada; histórico; sem rota.
- **ARCHIVED** — fora do core; sem log nem rota.

## 5. Output permissions

`log` · `watch_note` · `telegram_review` · `telegram_urgent` · `execution`.

Matriz status → permissões:
- RESEARCH → log
- WATCH_ONLY → log, watch_note
- LIVE_REVIEW → log, watch_note, telegram_review
- DISABLED → log
- REJECTED → log
- ARCHIVED → (nenhuma)

**Regra fixa desta fase:** `telegram_urgent = false` e `execution = false` para **TODOS** os status (reservados ao futuro, com gate próprio). Nenhuma estratégia pode executar trade.

## 6. Relacionamento com outros componentes

- **Strategy Module Contract** — o módulo da estratégia (gates/entry/exit/risk) referencia o registry via `status` (status não vive no módulo). O registry aponta para o módulo via `strategy_module_ref`.
- **Notification Policy** — consome o `status` + `notification_permissions` do registry para decidir saída; substitui `NO_TELEGRAM_DISPATCH` e a lógica de send espalhada no receiver.
- **Outcome Engine** — usa `outcome_spec_ref` para medir resultado pós-sinal; desacoplado da emissão.
- **Legacy catalog** — `catalog.json` é **input histórico**, não fonte final. O registry nasce em paralelo, importa só o que for aprovado.

## 7. Migration rule

- O `catalog.json` atual é **input histórico**, não fonte de verdade do registry.
- **Nenhuma estratégia migra sem audit** (validação RAW-first + lookahead).
- **XAU 4H LONG / a6_a7** (único candidato a core) ainda precisa de **lookahead audit** antes de qualquer migração (`lookahead_audit_status = PENDING`).
- **`recheck:931` / BREAKOUT_CONTINUATION ativo deve ser neutralizado** antes de qualquer retomada operacional (ver auditoria de exposição 2026-06-14 em `OPERATIONAL_INVENTORY.md`).
- Nada do registry conecta ao runtime nesta fase; pause flag + daemon dormant permanecem como estão.

## 8. Não-objetivos desta fase

NÃO popular registry, NÃO migrar estratégia, NÃO conectar ao receiver/recheck/monitor, NÃO tocar produção, NÃO habilitar `telegram_urgent`/`execution`.
