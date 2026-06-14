# STRATEGY MODULE CONTRACT — SPEC (Patch 2, design-only)

**Criado:** 2026-06-14 · **Estado:** SPEC apenas. Nenhum código, nenhum módulo implementado, nenhuma estratégia migrada, nada conectado ao runtime. Irmão de `STRATEGY_REGISTRY_SPEC.md`.

## 1. Purpose

Este contrato define a **interface única** que toda estratégia futura implementa. Substitui a lógica hoje espalhada e duplicada em `strategy_rules.json` (monolito), `claude_recheck.py` (módulos ATIVO/DESATIVADO + classificação SETUP_VALIDO), `operational_prompt.md` (regras discricionárias) e os hard blocks globais. Cada estratégia vira um **módulo isolado** conforme a um contrato; o core comum permanece pequeno.

## 2. Core Rule

**Status e permissão vivem no Strategy Registry, NÃO no módulo.** O módulo da estratégia **não decide** se pode enviar Telegram, se está LIVE, nem se pode executar. Ele apenas **calcula um setup e devolve um signal candidate** + razões. A decisão de rota (log/watch/Telegram/execução) é da Notification Policy, derivada do `status` no registry.

## 3. Minimal Strategy Module Fields

- `id` — único, estável (casa com o registry).
- `symbol`, `timeframe`, `direction` (LONG/SHORT/BOTH/CONTEXT).
- `gates` — lista de predicados causais (ver §7).
- `entry_logic` — trigger no close do bar causal.
- `invalidation` — condição de anulação/saída do setup.
- `risk_model` — stop/target/exit declarados (ex.: stop estrutural −ATR / R-based / V_stair).
- `evidence_ref` — link para backtest/validação RAW-traced.
- `raw_source_map` — mapa campo→fonte RAW (proíbe SLIM/proxy).
- `lookahead_audit_status` — PENDING / PASSED / FAILED / NOT_REQUIRED.
- `outcome_spec` — como o Outcome Engine mede este setup.
- `version` — versão do módulo.
- `status_ref` (owner) — aponta para a entrada no registry (status não vive aqui).

## 4. What A Strategy Module MAY Do

- Calcular o setup a partir de dados causais.
- Devolver um **signal candidate** (estado + metadados).
- Devolver **rejection reason** quando um gate falha.
- Declarar seus **source fields** (raw_source_map).
- Declarar seu **risk model**.
- Declarar seu **outcome spec**.

## 5. What A Strategy Module MUST NOT Do

- Enviar Telegram (ou qualquer notificação).
- Decidir o próprio status.
- Decidir deployment.
- Acessar o execution adapter.
- Usar SLIM/proxy como validação.
- Depender de **nome de estratégia** sem a definição real (gates reais ≠ nome).
- Sobrescrever a Notification Policy.

## 6. Required Output Format (mínimo)

Cada avaliação devolve um objeto com:
- `strategy_id`
- `timestamp` (ISO, do bar causal)
- `symbol`
- `timeframe`
- `direction`
- `signal_state` ∈ { `NO_SIGNAL`, `CANDIDATE`, `VALID_SETUP`, `REJECTED_BY_GATE` }
- `gates_passed` (lista)
- `gates_failed` (lista)
- `rejection_reason` (string; vazio se não rejeitado)
- `confidence_notes` (texto opcional, não-numérico-overfit)
- `risk_model_ref`
- `evidence_ref`

O módulo **nunca** emite `SETUP_VALIDO`-como-rota; `VALID_SETUP` é só um estado de signal — a rota é decidida pelo registry/policy.

## 7. Gate Discipline

Todo gate declara obrigatoriamente:
- `predicate` — a condição lógica.
- `source_field` — o campo de onde vem.
- `raw_source_map` — a fonte RAW do campo (nunca SLIM/proxy).
- `causal_timing` — usa só dados de bars fechados ≤ entry (close-only-causal); indicadores que repintam → SHIFT1.
- `lookahead_status` — PENDING/PASSED/FAILED/NOT_REQUIRED para o gate.
- `failure_behavior` — o que acontece se o gate falha (ex.: `REJECTED_BY_GATE` com reason).

## 8. Relationship With Registry

- O **módulo** gera o signal (estado + gates + razões).
- O **registry** decide se esse signal pode virar `log` / `watch_note` / `telegram_review`.
- `telegram_urgent` e `execution` ficam **sempre desabilitados nesta fase**, para todos.
- Sem entrada no registry com permissão correspondente, o signal **não tem rota** (não existe rota por desenho).

## 9. Migration Rule

Estratégias antigas **não migram por nome**. Só migram após, em ordem:
1. `raw_source_map` completo (campos traçados a RAW),
2. **lookahead audit** (ORIG vs SHIFT1),
3. `evidence_ref` (validação RAW-traced documentada),
4. entrada no **registry**,
5. **notification permission** derivada do status.

Nenhum atalho via SLIM, nome ou status legado.

## 10. First Candidate Note

**XAU 4H LONG / detector a6_a7** é apenas **CORE_CANDIDATE_INPUT**. NÃO vira módulo oficial antes do **lookahead/SHIFT1 audit** (hoje `lookahead_audit_status = PENDING`). L1 (H1 BULL_PULLBACK) é aprovado por Cris como layer, mas as métricas R herdam o status do detector não-auditado — logo o módulo permanece não-oficial até o audit.

## 11. Não-objetivos desta fase

NÃO implementar módulo, NÃO migrar estratégia, NÃO popular registry, NÃO conectar a receiver/recheck/monitor, NÃO habilitar telegram_urgent/execution, NÃO tocar produção.
