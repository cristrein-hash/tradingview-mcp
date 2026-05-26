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
import os
import re
import signal
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
EVAL_BARS_AFTER = 20  # legacy default (kept for backward compat with old records)
EVAL_BARS_DETAIL = [1, 5, 10, 20]  # snapshots reported

# Stop loss & target (legacy single-ATR — preserved for retro-compat)
STOP_ATR_MULT = 1.0  # 2026-05-18: 0.5 -> 1.0; losers had high MFE_R with tight stop
TARGET_R = 2.0

# 2026-05-19: B+C+D+E enrichment — multi-lens outcome measurement
# B: outcomes_by_atr_mult — 3 stop scenarios (1x, 2x, 3x ATR)
ATR_MULT_SCENARIOS = [1.0, 2.0, 3.0]
# C: potential_direction — max favorable excursion in window, no stop applied
# D: proportional eval window by TF (function eval_bars_for_tf)
# E: structural stop — last swing low/high in 30 bars before signal,
#    with fallback to 2x ATR if no swing found
STRUCTURAL_LOOKBACK_BARS = 30
STRUCTURAL_PIVOT_SIDE = 3  # bars on each side that must be higher (long) / lower (short)
STRUCTURAL_BUFFER_ATR_FRAC = 0.10  # stop = swing +/- 10% of ATR
STRUCTURAL_FALLBACK_ATR_MULT = 2.0  # if no swing found in lookback

# TF in minutes for age calculation
TF_MINUTES = {
    "15": 15,
    "30": 30,
    "60": 60,
    "240": 240,
    "1D": 1440,
    "D": 1440,
}


def eval_bars_for_tf(tf_str: str) -> int:
    """Window size proportional to TF (D, added 2026-05-19).
    Shorter TFs need fewer bars (less real time); longer TFs need more.
        15M -> 20 bars (5h real time)
        30M -> 20 bars (10h)
        1H  -> 40 bars (~1.7d)
        4H  -> 80 bars (~13d)
        1D  -> 160 bars (~32 weeks)
    """
    tf_min = TF_MINUTES.get(str(tf_str), 60)
    if tf_min <= 30:
        return 20
    if tf_min <= 60:
        return 40
    if tf_min <= 240:
        return 80
    return 160

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
    """Check if signal has enough bars after ts_signal to evaluate.
    Uses proportional window (D): 20 bars for 15M/30M, 40 for 1H, 80 for 4H, 160 for 1D.
    """
    ts = parse_iso(signal.get("ts_signal"))
    if not ts:
        return False
    tf_str = str(signal.get("timeframe", ""))
    tf_min = TF_MINUTES.get(tf_str)
    if not tf_min:
        return False
    eval_bars = eval_bars_for_tf(tf_str)
    age_minutes = (now - ts).total_seconds() / 60
    return age_minutes >= (eval_bars * tf_min)


