# MODULE_AWARE_GLOBAL_RULES_V3

Status: active (substitui V2 — shadow mode removido por decisão do usuário em 2026-05-12)
Purpose: adapt global validation rules to backtested strategy modules without removing operational safety, with explicit short-circuit hierarchy, caps for Telegram and Watch Manager, and module precedence rules.

## 1. Core decision

The old global rule set must no longer act as a universal setup checklist for all modules.

It remains as a safety layer.

Each validated module has its own checklist.

Final classification must follow the explicit short-circuit hierarchy described in §5.

GLOBAL HARD BLOCKS
+
MODULE DETECTION
+
MODULE-SPECIFIC CHECKLIST
+
PROMOTION TRIGGER
+
ENTRY QUALITY
=
classification

## 2. Why this exists

The system now has multiple strategy modules validated by historical backtests:

- XAUUSD_4H_LONG_REJECTION_SWING
- XAUUSD_1H_LONG_REJECTION_EXECUTION
- XAUUSD_INTRADAY_BB_CONFLUENCE_EXECUTION
- US500_4H_LONG_PULLBACK_REJECTION
- US500_INTRADAY_LONG_PULLBACK_EXECUTION
- ETHUSD_4H_LONG_BREAKOUT_CONTINUATION
- ETHUSD_30M_CONFIRMED_MOMENTUM_EXECUTION
- EURUSD_30M_LONG_QUALITY_BREAKOUT_CONTINUATION

The old global checklist required RSI extreme, TOP/BOTTOM, and Market Order Bubbles too broadly.

That conflicts with several modules:

- US500 pullback modules do not require RSI < 30.
- EURUSD quality breakout needs RSI supportive, not extreme.
- ETHUSD momentum continuation needs momentum confirmation, not reversal RSI.
- XAUUSD quality rejection can be valid without all old global confirmations.

Therefore, RSI extreme / NAS / Bubbles cannot remain universal hard requirements.

## 3. Global hard blocks

These remain mandatory for every module.

Do NOT classify as SETUP_VALIDO or SETUP_VALIDO_INTRADAY if any are true:

- MCP/chart reading is unreliable.
- Symbol/timeframe is wrong.
- Direction is undefined or conflicts with the module.
- R:R < 2:1.
- Stop is not clear or not technical.
- Entry is late/chasing (entry_late_distance_r >= 0.5R).
- Setup is already missed / do not pursue.
- Macro red window is immediate.
- Price is in obvious falling knife / melt-up chase against the module.
- No objective trigger exists.
- Setup depends only on RSI, NAS, bubble, or dry zone touch without **price structure** (see strategy_rules.json → accepted_price_structures for the formal definition).

These hard blocks override all modules.

## 4. Flexible global confluences

The following are not universal hard requirements.

They are confluences whose meaning depends on the module:

- RSI
- NAS TOP/BOTTOM
- Market Order Bubbles
- Divergence
- Rejection close
- CHoCH/BOS
- Sweep/reentry
- Breakout/retest
- HTF context
- Momentum expansion
- Pullback quality

The question is not "Is RSI extreme?". The correct question is "Is RSI appropriate for THIS module?".

Examples:

- **EURUSD_30M_LONG_QUALITY_BREAKOUT_CONTINUATION:** RSI >= 54 can be valid. RSI extreme is not required.
- **US500_INTRADAY_LONG_PULLBACK_EXECUTION:** Bullish pullback context matters more than RSI oversold.
- **ETHUSD_30M_CONFIRMED_MOMENTUM_EXECUTION:** Momentum confirmation matters more than reversal RSI.
- **XAUUSD_1H_LONG_REJECTION_EXECUTION:** Quality rejection + structure + R:R can be sufficient.

## 5. Evaluation hierarchy (short-circuit, MANDATORY ORDER)

Each step is evaluated in order. If a step fails, **stop and classify according to that step's exit rule**. Do NOT continue evaluating subsequent steps.

### Step 1 — hard_blocks

Evaluate all global hard blocks (§3).

- on FAIL → `classification = NO_TRADE`. Set `hard_block_triggered = <name>`. STOP.
- on PASS → go to step 2.

### Step 2 — module_detection

Detect if any experimental module applies (asset + TF + direction compatible).

- on NO MATCH → apply classical global rule. Classification máxima permitida = `SETUP_CANDIDATO_FORTE` (régua antiga; cap RSI clássico aplica).
- on MULTIPLE MATCH → apply precedence rules from §7.
- on SINGLE MATCH → go to step 3 with that module.

### Step 3 — module_checklist

Evaluate the specific checklist of the detected module.

- on FAIL → `classification máxima = SETUP_CANDIDATO_FORTE`. Set `module_checklist_failed_on = <item>`. STOP de promoção.
- on PASS → go to step 4.

