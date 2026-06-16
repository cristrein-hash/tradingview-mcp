# OPERATING — XAU L1 (EMA21 Continuation) · ciclo operacional

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
python3 run_l1_cycle.py               # DRY-RUN (sem Telegram)
python3 run_l1_cycle.py --send-telegram   # envia notificação SE houver operational_candidate
```
Estado/log do ciclo em `.runtime_state/l1_cycle.log` (não-legacy). Dedup em `.runtime_state/l1_dedup.txt`.

## Interpretar a saída
- **`no_candidate`** — regime D-1 ≠ BULL (ex.: BEAR) ou regra-base não satisfeita. Nenhuma ação. Sem Telegram.
- **`blocked_exhaustion`** — regime BULL mas RSI gate (`rsi_vs_ma ≤ −9.35`) bloqueou (topo/exaustão). Sem Telegram.
- **`operational_candidate`** — candidato válido. **Telegram candidate notification enviado** (se `--send-telegram`).
- **`regime_l1_v4_stale`** — regime desatualizado; rode `refresh_regime_l1_v4.py --write` primeiro (o runner já faz isso).

## Telegram NÃO é ordem
A notificação diz **"CANDIDATE — revise o chart"** + `signal_hash`. **NÃO é "entre", não é "entrada aprovada", não é "trade validado".**
**A entrada é 100% decisão humana.** Você confirma no chart e, se entrar, registra manualmente (journal `--entry-taken`).

## Scheduler (`com.cristrein.xau-l1-cycle.plist`) — ⚠️ NÃO CARREGADO
A plist existe como **template**, mas **NÃO foi carregada** (hard stop): a grade de fechamento 4H do XAU
**desloca 1h com DST** (verão UTC 02/06/10/14/18/22 · inverno 03/07/11/15/19/23) e o `StartCalendarInterval`
do launchd usa o **TZ local da máquina**. Carregar com horário desalinhado erraria os fechamentos metade do ano.

**Antes de carregar (decisão sua):** confirmar o TZ da máquina e ajustar os horários da plist ao fechamento 4H
real (ou usar abordagem DST-robusta). Só então:
```bash
cp com.cristrein.xau-l1-cycle.plist ~/Library/LaunchAgents/
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.cristrein.xau-l1-cycle.plist
launchctl list | grep xau-l1-cycle           # confirmar carregado
```
**Pausar / descarregar:**
```bash
launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.cristrein.xau-l1-cycle.plist
rm ~/Library/LaunchAgents/com.cristrein.xau-l1-cycle.plist   # remover de vez
```
O runner é **DST-agnóstico** (lê a barra live + dedup), então operação **manual** é segura agora mesmo, sem o scheduler.

## Não fazer
Não tocar broker/Pepperstone · receiver/monitor/recheck/strategy_rules/catalog legacy · RAW/v6 · pause flag.
Não ativar XAU 1H/15M. Não transformar Telegram em ordem.
