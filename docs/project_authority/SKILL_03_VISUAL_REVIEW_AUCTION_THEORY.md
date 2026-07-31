# SKILL 03 — Visual Review / Auction Theory

**Purpose:** Validate whether mechanical trades actually match market auction logic.

## Core Rule

```text
A backtest number is not enough.
A trade must make auction sense.
```

## Auction Review Dimensions

For each trade/checkpoint, inspect:

1. **Location**
   - premium/discount
   - demand/supply
   - range position
   - proximity to opposite zone

2. **Acceptance / Rejection**
   - reclaim
   - retest hold
   - failure to continue
   - clean rejection

3. **Initiative / Responsive**
   - breakout/initiative buying
   - responsive buying at demand
   - exhaustion/reversal

4. **Pressure**
   - bubbles showing aggression
   - aggression failing or continuing
   - seller/buyer pressure shrinking or expanding

   **REGRA DE POLARIDADE DE BUBBLES — CONTEXTO-DEPENDENTE (canónica; validada 2026-06-03, n=1163 XAU 4H; memory `feedback_bubbles_polarity_rule`; código: `alert-bridge/bubble_polarity.py`).**
   A cor da bubble por si só NÃO é o sinal — o sinal é se a agressão está a ser **absorvida** num nível (reversão) ou a **continuar** com a perna (pullback). Classifica o CONTEXTO primeiro, depois aplica a polaridade. NUNCA "sell=bearish" nem "LONG exige buy-cluster" como regra fixa (foi o bug de 2026-06-03). Mapeamento cru: BUY=plot_0/2/4, SELL=plot_6/8/10.
   - **Reversal-em-fundo** (drawdown/capitulação/fundo em demanda 4H/1D, RSI oversold): **SELL-bubble absorvido = BULLISH** (agressão vendedora no low absorvida por limit-buyers = acumulação); BUY-bubble = anti-padrão. → um LONG de reversão-em-fundo com SELL absorvido está CONFIRMADO, não bloqueado por "falta de buy-cluster".
   - **Pullback em uptrend** (demanda em regime BULL, continuação): **BUY-bubble = BULLISH**; SELL = neutro.
   - **Reversal-em-topo** (SHORT em supply, RSI overbought): **BUY-bubble absorvido = BEARISH** (distribuição); SELL = anti-padrão.
   - **GUARDA (absorção ≠ faca):** "absorvido" exige reclaim/hold ≥2 barras fechadas no nível. Vertical news-driven (FOMC-spike, high_impact) que atravessa o nível = FACA/continuação, não absorção.

5. **Structure**
   - BOS
   - CHoCH
   - internal vs swing
   - structural continuation vs noise

6. **Timing**
   - early
   - good
   - late
   - chasing
   - falling knife

7. **Risk / Space**
   - stop makes sense
   - target has room
   - next supply/demand in path

## Classification Tags

Use concise tags:

```text
REAL_AUCTION_ACCEPT
GOOD_REJECTION
GOOD_RECLAIM
LATE_ENTRY
FALLING_KNIFE
TOP_EXHAUSTION
SUPPLY_OVERHEAD
NO_REAL_RECLAIM
WEAK_STRUCTURE
UNCLEAR
```

## Visual Review Sample

For a strategy candidate:

```text
10 winners
10 losers
5 borderline
key rejected examples
key false positives/false negatives
```

If sample is tiny, review all trades.

## Output Format

Keep it short:

```text
what looked valid
what looked invalid
main failure mode
one next test
```

## Do Not

- over-explain screenshots;
- create new filters during review unless asked;
- call visual impressions “validated”;
- ignore user visual judgment.