### Step 4 — promotion_trigger

Check if the module's objective trigger is present **and confirmed** (closed candle when applicable).

- on NONE → `classification máxima = SETUP_CANDIDATO_FORTE`. Set `promotion_trigger = NONE`. STOP de promoção.
- on PRESENT → go to step 5.

### Step 5 — entry_quality

Validate R:R >= 2:1, stop technical defined, entry not late (`entry_late_distance_r < 0.5`).

- R:R or stop fails → `NO_TRADE` (severe) or `SETUP_EM_OBSERVACAO` (waitable).
- entry late → `SETUP_ATRASADO_AGUARDAR_RETESTE`.
- all pass → **promote to `SETUP_VALIDO` (swing module) or `SETUP_VALIDO_INTRADAY` (intraday module).**

## 6. Canonical classifications (v3 — only 7)

Use only these classifications:

1. `SETUP_VALIDO` — swing/HTF.
2. `SETUP_VALIDO_INTRADAY` — intraday (15M/30M/1H).
3. `SETUP_CANDIDATO_FORTE` — module applies, checklist not fully met. Goes to Telegram (capped). Use `execution_tf` field to distinguish swing vs intraday.
4. `SETUP_EM_OBSERVACAO` — area relevant, setup forming. Use `execution_tf` field.
5. `NO_TRADE` — hard block or invalidation.
6. `SETUP_PERDIDO_NAO_PERSEGUIR` — ideal move happened during system blind window; do not chase.
7. `SETUP_ATRASADO_AGUARDAR_RETESTE` — trigger fired but entry now compromised; wait for retest.

**Removed:** SETUP_FORTE, SETUP_EXCELENTE, SETUP_VALIDO_SHADOW, SETUP_VALIDO_INTRADAY_SHADOW, SETUP_OPERACIONAL_MANUAL, INTRADAY_NO_TRADE, INTRADAY_EM_OBSERVACAO, INTRADAY_SETUP_VALIDO, INTRADAY_SETUP_FORTE, INTRADAY_SETUP_EXCELENTE, SETUP_CANDIDATO_FORTE_INTRADAY.

See `strategy_rules.json → module_aware_policy.deprecation_mapping` for retro-mapping.

## 7. Module precedence

When multiple modules apply to the same symbol:

1. SWING > INTRADAY no mesmo ativo no mesmo dia.
2. Direções conflitantes (um LONG, outro SHORT) → `NO_TRADE`. Não tomar nenhum dos dois.
3. Mesma direção, múltiplos módulos: maior Priority ganha (A > B > C).
4. Empate de Priority: maior `module_backtest_n` ganha.
5. Empate de n: menor TF (mais granular) ganha.
6. Nunca empilhar exposição duplicada — apenas um módulo gera sinal por ativo por janela operacional.

## 8. Telegram caps

- `SETUP_VALIDO` → sem cap (qualidade alta, raro).
- `SETUP_VALIDO_INTRADAY` → sem cap.
- `SETUP_CANDIDATO_FORTE` → **máximo 5 por ativo por dia.** Acima disso, agrupar em digest.
- `SETUP_EM_OBSERVACAO` → normalmente não enviar; só enviar quando relevante (gatilho a 1 candle de fechar, entrada próxima).

## 9. Watch Manager caps

- Máximo 6 ACTIVE_WATCH simultâneos.
- Fila prioritária: Priority A > B > C.
- Em empate de Priority: FIFO ou maior `module_backtest_n`.
- Quando atingir 6, novos watches só entram substituindo um existente de prioridade inferior.

## 10. Required structured output fields

For every operational event, Claude MUST expose these fields in text so the receiver can persist them:

```
Strategy Module:
Module backtest n:
Global hard blocks: PASS | FAIL
Module checklist: PASS | FAIL
Module checklist notes:
Module score:
Operational signal: YES_MANUAL_REVIEW | NO
D2R required: true | false
Hard block triggered: NONE | <name>
Module checklist failed on: NONE | <item>
Promotion trigger: NONE | REJECTION_CLOSE | MOMENTUM_CONTINUATION | BREAKOUT_RETEST | SWEEP_REENTRY | CHOCH_BOS | RETEST_HOLD | NAS_SIGNAL_AT_ZONE | DENSE_STRUCTURAL_CONFLUENCE
Promotion status: NOT_PROMOTED | KEEP_AS_CANDIDATO_FORTE | PROMOTE_TO_SETUP_VALIDO | PROMOTE_TO_SETUP_VALIDO_INTRADAY | DOWNGRADE_TO_OBSERVACAO | NO_TRADE
Priority: A | B | C
Trigger:
Execution TF: 15 | 30 | 60 | 240 | 720 | D
Entrada ideal:
Preço atual:
Entrada atrasada: SIM | NÃO
Entry late distance R:
Classificação:
Direção:
```

