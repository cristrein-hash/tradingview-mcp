# OPERATING — XAU L1 (EMA21 Continuation) · ciclo operacional

> **Referência canônica de contexto:** [`docs/BOOTSTRAP_REARCHITECTURE_CANONICAL_CONTEXT.md`](../../../../../docs/BOOTSTRAP_REARCHITECTURE_CANONICAL_CONTEXT.md) — estado completo da re-arquitetura, hard stops, legacy, regime, gate.
> **Próxima frente (spec, design-only):** [`docs/FORWARD_OUTCOME_LAYER_SPEC.md`](../../../../../docs/FORWARD_OUTCOME_LAYER_SPEC.md) · [`docs/FORWARD_OUTCOME_LAYER_ROADMAP.md`](../../../../../docs/FORWARD_OUTCOME_LAYER_ROADMAP.md).

Estratégia única ativa: **XAU 4H LONG — CONTINUATION / L1 · EMA21 CONTINUATION** · PEPPERSTONE:XAUUSD · 4H · LONG · `group_id: XAU_240`.
XAU_60 / XAU_15 = **reservados, inativos, sem Telegram**. Sem multi-ativo. Sem broker. Sem ordem automática.

## Como o ciclo funciona
```
run_l1_cycle.py
  → refresh_regime_l1_v4.py --write     (mantém o regime D-1 fresco; already_fresh se nada novo)
  → runtime_xau.py --once               (lê o chart XAU 4H via MCP, aplica gate, decide estado)
  → Telegram candidate notification     SOMENTE se operational_candidate (com --send-telegram)
  → dedup por signal_hash               (≤ 1 Telegram por barra/sinal)
  → humano revisa o chart e decide a ENTRADA
  → journal / outcome continuam MANUAIS
```
Default = **dry-run** (sem Telegram). Falha fechado: qualquer hard stop aborta sem enviar.

## Rodar manualmente
```bash
cd my-strategy/strategies/xau_4h_long/continuation/L1_EMA21_CONTINUATION
python3 run_l1_cycle.py                    # DRY-RUN (sem Telegram), usa o chart como está
python3 run_l1_cycle.py --send-telegram    # envia notificação SE houver operational_candidate
python3 run_l1_cycle.py --manage-chart     # prepara chart PEPPERSTONE:XAUUSD/240 e RESTAURA depois
python3 run_l1_cycle.py --manage-chart --leave-chart-240   # deixa o chart em 240 (não restaura)
```

## `--manage-chart` (auto-chart 240) — usado pelo scheduler (2026-06-16)
Sem isto, o runtime **hard-stopa** se o chart estiver em outro TF (ex.: 15M). Com `--manage-chart` o runner,
via MCP (`src/server.js`), **lê → troca para PEPPERSTONE:XAUUSD/240 → roda a L1 → restaura o chart anterior**.
- **NUNCA** dirige trade, desenha, toca broker, nem troca para outro símbolo. Lock-guard (`chart_op.lock`)
  + checagem de coleta replay ativa evitam conflito simultâneo. Falha de confirmação = **HARD_STOP sem Telegram**.
- Loga `chart_before` / `chart_used` / `chart_restore` no `l1_cycle.log`.
- O **scheduler agora roda com `--manage-chart --send-telegram`** → a L1 opera no fechamento 4H mesmo se você
  estiver usando o chart em 15M (ele troca por ~30s e devolve). Use `--leave-chart-240` só se quiser ficar em 240.
Estado/log do ciclo em `.runtime_state/l1_cycle.log` (não-legacy). Dedup em `.runtime_state/l1_dedup.txt`.

## Interpretar a saída
- **`no_candidate`** — regime D-1 ≠ BULL (ex.: BEAR) ou regra-base não satisfeita. Nenhuma ação. Sem Telegram.
- **`blocked_exhaustion`** — regime BULL mas RSI gate (`rsi_vs_ma ≤ −9.35`) bloqueou (topo/exaustão). Sem Telegram.
- **`operational_candidate`** — candidato válido. **Telegram candidate notification enviado** (se `--send-telegram`).
- **`regime_l1_v4_stale`** — regime desatualizado; rode `refresh_regime_l1_v4.py --write` primeiro (o runner já faz isso).

## Telegram NÃO é ordem
A notificação diz **"CANDIDATE — revise o chart"** + `signal_hash`. **NÃO é "entre", não é "entrada aprovada", não é "trade validado".**
**A entrada é 100% decisão humana.** Você confirma no chart e, se entrar, registra manualmente (journal `--entry-taken`).

## Scheduler (`com.cristrein.xau-l1-cycle.plist`) — ✅ CARREGADO E ATIVO
A plist está **carregada e disparando** (confirmado em `launchctl list` + `.runtime_state/l1_cycle.log`).
TZ da máquina = **Europe/Lisbon**, então a grade **local** é **DST-robusta**: o fechamento 4H do XAU mapeia
para os **mesmos horários locais** o ano todo (verão UTC+1 / inverno UTC+0) → **03:05 / 07:05 / 11:05 / 15:05 / 19:05 / 23:05**
(5 min pós-fechamento). `RunAtLoad=false` (só roda nos horários). Roda com `--send-telegram` (envia só se `operational_candidate`).

**Confirmar estado:**
```bash
launchctl list | grep xau-l1-cycle           # deve aparecer carregado
tail -5 .runtime_state/l1_cycle.log           # últimos ciclos (status/state/notify)
```
**Pausar / descarregar (decisão sua):**
```bash
launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.cristrein.xau-l1-cycle.plist
# rm ~/Library/LaunchAgents/com.cristrein.xau-l1-cycle.plist   # remover de vez (opcional)
```
**Recarregar (após pausar):**
```bash
cp com.cristrein.xau-l1-cycle.plist ~/Library/LaunchAgents/
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.cristrein.xau-l1-cycle.plist
```
O runner é **DST-agnóstico** (lê a barra live + dedup), então a operação **manual** também é segura a qualquer momento.

## Não fazer
Não tocar broker/Pepperstone · receiver/monitor/recheck/strategy_rules/catalog legacy · RAW/v6 · pause flag.
Não ativar XAU 1H/15M. Não transformar Telegram em ordem.
