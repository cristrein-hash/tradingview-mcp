# 02 — Data Source Policy: RAW First

## Objetivo

Definir a hierarquia de fontes de dados do projeto Trading System e impedir validações contaminadas por features derivadas, proxies ou interpretações não verificadas.

## Regra central

**RAW replay / TradingView visual / source data são a fonte de verdade.**

Nenhuma estratégia séria deve ser validada, recalibrada ou promovida com base apenas em `slim_features`, proxies ou campos derivados.

## Hierarquia de confiança

1. **TradingView visual / Replay com indicadores reais**
   - Fonte máxima para leitura visual, zonas, labels e comportamento de Auction Theory.

2. **RAW replay/source payload**
   - Fonte primária para backtests sérios.
   - Deve conter campos originais ou rastreáveis dos indicadores.

3. **Extractor fiel e auditado**
   - Pode transformar RAW em campos úteis se a fidelidade for comprovada.
   - Deve registrar versão, schema e origem de cada campo.

4. **Features derivadas simples e verificáveis**
   - Exemplo: ATR calculado de OHLC, range, candle body, RSI recalculado de closes.
   - Podem ser usadas se a fórmula for explícita e verificável.

5. **SLIM / proxy / feature interpretativa**
   - Não é fonte validatória.
   - Pode ser usado apenas para screening exploratório, com autorização explícita.

## O que não pode validar estratégia

Os seguintes tipos de campo não podem ser tratados como verdade sem validação RAW/visual:

- `inside_demand`
- `inside_supply`
- `nearest_demand_atr`
- `nearest_supply_atr`
- `demand_state`
- `supply_state`
- `n_demand_zones`
- `n_supply_zones`
- `absorption_depth_atr_5b`
- swing-low proxy sintético
- qualquer proxy de zona
- qualquer proxy de Auction Theory
- qualquer campo derivado que tente representar aceitação, absorção, defesa, rejeição ou localização sem prova visual/RAW.

## Política sobre SLIM

`slim_features` devem ser tratados como artefato derivado, não como fonte final.

Podem ser usados para:

- exploração rápida;
- contagem aproximada;
- screening inicial;
- debugging de disponibilidade de campos;
- comparação preliminar, se autorizado.

Não podem ser usados para:

- validação final;
- threshold oficial;
- decisão de catalog;
- promoção operacional;
- backtest sério de estratégia sensível a indicadores visuais;
- conclusão sobre zonas, NAS, Bubbles, SMC, BigBeluga, Custom OB ou Auction Theory.

## Thresholds

Qualquer threshold estratégico deve ser calibrado em RAW.

Exemplos:

- queda de RSI;
- expansão de range;
- distância até zona;
- contagem de bubbles;
- distância até supply/demand;
- número de candles consecutivos;
- slope, volatility, ATR ratio.

Threshold derivado de SLIM é inválido até recalibrado em RAW.

## Indicadores sensíveis

### NAS TOP BOTTOM

Obrigatório verificar:

- campo usado;
- source (`pine_labels`, `study_values`, etc.);
- timestamp do evento;
- preço ancorado (`event_price`);
- diferença entre label visual e flag booleana;
- se o campo é evento, estado recente ou confirmação tardia.

### Market Order Bubbles

Obrigatório verificar:

- side buy/sell;
- size/rank;
- plot_id mapping;
- se large é side-specific ou genérico;
- cluster temporal;
- relação com low/high local;
- se o bubble representa pressão ativa, capitulação, absorção ou climax apenas com contexto.

### SMC / LuxAlgo

Obrigatório distinguir:

- `internal` vs `swing`;
- CHoCH vs BOS;
- direção bull/bear;
- evento novo vs estado recente;
- linha contínua estrutural vs serrilhado/interno.

### Zonas / BigBeluga / Custom OB

Obrigatório verificar:

- se a zona é literal do indicador ou proxy;
- timeframe da zona;
- high/low da zona;
- se a zona está ativa, mitigada, rompida ou sintética;
- se a distância é calculada em preço, ATR ou estado derivado;
- se o campo representa o visual real no chart.

## Source Trace Manifest

Qualquer validação séria precisa de um manifest mínimo:

- RAW file(s) usados;
- período e timeframe;
- extractor version/schema;
- campos usados;
- origem de cada campo;
- predicados exatos;
- exemplos que passam;
- exemplos que falham;
- spot-check visual/RAW.

## Status de trabalhos recentes

Qualquer lab/backtest recente dependente de SLIM-only, proxies de zona ou features interpretativas deve ser tratado como:

**EXPLORATÓRIO / SUSPEITO / NÃO VALIDADO**

até passar por RAW/source-field/visual validation.

## Regra final

Se não há rastreio RAW ou validação visual, não há validação de estratégia. Há apenas hipótese exploratória.