### PASS / FAIL binário (v3)

**Nunca use "PASS parcial".** Os campos `Global hard blocks` e `Module checklist` são estritamente binários: PASS ou FAIL.

Para detalhar itens parcialmente cumpridos use o campo `Module checklist notes` (texto livre). Quando o checklist falha parcialmente mas o resto está OK, a classificação é `SETUP_CANDIDATO_FORTE`.

## 11. Module backtest n — required

Cada evento operacional deve declarar o `module_backtest_n` do módulo aplicado. Valores atuais (ver `strategy_rules.json → module_aware_policy.module_backtest_n_required.current_values`):

| Módulo | n |
|---|---:|
| ETHUSD_30M_CONFIRMED_MOMENTUM_EXECUTION | 637 |
| US500_INTRADAY_LONG_PULLBACK_EXECUTION | 71 |
| XAUUSD_1H_LONG_REJECTION_EXECUTION | 21 |
| outros | a declarar |

Use este valor:
- Como tie-breaker em precedência de módulos (§7.4).
- Para ponderar análises posteriores de D2R.
- Como sanity check: módulos com n < 25 devem ser tratados com mais cautela (manter Priority B mesmo quando outros critérios indicariam A).

## 12. Telegram routing

Vai para Telegram (revisão humana / não-automática):

- `SETUP_VALIDO`
- `SETUP_VALIDO_INTRADAY`
- `SETUP_CANDIDATO_FORTE` (sujeito ao cap de 5/ativo/dia)
- `SETUP_EM_OBSERVACAO` apenas quando relevante (gatilho a 1 candle de fechar)
- `SETUP_PERDIDO_NAO_PERSEGUIR` quando contextualmente útil
- `SETUP_ATRASADO_AGUARDAR_RETESTE` quando reteste é provável

**Não vai para Telegram automaticamente:**
- `NO_TRADE`
- `test_or_non_operational` (alert_type = test_connectivity)
- Eventos sem `alert_type` válido (tratar como `setup_recheck` genérico mas não despachar Telegram operacional).

## 13. D2R required

Sempre `true` para:
- `SETUP_VALIDO`
- `SETUP_VALIDO_INTRADAY`
- `SETUP_CANDIDATO_FORTE`

Para os demais (`SETUP_EM_OBSERVACAO`, `NO_TRADE`, `SETUP_PERDIDO_NAO_PERSEGUIR`, `SETUP_ATRASADO_AGUARDAR_RETESTE`): `false` por padrão; pode ser elevado a `true` se o evento for marcado como instrutivo para auditoria.

## 14. Operational signal

- `SETUP_VALIDO` / `SETUP_VALIDO_INTRADAY` → `Operational signal: YES_MANUAL_REVIEW` (execução manual; revisão humana antes de qualquer ordem).
- `SETUP_CANDIDATO_FORTE` → `Operational signal: YES_MANUAL_REVIEW`.
- Demais → `Operational signal: NO`.

Em todos os casos, execução é manual. **O sistema nunca executa ordens automaticamente.** O usuário revisa o sinal no Telegram e decide.

## 15. Current decision

`MODULE_AWARE_GLOBAL_RULES_V3` está ativo.

A régua global antiga continua existindo como camada de segurança e como checklist padrão quando nenhum módulo aplica.

Quando há conflito entre régua global antiga (RSI extremo, NAS, Bubbles obrigatórios) e checklist de módulo validado:

1. Hard blocks globais primeiro.
2. Checklist do módulo segundo.
3. Régua global antiga vira "evidência de apoio opcional", não bloqueio.

## 16. Operational discipline

Mesmo com SETUP_VALIDO direto (sem shadow), a disciplina é:

- Todo sinal vai para Telegram como `YES_MANUAL_REVIEW`.
- Nenhuma execução automática.
- Usuário revisa o sinal humanamente antes de cada ordem.
- D2R mede cada sinal post-hoc para auditoria de expectancy por módulo.
- Após 30-50 eventos por módulo, avaliar se o módulo merece confiança extra (não automática — apenas conceitual: o backtest se confirmou em produção?).

## 17. Shadow mode — REMOVIDO

Versões anteriores do documento descreviam `SETUP_VALIDO_SHADOW`, `SETUP_VALIDO_INTRADAY_SHADOW` e `SETUP_OPERACIONAL_MANUAL` como classificações intermediárias.

**Removidos em 2026-05-12.** Razão: o usuário confia no backtest e fará revisão manual em cada sinal Telegram. Shadow era redundante com a revisão manual obrigatória já presente em todo SETUP_VALIDO. A separação criava 12 classificações onde 7 bastam.

Eventos antigos no log com classificações shadow continuam válidos historicamente; mapeamento retroativo em `strategy_rules.json → module_aware_policy.deprecation_mapping`.
