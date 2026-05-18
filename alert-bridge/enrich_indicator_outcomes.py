#!/usr/bin/env python3
"""
enrich_indicator_outcomes.py — pos-processa indicator_signals.jsonl
adicionando outcomes (R-multiple hipotético) usando Claude headless + TV MCP.

Estratégia:
- Batch 10-20 signals por Claude call (econômico)
- Stop = ATR × 0.5 (curto, padrão SMC)
- Target = 2R
- Direction classification: long/short por signal_type; ambíguos calculam ambos lados
- Filtro de idade: signal precisa ter ≥ 20 bars desde ts_signal pra enriquecer
- Dedup: skip signals já presentes em outcomes (por signal_hash)
- Append-only em indicator_signals_outcomes.jsonl

Usage:
  python3 enrich_indicator_outcomes.py [--batch-size 15] [--dry-run] [--limit N]
"""

from pathlib import Path
from datetime import datetime, timezone, timedelta
import argparse
import fcntl
import json
import re
import subprocess
import sys
import textwrap
import time

BASE_DIR = Path.home() / "tradingview-mcp"
BRIDGE_DIR = BASE_DIR / "alert-bridge"
LOG_DIR = BRIDGE_DIR / "logs"
SIGNALS_LOG = LOG_DIR / "indicator_signals.jsonl"
OUTCOMES_LOG = LOG_DIR / "indicator_signals_outcomes.jsonl"

# 2026-05-18: CDP chart lock — same path as claude_recheck.py.
# Prevents race condition when claude_recheck (webhook-driven) and
# this enrichment script both invoke chart_set_symbol/timeframe.
# Acquired per Claude batch; released between batches to allow
# claude_recheck windows.
CHART_LOCK_PATH = "/tmp/tradingview_chart.lock"
CHART_LOCK_TIMEOUT_S = 600  # 10 min per batch (Claude may take 5+ min)


def acquire_chart_lock(timeout_s=CHART_LOCK_TIMEOUT_S):
    fd = open(CHART_LOCK_PATH, "w")
    deadline = time.monotonic() + timeout_s
    start = time.monotonic()
    while True:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return fd, round(time.monotonic() - start, 2)
        except BlockingIOError:
            if time.monotonic() >= deadline:
                fd.close()
                raise TimeoutError(f"chart lock timeout after {timeout_s}s")
            time.sleep(0.5)


def release_chart_lock(fd):
    if fd is None:
        return
    try:
        fcntl.flock(fd, fcntl.LOCK_UN)
        fd.close()
    except Exception:
        pass

# Bars window for outcome evaluation
EVAL_BARS_AFTER = 20  # need at least 20 bars after signal to enrich
EVAL_BARS_DETAIL = [1, 5, 10, 20]  # snapshots reported

# Stop loss & target
STOP_ATR_MULT = 1.0  # 2026-05-18: ajustado de 0.5 pra 1.0 (mais largo) — losers tinham MFE_R alto com stop apertado
TARGET_R = 2.0

# TF in minutes for age calculation
TF_MINUTES = {
    "15": 15,
    "30": 30,
    "60": 60,
    "240": 240,
    "1D": 1440,
    "D": 1440,
}

