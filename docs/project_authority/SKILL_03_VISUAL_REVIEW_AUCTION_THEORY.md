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
