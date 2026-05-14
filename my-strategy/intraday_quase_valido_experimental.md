# INTRADAY_QUASE_VALIDO — Regra Experimental v1.0

**Status**: 🧪 **EXPERIMENTAL — em observação**
**Criada em**: 2026-04-29
**Validade**: provisória até 25-30 casos reais avaliados em R
**Aprovada para entrada automática?** ❌ NÃO
**Aprovada para Telegram com marcador "REVISÃO HUMANA"?** ✅ SIM

---

## 1. Propósito

Esta regra existe **fora** de `strategy_rules.json` para capturar oportunidades intraday assimétricas (R:R ≥ 2:1) que **não atendem ao critério rígido de RSI 4H extremo** mas têm múltiplas confluências locais.

**Justificativa estatística** (auditoria de 9 casos fechados em 2026-04-28/29):
- Win rate aproximado: 78%
- Average win: ~+2.5R (saída em primeiro target técnico)
- Average loss: -1R (stop técnico atrás de zona)
- **Expectancy líquido: ~+1.7R por trade**
- Mesmo no cenário pessimista (50% win rate, +2R/-1R), a expectancy permanece **positiva** (~+0.5R/trade) por causa da assimetria estrutural (R:R obrigatório ≥ 2:1).

A regra existe para **revisão humana**, não para entrada automática.

---

## 2. Critérios obrigatórios (TODOS devem estar presentes)

| # | Critério | Verificação |
|---|---|---|
| 1 | **Whitelist** | Ativo está nos 9 ativos ativos pós-otimização (XAUUSD, XAGUSD, XPTUSD, US500, BTCUSD, ETHUSD, USOUSD, EURUSD, USDJPY) |
| 2 | **Timeframe de execução** | 15M, 30M ou 1H |
| 3 | **Zona local marcada** | Zona BB 30M/1H/4H AUTO_CLAUDE_ existe e preço dentro/tocando/encostando |
| 4 | **Sinal NAS100 dentro da zona** | 1+ sinal LONG (compra) ou SHORT (venda) dentro ou na borda da zona, na direção do trade |
| 5 | **Confirmação estrutural** | Pelo menos UMA: divergência Regular Bull/Bear detectada pelo RSI study OU CHoCH/BOS visível no TF de execução ou imediatamente superior, na direção do trade |
| 6 | **Stop técnico claro** | Invalidação ≤ 0.2 ATR atrás da borda da zona ou último swing oposto. Se zona ambígua, descartar |
| 7 | **R:R mínimo 2:1** | Distância ao primeiro alvo técnico (próxima zona oposta ou nível) ≥ 2× distância do stop |
| 8 | **Filtro macro** | NÃO disparar durante janela 🔴 do `macro_context_daily.md` (30 min antes a 30 min depois de FOMC, GDP/PCE, NFP, decisões ECB/BoE/BoJ, Powell speech) |
| 9 | **Filtro de range** | Estrutura direcional, não consolidação tight. Critério: ATR(14) do TF ≥ 0.5% do preço, OU preço quebrou estrutura recente, OU está alinhado com tendência D/4H |

**Se TODOS os 9 critérios atendidos** → INTRADAY_QUASE_VALIDO.
**Se 1 ou mais ausentes** → não é QUASE_VALIDO.

---

## 3. O que NÃO é QUASE_VALIDO

- Setup com apenas zona + sinal NAS100 (sem confirmação estrutural) — só observação.
- Setup em janela macro 🔴 — silenciar mesmo que critérios técnicos estejam presentes.
- Setup em range tight (USDJPY 30M consolidado 159-161 é o counter-example clássico) — exigir tendência ou breakout.
- Setup com R:R 1.5:1 — abaixo do mínimo 2:1.
- Setup onde o stop técnico fica indefinido (>0.5 ATR atrás) — ambiguidade.

---

## 4. Política de Telegram para QUASE_VALIDO

**Formato obrigatório da mensagem Telegram**:

```
🟡 INTRADAY_QUASE_VALIDO — REVISÃO HUMANA
[NÃO É ENTRADA AUTOMÁTICA — VOCÊ DECIDE]

Ativo: <symbol_with_provider>
TF: <15M|30M|1H>
Direção: <LONG|SHORT>
Status: 🧪 experimental v1 — em teste

Entry estimada: <price>
Stop técnico: <price> (motivo)
Alvo 1: <price> (motivo)
R:R: <ratio>:1

Confluências presentes:
✓ Zona <zone_id_or_drawing_name>
✓ Sinal NAS100 <LONG|SHORT> na zona
✓ <Bear/Bull div regular | CHoCH | BOS>
✓ Stop técnico viável (≤0.2 ATR)
✓ Filtro macro: 🟢 fora de janela crítica
✓ Filtro de range: estrutura direcional confirmada

Tendência maior: <aligned|neutral|against>

⚠️ ESTA É REVISÃO. Confirme manualmente antes de qualquer entrada.
⚠️ Status: experimental, sample atual <n>/30 antes de promoção.
```