# Signal direction classification
LONG_SIGNALS = {
    "new_ob_bullish", "ob_bullish_mitigated",
    "Small_Buy", "Medium_Buy", "Large_Buy",
    "Bullish_Divergence",
    "Cross_Oversold_30",  # RSI exits oversold = bullish
    "NAS_LONG",
}
SHORT_SIGNALS = {
    "new_ob_bearish", "ob_bearish_mitigated",
    "Small_Sell", "Medium_Sell", "Large_Sell",
    "Bearish_Divergence",
    "Cross_Overbought_70",  # RSI exits overbought = bearish
    "NAS_SHORT",
}
# Ambiguous: calculate BOTH long and short outcomes
AMBIGUOUS_SIGNALS = {
    "Cross_Neutral_50",
    "ob_bullish_touched", "ob_bearish_touched",
    "ob_bullish_violated", "ob_bearish_violated",
}


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def parse_iso(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None


def load_jsonl(path: Path):
    if not path.exists():
        return []
    out = []
    with path.open() as f:
        for line in f:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def append_jsonl(path: Path, records):
    with path.open("a", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def classify_direction(signal_type: str) -> str:
    if signal_type in LONG_SIGNALS:
        return "long"
    if signal_type in SHORT_SIGNALS:
        return "short"
    if signal_type in AMBIGUOUS_SIGNALS:
        return "ambiguous"
    return "unknown"


def signal_is_ready(signal: dict, now: datetime) -> bool:
    """Check if signal has enough bars after ts_signal to evaluate."""
    ts = parse_iso(signal.get("ts_signal"))
    if not ts:
        return False
    tf_min = TF_MINUTES.get(str(signal.get("timeframe", "")))
    if not tf_min:
        return False
    age_minutes = (now - ts).total_seconds() / 60
    return age_minutes >= (EVAL_BARS_AFTER * tf_min)


def build_batch_prompt(signals: list) -> str:
    """Build Claude headless prompt for batch outcome evaluation."""
    sigs_compact = []
    for s in signals:
        direction = classify_direction(s.get("signal_type", ""))
        sigs_compact.append({
            "signal_hash": s.get("signal_hash"),
            "ts_signal": s.get("ts_signal"),
            "base_symbol": s.get("base_symbol"),
            "symbol_tv": s.get("symbol"),
            "timeframe": s.get("timeframe"),
            "indicator_name": s.get("indicator_name"),
            "signal_type": s.get("signal_type"),
            "entry_price": s.get("price"),
            "direction": direction,
        })

    return textwrap.dedent(f"""
    You are INDICATOR SIGNAL OUTCOME EVALUATOR.

    Goal: For each signal below, fetch OHLCV from TradingView MCP and compute
    R-multiple outcome (hypothetical, post-hoc analysis only).

    Rules (per signal):
    - Use the symbol_tv (e.g. "PEPPERSTONE:XAUUSD") and timeframe to query MCP.
    - For each signal, call: chart_set_symbol(symbol_tv), chart_set_timeframe(timeframe),
      then data_get_ohlcv(count=200) — request bars covering BEFORE and AFTER ts_signal.
    - Locate the bar matching ts_signal (or the bar that contains it).
    - Take entry_price as the close at ts_signal bar.
    - Compute ATR(14) at signal bar (rough: mean of last 14 abs(high-low)).
    - Define stop = ATR × {STOP_ATR_MULT}, target = 2R distance from entry.
    - For each direction (long/short or both for ambiguous), check the {EVAL_BARS_AFTER} bars
      after ts_signal:
      - hit_stop if price crosses stop (low <= stop for long, high >= stop for short)
      - hit_target if price crosses target (high >= target for long, low <= target for short)
      - hit_stop_first: which came first in time
      - max_favorable_R: best excursion in trade direction (R-multiples)
      - max_adverse_R: worst excursion against trade direction
      - outcome_R: 2.0 if hit_target_first, -1.0 if hit_stop_first, else max_favorable_R-max_adverse_R (timeout case)
      - outcome_label: win_2r | loss_1r | breakeven | insufficient_data

    For signal with direction="long": populate long_outcome only, short_outcome=null
    For signal with direction="short": populate short_outcome only, long_outcome=null
    For signal with direction="ambiguous": populate BOTH long_outcome AND short_outcome
    For signal with direction="unknown": skip (don't include in response)

    Also capture +1/+5/+10/+20 bar close prices (snapshots) regardless of direction.

    Signals to evaluate:
    ```json
    {json.dumps(sigs_compact, ensure_ascii=False, indent=2)}
    ```

    Output valid JSON only between markers:

    INDICATOR_OUTCOME_JSON_START
    {{
      "evaluated_at": "{now_iso()}",
      "outcomes": [
        {{
          "signal_hash": "",
          "ts_signal": "",
          "base_symbol": "",
          "timeframe": "",
          "indicator_name": "",
          "signal_type": "",
          "direction_classified": "long|short|ambiguous|unknown",
          "entry_price": null,
          "atr_at_signal": null,
          "snapshots": {{
            "close_plus_1": null,
            "close_plus_5": null,
            "close_plus_10": null,
            "close_plus_20": null
          }},
          "long_outcome": {{
            "stop_price": null,
            "target_price": null,
            "max_favorable_R": null,
            "max_adverse_R": null,
            "hit_stop_first": false,
            "hit_target_first": false,
            "outcome_R": null,
            "outcome_label": ""
          }},
          "short_outcome": {{
            "stop_price": null,
            "target_price": null,
            "max_favorable_R": null,
            "max_adverse_R": null,
            "hit_stop_first": false,
            "hit_target_first": false,
            "outcome_R": null,
            "outcome_label": ""
          }},
          "bars_evaluated": {EVAL_BARS_AFTER},
          "enrichment_notes": "",
          "enriched_at": "{now_iso()}"
        }}
      ]
    }}
    INDICATOR_OUTCOME_JSON_END
    """).strip()


def parse_response(stdout: str):
    m = re.search(
        r"INDICATOR_OUTCOME_JSON_START\s*(\{.*?\})\s*INDICATOR_OUTCOME_JSON_END",
        stdout, re.DOTALL
    )
    if not m:
        return None
    try:
        return json.loads(m.group(1).strip())
    except json.JSONDecodeError:
        return None


def run_claude_batch(prompt: str, timeout: int = 1200) -> dict:
    """Run claude headless with MCP TradingView permissions.
    Acquires CDP chart lock for the duration of the call to prevent
    race condition with claude_recheck/setup_watch_manager.
    """
    cmd = [
        "claude",
        "-p",
        prompt,
        "--allowedTools",
        "Read,mcp__tradingview__*"
    ]
    lock_fd = None
    try:
        try:
            lock_fd, wait_s = acquire_chart_lock(timeout_s=CHART_LOCK_TIMEOUT_S)
            if wait_s > 0.5:
                print(f"  (waited {wait_s}s for chart lock)")
        except TimeoutError as e:
            return {"error": f"chart_lock_timeout:{e}"}

        try:
            result = subprocess.run(
                cmd,
                cwd=str(BASE_DIR),
                text=True,
                capture_output=True,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            return {"error": "timeout"}
        except FileNotFoundError:
            return {"error": "claude_cli_not_found"}
    finally:
        release_chart_lock(lock_fd)

    if result.returncode != 0:
        return {"error": f"non_zero_exit:{result.returncode}", "stderr_tail": (result.stderr or "")[-300:]}

    parsed = parse_response(result.stdout)
    if parsed is None:
        return {"error": "parse_failed", "stdout_tail": result.stdout[-500:]}
    return parsed


def main():
    p = argparse.ArgumentParser(description="Enrich indicator_signals with R outcomes")
    p.add_argument("--batch-size", type=int, default=15)
    p.add_argument("--limit", type=int, default=None, help="Max signals to enrich this run")
    p.add_argument("--dry-run", action="store_true", help="Show plan, don't call Claude")
    p.add_argument("--timeout", type=int, default=1200)
    args = p.parse_args()

    signals = load_jsonl(SIGNALS_LOG)
    outcomes = load_jsonl(OUTCOMES_LOG)
    enriched_hashes = {o.get("signal_hash") for o in outcomes if o.get("signal_hash")}

    print(f"Total signals: {len(signals)}")
    print(f"Already enriched: {len(enriched_hashes)}")

    now = datetime.now(timezone.utc)
    pending = []
    for s in signals:
        sig_hash = s.get("signal_hash")
        if not sig_hash or sig_hash in enriched_hashes:
            continue
        if not signal_is_ready(s, now):
            continue
        if classify_direction(s.get("signal_type", "")) == "unknown":
            continue
        pending.append(s)

    print(f"Pending enrichment: {len(pending)}")
    if args.limit:
        pending = pending[:args.limit]
        print(f"Limited to: {len(pending)}")

    if args.dry_run or not pending:
        if pending:
            print("Dry-run sample (first 3):")
            for s in pending[:3]:
                print(f"  hash={s.get('signal_hash','?')[:12]} | {s.get('base_symbol')} TF{s.get('timeframe')} | {s.get('indicator_name')} {s.get('signal_type')}")
        return 0

    new_outcomes = []
    batch_count = 0
    for i in range(0, len(pending), args.batch_size):
        batch = pending[i:i + args.batch_size]
        batch_count += 1
        print(f"\n[Batch {batch_count}] Processing {len(batch)} signals...")
        prompt = build_batch_prompt(batch)
        result = run_claude_batch(prompt, timeout=args.timeout)

        if "error" in result:
            print(f"  ERROR: {result['error']}")
            if "stdout_tail" in result:
                print(f"  Stdout tail: {result['stdout_tail'][:200]}")
            continue

        outs = result.get("outcomes", [])
        print(f"  Got {len(outs)} outcomes")
        new_outcomes.extend(outs)

    if new_outcomes:
        append_jsonl(OUTCOMES_LOG, new_outcomes)
        print(f"\nAppended {len(new_outcomes)} outcomes to {OUTCOMES_LOG}")
    else:
        print("\nNo outcomes produced.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