def build_batch_prompt(signals: list) -> str:
    """Build Claude headless prompt for batch outcome evaluation (B+C+D+E, 2026-05-19)."""
    sigs_compact = []
    for s in signals:
        direction = classify_direction(s.get("signal_type", ""))
        tf_str = str(s.get("timeframe", ""))
        sigs_compact.append({
            "signal_hash": s.get("signal_hash"),
            "ts_signal": s.get("ts_signal"),
            "base_symbol": s.get("base_symbol"),
            "symbol_tv": s.get("symbol"),
            "timeframe": tf_str,
            "indicator_name": s.get("indicator_name"),
            "signal_type": s.get("signal_type"),
            "entry_price": s.get("price"),
            "direction": direction,
            "eval_bars": eval_bars_for_tf(tf_str),  # D: proportional window
        })

    atr_scenarios_str = ", ".join(f"{m}x" for m in ATR_MULT_SCENARIOS)

    return textwrap.dedent(f"""
    You are INDICATOR SIGNAL OUTCOME EVALUATOR v2 (multi-lens, 2026-05-19).

    Goal: For each signal below, fetch OHLCV from TradingView MCP and compute
    FOUR DIMENSIONS of R-multiple outcome (hypothetical, post-hoc analysis only).

    === MCP FETCH (per signal) ===
    - Use the symbol_tv (e.g. "PEPPERSTONE:XAUUSD") and timeframe to query MCP.
    - Call: chart_set_symbol(symbol_tv), chart_set_timeframe(timeframe),
      data_get_ohlcv(count=200) — request bars covering BEFORE and AFTER ts_signal.
    - Locate the bar at ts_signal (or the bar that contains it).
    - entry_price = close at ts_signal bar.
    - atr_at_signal = mean of last 14 abs(high-low) before signal bar (rough ATR).
    - eval_bars = field provided in each signal (D: 20/40/80/160 by TF).

    === DIMENSION B — outcomes_by_atr_mult (3 stop scenarios) ===
    For each signal with direction="long" or "short", compute outcome at THREE stops:
      {atr_scenarios_str} ATR multiples.
    For each scenario:
      stop_price = entry +/- (atr_at_signal × multiplier)   [- for long, + for short]
      target_price = entry +/- (atr_at_signal × multiplier × 2)  [2R fixed]
      Scan the next eval_bars after signal:
        hit_stop_first if low<=stop (long) or high>=stop (short) reached first
        hit_target_first if high>=target (long) or low<=target (short) reached first
        max_favorable_R: best move in trade direction, in R units
        max_adverse_R: worst move against direction, in R units
        outcome_R:
          +2.0 if hit_target_first
          -1.0 if hit_stop_first
          (max_favorable_R - max_adverse_R) if neither (timeout)
        outcome_label: win_2r | loss_1r | breakeven | timeout
        bars_to_resolve: bar offset of first hit (or eval_bars if timeout)

    === DIMENSION C — potential_direction (no stop applied) ===
    For each signal with direction="long" or "short":
      Scan eval_bars after signal, find PEAK favorable excursion regardless of any stop.
        max_favorable_R_no_stop = peak distance from entry in trade direction / atr_at_signal
        bar_to_peak: bar offset of peak (0..eval_bars-1)
        was_direction_correct: true if max_favorable_R_no_stop >= 1.0, else false
      This measures pure directional edge of the signal.

    === DIMENSION E — outcome_structural (swing-based stop with fallback) ===
    For each signal with direction="long" or "short":
      Look BACK up to {STRUCTURAL_LOOKBACK_BARS} bars BEFORE signal bar.
      For LONG: find lowest pivot low — a low with {STRUCTURAL_PIVOT_SIDE} bars on each side
        having higher lows. swing_price = that pivot low.
        stop_price = swing_price - (atr_at_signal × {STRUCTURAL_BUFFER_ATR_FRAC})
      For SHORT: find highest pivot high — a high with {STRUCTURAL_PIVOT_SIDE} bars on each side
        having lower highs. swing_price = that pivot high.
        stop_price = swing_price + (atr_at_signal × {STRUCTURAL_BUFFER_ATR_FRAC})
      If NO valid pivot found: fallback to {STRUCTURAL_FALLBACK_ATR_MULT}x ATR stop. Set fallback_used=true.
      stop_distance_R = abs(entry - stop_price) / atr_at_signal
      target_price = entry +/- (stop_distance_R × atr_at_signal × 2)   [2:1 risk:reward]
      Scan next eval_bars, compute outcome_R / outcome_label / hit_stop_first / hit_target_first
      using the structural stop (not ATR-based).

    === LEGACY OUTCOMES (preserved for backward compat — DO NOT REMOVE) ===
    Also populate long_outcome / short_outcome using legacy formula:
      stop = atr_at_signal × {STOP_ATR_MULT}, target = 2R, eval over eval_bars.
    For direction="long": long_outcome populated, short_outcome=null
    For direction="short": short_outcome populated, long_outcome=null
    For direction="ambiguous": BOTH populated (legacy behavior).
      For ambiguous signals, set outcomes_by_atr_mult / potential_direction /
      outcome_structural to null (those new lenses don't apply to ambiguous).
    For direction="unknown": skip (don't include in response).

    === SNAPSHOTS (always) ===
    Capture +1/+5/+10/+20 bar close prices regardless of direction.

    === SIGNALS TO EVALUATE ===
    ```json
    {json.dumps(sigs_compact, ensure_ascii=False, indent=2)}
    ```

    === OUTPUT FORMAT ===
    Output valid JSON only between markers.

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
          "bars_evaluated": null,
          "snapshots": {{
            "close_plus_1": null,
            "close_plus_5": null,
            "close_plus_10": null,
            "close_plus_20": null
          }},
          "long_outcome": {{
            "stop_price": null, "target_price": null,
            "max_favorable_R": null, "max_adverse_R": null,
            "hit_stop_first": false, "hit_target_first": false,
            "outcome_R": null, "outcome_label": ""
          }},
          "short_outcome": {{
            "stop_price": null, "target_price": null,
            "max_favorable_R": null, "max_adverse_R": null,
            "hit_stop_first": false, "hit_target_first": false,
            "outcome_R": null, "outcome_label": ""
          }},
          "outcomes_by_atr_mult": {{
            "1x_atr": {{
              "stop_price": null, "target_price": null,
              "max_favorable_R": null, "max_adverse_R": null,
              "hit_stop_first": false, "hit_target_first": false,
              "outcome_R": null, "outcome_label": "",
              "bars_to_resolve": null
            }},
            "2x_atr": {{
              "stop_price": null, "target_price": null,
              "max_favorable_R": null, "max_adverse_R": null,
              "hit_stop_first": false, "hit_target_first": false,
              "outcome_R": null, "outcome_label": "",
              "bars_to_resolve": null
            }},
            "3x_atr": {{
              "stop_price": null, "target_price": null,
              "max_favorable_R": null, "max_adverse_R": null,
              "hit_stop_first": false, "hit_target_first": false,
              "outcome_R": null, "outcome_label": "",
              "bars_to_resolve": null
            }}
          }},
          "potential_direction": {{
            "max_favorable_R_no_stop": null,
            "bar_to_peak": null,
            "was_direction_correct": false
          }},
          "outcome_structural": {{
            "swing_found": false,
            "swing_price": null,
            "swing_bar_offset": null,
            "stop_distance_R": null,
            "stop_price": null,
            "target_price": null,
            "max_favorable_R": null,
            "max_adverse_R": null,
            "hit_stop_first": false,
            "hit_target_first": false,
            "outcome_R": null,
            "outcome_label": "",
            "fallback_used": false
          }},
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


def _kill_process_group(proc) -> None:
    """Kill a Popen and its WHOLE process group so the claude CLI's MCP server
    (node src/server.js) grandchild is never left orphaned. Relies on the Popen
    having been started with start_new_session=True (child PGID == child PID).
    Safe to call when proc is None or already dead. Logs cleanup without secrets.
    """
    if proc is None:
        return
    pgid = proc.pid  # == PGID because Popen used start_new_session=True

    def _signal_group(sig) -> bool:
        try:
            os.killpg(pgid, sig)
            return True
        except (ProcessLookupError, PermissionError, OSError):
            return False  # group already gone

    if not _signal_group(signal.SIGTERM):
        return
    try:
        proc.wait(timeout=5)
    except (subprocess.TimeoutExpired, Exception):
        pass
    # SIGKILL the group to catch any lingering grandchild (e.g. the MCP server.js)
    _signal_group(signal.SIGKILL)
    try:
        proc.wait(timeout=2)
    except (subprocess.TimeoutExpired, Exception):
        pass
    print("  [cleanup] claude process group terminated")


def run_claude_batch(prompt: str, timeout: int = 1200) -> dict:
    """Run claude headless with MCP TradingView permissions.
    Acquires CDP chart lock for the duration of the call to prevent
    race condition with claude_recheck/setup_watch_manager.

    The claude CLI spawns its MCP server (node src/server.js) as a child; without
    its own process group that grandchild is orphaned on timeout/exit. We start
    claude in a new session (own PGID) and kill the whole group in finally, so no
    server.js is left behind. Evaluation logic and output schema are unchanged.
    """
    cmd = [
        "claude",
        "-p",
        prompt,
        "--allowedTools",
        "Read,mcp__tradingview__*"
    ]
    lock_fd = None
    proc = None
    rc = None
    stdout = ""
    stderr = ""
    try:
        try:
            lock_fd, wait_s = acquire_chart_lock(timeout_s=CHART_LOCK_TIMEOUT_S)
            if wait_s > 0.5:
                print(f"  (waited {wait_s}s for chart lock)")
        except TimeoutError as e:
            return {"error": f"chart_lock_timeout:{e}"}

        try:
            proc = subprocess.Popen(
                cmd,
                cwd=str(BASE_DIR),
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True,  # own process group -> grandchildren killable
            )
        except FileNotFoundError:
            return {"error": "claude_cli_not_found"}

        try:
            stdout, stderr = proc.communicate(timeout=timeout)
            rc = proc.returncode
        except subprocess.TimeoutExpired:
            return {"error": "timeout"}
    finally:
        _kill_process_group(proc)  # claude + its MCP server.js, no orphans
        release_chart_lock(lock_fd)

    if rc != 0:
        return {"error": f"non_zero_exit:{rc}", "stderr_tail": (stderr or "")[-300:]}

    parsed = parse_response(stdout)
    if parsed is None:
        return {"error": "parse_failed", "stdout_tail": stdout[-500:]}
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