**Garantias da mensagem**:
- Sempre começa com 🟡 (não verde — não é setup pronto)
- Sempre inclui "REVISÃO HUMANA" e "NÃO É ENTRADA AUTOMÁTICA"
- Sempre inclui status experimental e sample count
- NUNCA chama de "setup pronto", "entry confirmada" ou "trade ativo"

---

## 5. Logging obrigatório

**Cada disparo** de INTRADAY_QUASE_VALIDO deve ser registrado em:

```
/Users/cristrein/tradingview-mcp/alert-bridge/intraday_quase_valido_log.jsonl
```

Formato: 1 JSON object por linha (JSONL). Schema definido em `intraday_quase_valido_log.jsonl` (primeira entrada `_schema_example`).

**Campos obrigatórios em cada entrada**:
- `timestamp_iso` — ISO 8601 UTC
- `symbol` — provider:symbol (ex: PEPPERSTONE:ETHUSD)
- `timeframe` — 15M | 30M | 1H
- `direction` — LONG | SHORT
- `entry_estimated`, `stop_estimated`, `target1_estimated`, `target2_estimated`
- `risk_reward_estimated` — número
- `confluences` — array de strings descrevendo confluências presentes
- `macro_window_active` — true | false (filtro macro)
- `range_atr_pct` — % do preço atual
- `htf_trend_aligned` — aligned | neutral | against
- `outcome_status` — pending | hit_target_1 | hit_target_2 | hit_stop | invalidated_other | indecisive
- `outcome_r_realized` — R fechado real (preencher após 4-12h)
- `outcome_evaluated_at_iso` — quando foi avaliado
- `mfe_r` — Maximum Favorable Excursion em R (peak unrealized)
- `mae_r` — Maximum Adverse Excursion em R (drawdown unrealized)
- `notes` — observações livres

**Quando preencher cada campo**:
- No disparo: timestamp, symbol, TF, direção, entry/stop/targets, R:R, confluences, filtros, htf_trend
- Após 4-12h: outcome_status, outcome_r_realized, outcome_evaluated_at_iso, mfe_r, mae_r, notes
- Se ainda indeciso após 12h: marcar `indecisive` e reavaliar em 24h

---

## 6. Política de validação (25-30 casos)

**Sample mínimo para promoção**: **25 casos com outcome_status fechado** (não pending nem indecisive).
**Sample máximo antes de revisão obrigatória**: 30 casos.

**Métricas a calcular após sample completo**:

```
win_rate = wins / total_closed
average_win_r = sum(R em wins) / count(wins)
average_loss_r = sum(R em losses) / count(losses)  # números negativos
expectancy_r = win_rate × avg_win - (1 - win_rate) × |avg_loss|
profit_factor = sum(winning R) / sum(|losing R|)
```

### Critérios de decisão após 25-30 casos

| Métrica | Promover | Manter experimental | Matar |
|---|---|---|---|
| Expectancy | ≥ +0.5R | 0 a +0.5R | < 0R |
| Win rate | ≥ 50% | 40-50% | < 40% |
| Profit factor | ≥ 1.5 | 1.0-1.5 | < 1.0 |
| MFE médio | ≥ 1.5R | 1-1.5R | < 1R |

**Promover** = mover para `strategy_rules.json` como condição formal `INTRADAY_SETUP_VALIDO_ALT` (alternativa ao RSI extremo) ou similar.
**Manter experimental** = continuar coletando casos, ajustar critérios marginais.
**Matar** = remover regra, voltar à régua atual estrita.

**Importante**: um único loss isolado não invalida a hipótese. Avaliar **expectancy líquido** sobre o sample completo.

### Critério de aborto antecipado (kill switch)

Se em qualquer ponto durante a coleta a expectancy projetada cair abaixo de **−1R em 10 casos consecutivos**, declarar `kill_switch_triggered: true` no log e parar de disparar QUASE_VALIDO até revisão humana.

---

## 7. Garantias e limites operacionais

✅ **NÃO altera** `strategy_rules.json`.
✅ **NÃO altera** `operational_prompt.md` sem aprovação humana.
✅ **NÃO automatiza** ordens.
✅ **NÃO transforma** em SETUP_VALIDO.
✅ Status permanece **experimental/em observação** até promoção formal.
✅ Telegram **sempre marcado** "QUASE_VALIDO — REVISÃO HUMANA".
✅ Falso positivo isolado **não invalida** a hipótese — avaliar expectancy líquido.
✅ Se sample < 25 → declarar **"amostra insuficiente"** ao reportar resultado.

---

## 8. Histórico de versões

| Versão | Data | Mudanças |
|---|---|---|
| v1.0 | 2026-04-29 | Criação inicial. Baseada em auditoria de 9 casos com expectancy +1.7R. |

---

## 9. Próxima revisão

- **Próxima auditoria**: ao atingir 10 casos fechados (revisão parcial — não decisão).
- **Auditoria de promoção**: ao atingir 25 casos fechados.
- **Se passar de 60 dias sem 25 casos**: revisar critérios — pode estar restritiva demais ou sample-rate insuficiente.
