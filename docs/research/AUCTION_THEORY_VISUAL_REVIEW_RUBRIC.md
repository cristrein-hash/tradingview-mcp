# Auction Theory Visual Review Rubric

## 1. Objective

Use Auction Theory as the **primary lens** for reviewing trades visually
on the chart, BEFORE any quantitative filter is proposed or modified.

This rubric exists so that data and indicators serve to **validate
hypotheses rooted in Auction Theory** — not to invent mechanical trades
disconnected from how the market actually trades.

If a trade does not pass this rubric, no amount of statistical edge
justifies including it. The strategy itself is what's wrong, not the
parameters.

## 2. GOOD LONG BREAKOUT — required visual signs

A long breakout is considered "GOOD" only when **all** of these are
visually true on the candle of the signal:

- Breaks a **structurally relevant** level (swing high, range high,
  prior supply, key liquidity).
- There is **acceptance above** that level — price holds above on the
  next 1-3 bars rather than immediately wicking back inside.
- There is **clean space** to the next significant supply / overhead
  resistance (target is reachable without crossing dense opposing
  evidence).
- Price is **not in a top / exhaustion** zone (no immediately prior
  blow-off candle, no parabolic extension, no clear distribution
  pattern above).
- There are **no excessive opposite signals immediately overhead**
  (no dense TOP labels, no clustered SHORT zones, no obvious
  resistance acting just above the breakout).
- The move looks like **initiative buying** — strong body, clear
  direction, follow-through — not a **stop-run** or a wick-driven
  fakeout.

## 3. BAD LONG BREAKOUT — visual rejection signs

Any of these is enough to start questioning the trade. **Three or more
present → AUCTION_REJECT** (see §6).

- Buy **at the top** of a multi-week rally with no pullback.
- Buy **after a vertical extension** (multiple consecutive large
  bullish candles without correction).
- **Multiple TOP / SHORT signals** clustered in the immediately
  preceding bars or just above current price.
- **RSI Bear / bearish divergence / exhaustion** signs on or just
  before the signal candle.
- **Supply zone overhead, close to entry** — target lies inside or
  beyond an obvious supply block that the strategy ignores.
- **Rompimento sem aceitação** — break of the level with NO
  follow-through; price returns inside the range within 1-2 bars.
- Price **returns quickly to inside the prior range** after the
  breakout candle (failed acceptance).
- The trade thesis depends on **continuation perfection** — there
  is no margin for normal post-breakout retracement; any pullback
  hits stop.

## 4. Visual classification (one per trade)

Each reviewed trade is tagged with exactly one of:

| Tag | Meaning |
|---|---|
| `GOOD_ACCEPTED_BREAKOUT` | All §2 criteria visually met; clean initiative move with acceptance and overhead space. |
| `BAD_TOP_EXHAUSTION` | Buy at the top of an extended rally; exhaustion signs present. |
| `BAD_RANGE_BREAKOUT` | Breakout from a chop range with no real acceptance; price returns to range. |
| `BAD_SUPPLY_OVERHEAD` | Supply / TOP / SHORT cluster sits directly above the entry; no clean path to target. |
| `BAD_LATE_ENTRY` | Move already extended for several bars before the signal; chasing the trade. |
| `UNCLEAR` | Visual evidence is mixed or insufficient; defer judgement, do not auto-classify. |

`UNCLEAR` is preferable to forcing a tag. Do not infer auction context
from the strategy's own rules — the rubric is independent.

## 5. 5-question visual checklist

For each trade under review, answer these in order. Each answer is
`yes / no / unclear`.

1. **Location:** Is the entry in a **discount / mid-range / premium**
   relative to the higher timeframe range? (Discount = good; premium =
   suspect; mid = depends.)
2. **Acceptance:** Did price **break and accept** above the level
   (held above on the next bar(s))? (Yes = good; no = bad.)
3. **Quality of the move:** Does the signal candle look like
   **initiative** (clean body, strong follow-through) or **exhaustion
   / stop-run** (long wick, blow-off, immediate reversal)? (Initiative
   = good.)
4. **Overhead supply:** Are there **clear sell signals overhead** —
   dense TOP / SHORT labels, prior supply blocks, RSI Bear — within
   reach of the target? (Yes = bad.)
5. **Space:** Is there **clean space** to the target without crossing
   obvious opposing evidence? (Yes = good.)

The five answers are recorded next to the trade in any review notes.

## 6. Decision rule

- **0-2 negative answers** → trade is plausible from an Auction Theory
  standpoint. Tag with the best §4 label (`GOOD_ACCEPTED_BREAKOUT` if
  no clearly negative answers).
- **3 or more negative answers (including "yes" on Q4 or "no" on Q2)**
  → **`AUCTION_REJECT`**. The trade fails the rubric regardless of
  what backtest statistics say about it.
- **Predominantly `unclear` answers** → tag as `UNCLEAR` in §4 and
  exclude from auction-based promotion decisions. Defer rather than
  guess.

The strategy as a whole is judged by the **proportion of trades that
are `AUCTION_REJECT`**, not by overall R or PF.

## 7. What this rubric is NOT

- It is **not** a filter to be coded into a strategy directly. Auction
  Theory criteria are visual and contextual; mechanizing them naively
  produces another rigid rule and recreates the original problem.
- It is **not** a substitute for backtest evidence. It is an
  **upstream gate**: a strategy without an auction-theory thesis
  should not be backtested at all.
- It is **not** about being right on every trade. Even a good
  auction-aligned trade can lose. The rubric judges whether the
  trade *makes sense to take*, not whether it wins.

## 8. The framing principle

> Data and indicators validate hypotheses rooted in Auction Theory.
> They do not invent strategies on their own.

Any future strategy proposal must first state its **auction thesis**
(where the trade fits in the auction: premium/discount, initiative/
responsive, acceptance/rejection, absorption/defense, exhaustion,
location) before any quantitative validation begins.
