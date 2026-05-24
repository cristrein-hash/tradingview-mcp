# Strategy Candidate Packet — Template

Use este template ao propor uma estratégia nova pra promover de RESEARCH → CANDIDATE. Salvar como `my-strategy/strategies/candidates/<strategy_id>.md`.

`strategy_id` é único e estável durante todo o lifecycle. Formato sugerido: `<asset>_<tf>_<direction>_<short_name>`. Ex: `xauusd_4h_long_breakout_continuation`.

---

## ⚡ MÍNIMO OBRIGATÓRIO (precisa pra promover RESEARCH → CANDIDATE)

Apenas 4 blocos abaixo são hard requirements:
- **Cabeçalho** (seção 1)
- **Hipótese operacional** (seção 1)
- **Critérios objetivos** (seção 2)
- **Backtest** (seção 3)

O resto (seções 4-8) é **OPCIONAL** — preencher só quando ajuda a clareza da decisão. Estratégia simples (ex: RSI cross em 1 ativo) raramente precisa de todos os campos. Estratégia complexa (multi-filtro, multi-TF, com regime gate) ganha valor preenchendo mais.

**Princípio:** preencher tudo "por garantia" vira teatro burocrático. Preencher só o necessário força clareza.

---

## Cabeçalho (obrigatório)

```yaml
strategy_id: <asset>_<tf>_<direction>_<short_name>
display_name: <Nome legível pra Telegram / logs>
asset: <PEPPERSTONE:XAUUSD | BINANCE:ETHUSD | etc.>
base_symbol: <XAUUSD | ETHUSD | EURUSD | US500 | XAGUSD | ...>
timeframe: <15 | 30 | 60 | 240 | 1D>
direction: <LONG | SHORT | BOTH>
status: RESEARCH
created_at: <YYYY-MM-DD>
author: <Cris | Claude+Cris>

# Accountability — quem aprovou o estado atual e quando
approved_by: <Cris | pending>
approved_at: <YYYY-MM-DD | null>
last_promotion_at: <YYYY-MM-DD | null>
last_promotion_to: <CANDIDATE | SHADOW | PRODUCTION_SMALL_SIZE | PRODUCTION_NORMAL_SIZE | PAUSED | RETIRED | null>
exception_to_pipeline: <descrever justificativa se pulou algum gate SOFT; senão "none">
```

**Regra:** toda mudança de `status` exige atualizar `approved_by`, `approved_at`, `last_promotion_at`, `last_promotion_to`. Sem esses campos atualizados, a promoção não vale (mesmo que o estado tenha sido alterado no arquivo).

---

## 1. Hipótese operacional

Em 2-3 frases: **o que** a estratégia tenta capturar e **por que** isso deve funcionar (edge teórico).

Bom exemplo:
> "Capturar continuação de breakout em XAU 4H após swing high de 10 candles, filtrando por regime macro (EMA50>EMA200, ADX≥20, slope EMA50 positivo). Edge teórico: rompimento de resistência relevante em regime de alta sustentada tende a continuar antes de reversão, principalmente quando ATR está expandindo."

Ruim:
> "Comprar quando RSI sair de oversold." (sem edge claro, sem filtro de regime)

---

## 2. Critérios objetivos

**Entrada** (cada item codificável em Pine sem ambiguidade):
- Trigger 1: ...
- Trigger 2: ...
- ...

**Filtros** (condições que precisam estar todas TRUE):
- Filtro 1: ...
- Filtro 2: ...
- ...

**Invalidação** (condições que matam a entrada antes do trigger):
- ...

**Stop técnico** (regra única, sem julgamento):
- Ex: `low - 0.5 * ATR14`

**Target / gestão de saída**:
- Ex: TP fixo em 4R, ou trailing por EMA50, ou exit por hard block, etc.

**Quando NÃO operar** (regimes/contextos a evitar):
- Ex: durante FOMC, em downtrend macro, etc.

---

## 3. Backtest

```yaml
window:
  start: <YYYY-MM-DD>
  end: <YYYY-MM-DD>
  bars: <N>
n_trades: <int>
win_rate_pct: <float>
expectancy_R: <float, positivo obrigatório>
profit_factor: <float, ≥1.2 ou justificativa>
max_drawdown_R: <float, negativo>
sharpe: <opcional>
n_dependency_test: <% do PnL vindo dos top-3 trades — se >50%, vermelho>
```

