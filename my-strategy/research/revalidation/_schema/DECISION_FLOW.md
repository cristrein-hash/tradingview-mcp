# Revalidation Decision Flow (2 stages)

The verdict is computed in two stages. **Stage 2 is only reached if Stage 1
passes.** Metrics from a technically-invalid run are never interpreted.

```
STAGE 1 — TECHNICAL VALIDITY (hard gate)
  PASS iff ALL:
    - no_future_leak                  (every context close_epoch <= base close_epoch;
                                         RSI-1D as-of bar already closed)
    - entry_is_next_bar_open          (fill == open of signal_bar + 1; never the signal close)
    - all_stop_distance_positive      (entry - stop_price > 0 for every trade)
    - report_generated
  if NOT pass:
    result_status = "inconclusive"
    STOP. Do not interpret metrics. Record which check failed.

STAGE 2 — MERIT (only if Stage 1 passed)
  n = trades in official mode (primary) at primary target (2R)

  if n < min_n_needs_more_data (20):
      result_status = "needs_more_data"

  elif min_n_needs_more_data <= n < min_n_candidate (30):
      result_status = "inconclusive"        # moderate sample

  elif avg_r <= 0 OR profit_factor < 1.0:
      result_status = "fail"                # then recommend reject_or_downgrade
                                            # (use "reject_or_downgrade" when the
                                            #  issue is loss of justified status
                                            #  rather than total failure)

  elif (avg_r > 0 AND profit_factor >= pf_min (1.3)
        AND ex_covid_sum_r > 0 AND ex_top5_sum_r > 0
        AND n >= min_n_candidate):
      result_status = "candidate_for_VALIDATED"

  else:
      result_status = "pass"                # positive but fragile -> ACTIVE_CANDIDATE
```

## Robustness checks feeding Stage 2

- **ex-COVID**: re-aggregate excluding the 2020 COVID bucket; the edge must not
  depend on the COVID shock alone.
- **ex-top5 / ex-top10**: `sum_r` minus the 5/10 best trades; the edge must not be
  carried by a handful of outliers.
- **per-regime**: report n and expectancy per regime bucket; flag buckets with
  small n as not individually conclusive (do not promote on one regime).
- **mode comparison**: primary vs event-only signal counts; report which better
  approximates the legacy reference n.

## Output, not action

The flow writes `decision.result_status` + `recommended_catalog_transition` +
`rationale` into `report.json`, and a human-readable version into `summary.md`.
**No catalog or production file is modified by the lab.** A human applies the
transition manually (see STATUS_TAXONOMY.md).
