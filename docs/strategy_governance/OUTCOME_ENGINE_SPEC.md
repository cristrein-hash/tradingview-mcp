# OUTCOME ENGINE — SPEC (Patch 4, design-only)

**Criado:** 2026-06-14 · **Estado:** SPEC apenas. Nenhum código, nada conectado ao runtime, nenhuma automação. Quarto e último pilar de governança desta rodada (com Registry, Module Contract, Notification Policy).

## 1. Purpose

O **Outcome Engine** é a camada **separada** que mede o resultado **pós-sinal** (R, MFE/MAE, hit target/stop, tempo) de forma RAW-traced e auditável. Ele **não emite alertas** e **não decide status** — apenas computa e registra o resultado para pesquisa/aprendizado humano. Seed/referência: o **Signal Outcome Lab** (72 outcomes XAU CLEAN + manifest).

## 2. Core Rule

O Outcome Engine:
- **não envia Telegram**,
- **não valida estratégia sozinho**,
- **não executa trades**,
- **não altera o registry automaticamente** (qualquer mudança de status é decisão humana, separada).

## 3. Inputs

- `event_id` / `signal_id`
- `strategy_id`
- `timestamp` (do bar causal)
- `symbol`
- `timeframe`
- `direction`
- `entry_reference` (preço/bar de entrada)
- `risk_model_ref` (stop/target/exit do módulo)
- `outcome_spec` (como medir, vindo do módulo)
- `raw_source_reference` (dataset RAW + range/sha)

## 4. Outputs

- `outcome_id`
- `status` ∈ { `CLEAN`, `INCOMPLETE`, `INVALID`, `CONTAMINATED` }
- `R_result` (R realizado)
- `MFE` / `MAE`
- `hit_target` (bool)
- `hit_stop` (bool)
- `time_to_target`
- `time_to_stop`
- `data_quality_flags` (lista)
- `source_refs` (slim/raw file + row range + sha)
- `manifest` / `checksum` (provenance do run)

## 5. Safety Rules

- **RAW/source-first** — outcome só de dados RAW-traced.
- **Sem validação por SLIM/proxy.**
- **Sem outcomes contaminados** entrando como verdade (provider/ticker corretos; PEPPERSTONE hard-gate).
- **Sem promoção automática de estratégia.**
- **Sem execução ao vivo.**
- **Sem schedule/automação** até aprovação explícita (sem LaunchAgent inicial — batch/manual).

## 6. Relationship With Other Specs

- `STRATEGY_MODULE_CONTRACT_SPEC.md` — o **módulo cria** o signal candidate (e declara `outcome_spec`).
- `STRATEGY_REGISTRY_SPEC.md` — o **registry define** status/evidência (Outcome Engine pode *informar* `evidence_refs`, mas não muda status sozinho).
- `NOTIFICATION_POLICY_SPEC.md` — controla **saída**; o Outcome Engine não tem rota de notificação.
- **Outcome Engine** — **mede o resultado depois do fato**, desacoplado da emissão.

Fluxo: **Module → signal → (Registry status → Notification Policy → saída)** … e, separadamente e depois, **Outcome Engine mede o resultado** → alimenta pesquisa humana.

## 7. Migration Note

- **Signal Outcome Lab** (`alert-bridge/logs/signal_outcomes_lab/`) é **seed/referência** (evaluator + 72 XAU CLEAN + manifest).
- **enrich / d2r antigos estão deprecados/decommissionados** (bare-ticker→OANDA; ver `OPERATIONAL_INVENTORY.md` §12).
- **`d2r-daily` permanece pausado** (moratório, plist arquivado 2026-06-14) até existir um Outcome Engine limpo.
- **Outcomes legados contaminados** (`*.contaminated_pre_pepperstone_fix`, 330) permanecem **quarentena/referência apenas** — nunca como verdade.

## 8. Future Automation Boundary

- O Outcome Engine **pode alimentar** pesquisa/aprendizado futuro (descoberta de features, calibração — sempre com revisão humana).
- Ele **não pode disparar trades** direta ou indiretamente.
- Qualquer automação futura passa por um **gate próprio do execution adapter** (hoje sempre disabled), com aprovação explícita separada.

## 9. Não-objetivos desta fase

NÃO implementar o engine, NÃO agendar (sem LaunchAgent), NÃO popular registry, NÃO conectar a receiver/recheck/monitor, NÃO reativar d2r/enrich, NÃO tocar produção, NÃO habilitar execução.