**Janela mínima:** 6 meses OU n=30 (whichever first). Se opera 4H/1D e n<30 em 6 meses, estender janela ANTES de avançar.

---

---

## 🔧 OPCIONAL — preencher quando ajuda clareza (seções 4-8)

Pular qualquer seção abaixo é OK se: (a) campo não se aplica à estratégia, OU (b) é redundante com info já no backtest/critérios. **Não preencher por preencher.**

---

## 4. Sample evidence (opcional)

3 exemplos **bons** (trades vencedores que ilustram o setup ideal):
- Trade 1: `<data> <ativo> <TF>` — descrição curta + screenshot path opcional
- Trade 2: ...
- Trade 3: ...

3 exemplos **ruins** (trades perdedores instrutivos — onde o setup parecia bom mas o resultado foi negativo):
- Trade 1: ...
- Trade 2: ...
- Trade 3: ...

3 exemplos **borderline** (filtros quase falharam — bom pra calibrar):
- ...

---

## 5. Pine + template (obrigatório APENAS no gate CANDIDATE → SHADOW; opcional antes)

```yaml
pine_file: my-strategy/pine_alerts/<NN>_<asset>_<tf>_<short>.pine
pine_indicator_title: "<asset> <tf> <NAME> — Alert"
template_file: alert-bridge/alert_templates/<base_asset>_<short>.json
alert_type: module_trigger_<asset>_<tf>_<short>
strategy_module: <ASSET>_<TF>_<DIRECTION>_<SHORT>_VERSION
indicator_version: <v1 | v2 | ...>
webhook_url: /webhook/<SECRET>   # gerado pelo LaunchAgent, NUNCA hardcoded
```

**Checklist Pine** (ver `DEPLOYMENT_CHECKLIST.md` seção "Pine"):
- [ ] `ts_signal` via `str.format_time(time, "yyyy-MM-dd'T'HH:mm:ss'Z'", "UTC")` no payload
- [ ] `barstate.isconfirmed` ou `freq_once_per_bar_close`
- [ ] `r_sanity_pass` check (r_points > 0 e ≤ 5×ATR)
- [ ] `alert_type` único no projeto

---

## 6. Métricas que vão ser medidas em SHADOW (opcional)

Lista o que o `evaluate_setup_outcomes.py` ou equivalente vai medir pra essa estratégia:
- MFE em N candles (5, 10, 20, 50)
- MAE em N candles
- R outcome
- Tempo até stop / TP
- Hard blocks acionados (quantos e quais)
- Comparação outcome shadow vs backtest

---

## 7. Sinais de falha que devem disparar PAUSED (recomendado pra estratégia que vai pra PRODUCTION; opcional pra SHADOW)

Definir A PRIORI o que sinaliza problema:
- Drawdown realizado > 1.5× projetado pelo backtest
- 3 trades perdedores consecutivos fora do esperado
- Win rate em SHADOW desvia >20% do backtest
- Schema warnings > 5% dos eventos
- Mudança de regime macro identificável

Isso evita "decisão emocional" de pausar/aposentar.

---

## 8. Anexos (opcional)

- Link pra notebook/script de backtest
- Path do arquivo `proposals/<id>_proposal.md` (quando aplicável, ver D4 do RESEARCH_POLICY)
- Referências (papers, posts, threads que inspiraram)

---

## Exemplo preenchido (estrutura mínima)

```yaml
strategy_id: xauusd_4h_long_breakout_continuation
display_name: "XAU 4H BREAKOUT_CONTINUATION_REGIME_FILTERED"
asset: PEPPERSTONE:XAUUSD
base_symbol: XAUUSD
timeframe: 240
direction: LONG
status: PRODUCTION_NORMAL_SIZE   # exemplo já avançado
created_at: 2026-05-15
```

Hipótese: continuação de breakout após swing_high(10) com regime macro alinhado (5 filtros).

Backtest: 234 trades / 7.4 anos / +64.57R / PF 1.64 / expectancy 0.28R.

Pine: `my-strategy/pine_alerts/01_xauusd_4h_breakout_continuation.pine` v12, `ts_signal` presente, slot único pós-cleanup 2026-05-23.

Template: alerta TV mecânico, sem payload externo (Pine emite via `alert()`).
