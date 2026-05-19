#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, timezone
import argparse
import json
import re
import subprocess
import sys
import textwrap

BASE_DIR = Path.home() / "tradingview-mcp"
BRIDGE_DIR = BASE_DIR / "alert-bridge"
STRATEGY_DIR = BASE_DIR / "my-strategy"

RESEARCH_LOG = BRIDGE_DIR / "logs/setup_research_log.jsonl"
R_OUTCOME_LOG = BRIDGE_DIR / "logs/setup_r_outcome_log.jsonl"

R_SCHEMA = STRATEGY_DIR / "research/setup_r_outcome_schema.md"
RULES = STRATEGY_DIR / "strategy_rules.json"
OP_PROMPT = STRATEGY_DIR / "operational_prompt.md"
CANDIDATE_POLICY = STRATEGY_DIR / "research/experimental/setup_candidato_forte_policy.md"


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def load_jsonl(path: Path):
    if not path.exists():
        return []

    rows = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def append_jsonl(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def parse_dt(row):
    ts = row.get("received_at") or row.get("evaluated_at")
    if not ts:
        return None
    try:
        return datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    except Exception:
        return None


# === P0.2 (2026-05-19): External factors snapshot extraction ===
# Extracts external_* fields from event's claude_stdout (where Claude echoed
# the "Macro context" block) and attaches snapshot to R outcome record so
# D2R analysis can correlate macro state with outcome without re-fetching.
# Source: setup_research_log.jsonl event.claude_stdout (free text).
# Fallback: returns {"extracted_from": "absent"} if no macro block present.

_EXT_PATTERNS = {
    "bias": re.compile(r"external_bias:\s*(\w+)"),
    "risk_level": re.compile(r"external_risk_level:\s*(\w+)"),
    "trade_validation": re.compile(r"external_trade_validation:\s*(\w+)"),
    "long_validation": re.compile(r"external_long_validation:\s*(\w+)"),
    "short_validation": re.compile(r"external_short_validation:\s*(\w+)"),
    "primary_driver": re.compile(r"external_primary_driver:\s*([\w.]+)"),
    "phase": re.compile(r"external_phase:\s*([\w._]+)"),
    "schema_version": re.compile(r"external_schema_version:\s*([\w._]+)"),
    "fetch_ok": re.compile(r"external_fetch_ok:\s*(True|False|true|false)"),
    "stale": re.compile(r"external_stale:\s*(True|False|true|false)"),
    "calendar_active": re.compile(r"external_calendar_active:\s*(True|False|true|false)"),
    "calendar_risk_level": re.compile(r"external_calendar_risk_level:\s*(\w+)"),
    "calendar_score": re.compile(r"external_calendar_score:\s*([\d.\-]+|null|None)"),
    "vix": re.compile(r"external_vix:\s*([\d.\-]+|null|None)"),
    "us10y_nominal": re.compile(r"external_us10y_nominal:\s*([\d.\-]+|null|None)"),
    "us10y_real": re.compile(r"external_us10y_real:\s*([\d.\-]+|null|None)"),
    "trade_weighted_usd": re.compile(r"external_trade_weighted_usd:\s*([\d.\-]+|null|None)"),
    "confidence": re.compile(r"external_confidence:\s*([\d.\-]+|null|None)"),
    "age_minutes": re.compile(r"external_age_minutes:\s*([\d.\-]+|null|None)"),
    "context": re.compile(r"external_context:\s*([\w|_]+)"),
}

_EXT_LIST_PATTERNS = {
    "risk_flags": re.compile(r'external_risk_flags:\s*\[([^\]]*)\]'),
    "support_flags": re.compile(r'external_support_flags:\s*\[([^\]]*)\]'),
}


def extract_external_snapshot(event):
    """Extract external_factors_v1.2 snapshot from event's claude_stdout text.

    Returns dict with extracted fields + 'extracted_from' metadata.
    If no macro block present: returns minimal stub with extracted_from='absent'.
    """
    stdout = event.get("claude_stdout") or ""
    if "external_bias" not in stdout and "Macro context" not in stdout:
        return {"extracted_from": "absent", "schema": "external_factors_v1.2"}

    snap = {"extracted_from": "stdout_regex", "schema": "external_factors_v1.2"}
    for name, pat in _EXT_PATTERNS.items():
        m = pat.search(stdout)
        if not m:
            continue
        val = m.group(1).strip()
        if val in ("null", "None"):
            val = None
        elif val.lower() in ("true", "false"):
            val = (val.lower() == "true")
        else:
            try:
                val = float(val)
            except ValueError:
                pass
        snap[name] = val

    for fname, pat in _EXT_LIST_PATTERNS.items():
        m = pat.search(stdout)
        if not m:
            continue
        content = m.group(1).strip()
        flags = re.findall(r'"([^"]+)"', content)
        if not flags and content:
            flags = [x.strip().strip('"').strip("'") for x in content.split(",") if x.strip()]
        snap[fname] = flags

    return snap


def already_evaluated_ids():
    rows = load_jsonl(R_OUTCOME_LOG)
    return {r.get("event_id") for r in rows if r.get("event_id")}


def is_test_event(event):
    text = " ".join(str(event.get(k, "")) for k in [
        "alert_type",
        "event",
        "reason",
        "expected_recheck",
        "drawing_name",
        "claude_stdout"
    ]).lower()

    markers = [
        "test_connectivity",
        "system_test",
        "teste manual",
        "teste controlado",
        "named tunnel",
        "webhook fixo",
        "ssl ok"
    ]

    return any(m in text for m in markers)


def select_events(limit, since="", classifications="", newest_first=False):
    rows = load_jsonl(RESEARCH_LOG)
    done = already_evaluated_ids()

    since_dt = None
    if since:
        since_dt = datetime.fromisoformat(since)
        if since_dt.tzinfo is None:
            since_dt = since_dt.replace(tzinfo=timezone.utc)

    class_terms = [x.strip().lower() for x in classifications.split(",") if x.strip()]

    if newest_first:
        rows = list(reversed(rows))

    selected = []

    for event in rows:
        event_id = event.get("event_id")
        if not event_id:
            continue

        if event_id in done:
            continue

        if is_test_event(event):
            continue

        if since_dt:
            dt = parse_dt(event)
            if not dt or dt < since_dt:
                continue

        if class_terms:
            text = ((event.get("classification") or "") + " " + (event.get("claude_stdout") or "")).lower()
            if not any(term in text for term in class_terms):
                continue

        selected.append(event)

        if len(selected) >= limit:
            break

    return selected


def build_prompt(events):
    return textwrap.dedent(f"""
    You are CLAUDE R-MULTIPLE SETUP OUTCOME EVALUATOR.

    Goal:
    Evaluate selected D1 trading events in theoretical R-multiple terms.

    Read these files:
    - {RULES}
    - {OP_PROMPT}
    - {CANDIDATE_POLICY}
    - {R_SCHEMA}

    Events to evaluate:
    ```json
    {json.dumps(events, ensure_ascii=False, indent=2)}
    ```

    Rules:
    - Use TradingView MCP only to fetch OHLCV/chart data needed for the evaluation.
    - Do not modify files.
    - Do not create alerts.
    - Do not draw.
    - Do not execute trades.
    - Do not use hindsight-perfect entries.
    - Use the D1 event text to infer plausible entry, stop and targets.
    - If no clear stop exists, mark no_trade or unclear.
    - If planned R:R is below 2:1, do not mark as retroactive SETUP_VALIDO.
    - Be conservative.
    - Separate tradeable setups from visually interesting but non-tradeable ideas.

    Output valid JSON only between these markers:

    R_OUTCOME_JSON_START
    {{
      "evaluated_at": "{now_iso()}",
      "r_outcomes": [
        {{
          "event_id": "",
          "evaluated_at": "{now_iso()}",
          "symbol": "",
          "timeframe": "",
          "alert_type": "",
          "drawing_name": "",
          "classification_at_signal": "",
          "direction": "long|short|breakout|breakdown|unknown",
          "entry_model": "zone_touch|reentry|confirmation_close|breakout_retest|line_break|unknown",
          "entry_price": null,
          "stop_price": null,
          "target_1_price": null,
          "target_2_price": null,
          "risk_points": null,
          "reward_1_points": null,
          "reward_2_points": null,
          "planned_rr_1": null,
          "planned_rr_2": null,
          "max_favorable_r": null,
          "max_adverse_r": null,
          "hit_stop": false,
          "hit_1r": false,
          "hit_2r": false,
          "hit_target_1": false,
          "hit_target_2": false,
          "hit_stop_first": false,
          "hit_target_1_first": false,
          "hit_target_2_first": false,
          "theoretical_r_outcome": null,
          "r_outcome_label": "win_2r|win_1r|loss_1r|breakeven|no_trade|unclear|insufficient_data",
          "would_have_been_tradeable": false,
          "why_tradeable_or_not": "",
          "setup_valid_retro": false,
          "candidate_strong_retro": false,
          "main_blocker_was_valid": true,
          "blocker_assessment": "",
          "suggested_learning": "",
          "should_review_manually": false
        }}
      ]
    }}
    R_OUTCOME_JSON_END
    """).strip()


def parse_json(stdout):
    match = re.search(
        r"R_OUTCOME_JSON_START\s*(\{.*?\})\s*R_OUTCOME_JSON_END",
        stdout,
        re.DOTALL
    )
    if not match:
        return None

    try:
        return json.loads(match.group(1).strip())
    except json.JSONDecodeError:
        return None


def main():
    parser = argparse.ArgumentParser(description="Evaluate D1 events in R-multiple terms")
    parser.add_argument("--limit", type=int, default=1)
    parser.add_argument("--since", default="2026-05-04")
    parser.add_argument("--classifications", default="SETUP_CANDIDATO_FORTE,SETUP_EM_OBSERVACAO,SETUP EM OBSERVAÇÃO")
    parser.add_argument("--newest-first", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--timeout", type=int, default=900)
    args = parser.parse_args()

    events = select_events(
        limit=args.limit,
        since=args.since,
        classifications=args.classifications,
        newest_first=args.newest_first
    )

    if not events:
        print("Nenhum evento elegível para D2R.")
        return

    if args.dry_run:
        print(f"Eventos selecionados para D2R: {len(events)}")
        for e in events:
            print("-", e.get("event_id"), e.get("symbol"), e.get("timeframe"), e.get("alert_type"), "|", e.get("classification"))
        return

    prompt = build_prompt(events)

    cmd = [
        "claude",
        "-p",
        prompt,
        "--allowedTools",
        "Read,mcp__tradingview__*"
    ]

    try:
        result = subprocess.run(
            cmd,
            cwd=str(BASE_DIR),
            text=True,
            capture_output=True,
            timeout=args.timeout
        )
    except subprocess.TimeoutExpired:
        print(f"Erro: D2R excedeu timeout de {args.timeout}s.")
        sys.exit(1)

    stdout = (result.stdout or "").strip()
    stderr = (result.stderr or "").strip()

    if result.returncode != 0:
        print("Claude retornou erro.")
        print(stderr)
        sys.exit(result.returncode)

    parsed = parse_json(stdout)
    if not parsed:
        print("Erro: não consegui extrair R_OUTCOME_JSON.")
        print(stdout[-3000:])
        sys.exit(1)

    rows = parsed.get("r_outcomes", [])
    if not rows:
        print("Nenhum R outcome retornado.")
        return

    done = already_evaluated_ids()
    fresh = [r for r in rows if r.get("event_id") not in done]

    # P0.2 (2026-05-19): attach external_factors snapshot to each fresh outcome
    # so D2R analysis can correlate macro context with R outcome.
    # Source: claude_stdout of the originating event in setup_research_log.
    event_by_id = {e.get("event_id"): e for e in events if e.get("event_id")}
    for r in fresh:
        ev = event_by_id.get(r.get("event_id"))
        if ev is not None:
            r["external_factors_snapshot"] = extract_external_snapshot(ev)
        else:
            r["external_factors_snapshot"] = {"extracted_from": "no_source_event", "schema": "external_factors_v1.2"}

    if fresh:
        append_jsonl(R_OUTCOME_LOG, fresh)

    print(f"Eventos avaliados D2R: {len(events)}")
    print(f"R outcomes recebidos: {len(rows)}")
    print(f"R outcomes novos salvos: {len(fresh)}")
    print(f"Arquivo: {R_OUTCOME_LOG}")


if __name__ == "__main__":
    main()
