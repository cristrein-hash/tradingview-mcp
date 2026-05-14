#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
import json
import collections

BASE = Path.home() / "tradingview-mcp"
R_LOG = BASE / "alert-bridge/logs/setup_r_outcome_log.jsonl"
OUT_DIR = BASE / "my-strategy/research/daily"


def load_jsonl(path):
    rows = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except Exception:
            pass
    return rows


def safe(v):
    return "" if v is None else str(v)


def short(text, n=280):
    text = text or ""
    return text if len(text) <= n else text[:n].rstrip() + "..."


def main():
    rows = load_jsonl(R_LOG)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    today = datetime.now().strftime("%Y-%m-%d")
    out = OUT_DIR / f"{today}_D2R_summary.md"

    labels = collections.Counter(r.get("r_outcome_label") for r in rows)
    symbols = collections.Counter(r.get("symbol") for r in rows)
    tradeable = collections.Counter(str(r.get("would_have_been_tradeable")) for r in rows)
    retro = collections.Counter(str(r.get("setup_valid_retro")) for r in rows)
    blocker = collections.Counter(str(r.get("main_blocker_was_valid")) for r in rows)

    total_r = 0
    r_count = 0
    for r in rows:
        val = r.get("theoretical_r_outcome")
        if isinstance(val, (int, float)):
            total_r += val
            r_count += 1

    avg_r = round(total_r / r_count, 2) if r_count else None

    setup_valid_retro = [r for r in rows if r.get("setup_valid_retro")]
    blocker_false = [r for r in rows if r.get("main_blocker_was_valid") is False]
    wins = [r for r in rows if r.get("r_outcome_label") in ("win_2r", "win_1r")]
    losses = [r for r in rows if r.get("r_outcome_label") == "loss_1r"]

    lines = []
    lines.append("# D2R Summary — R-Multiple Backtest")
    lines.append("")
    lines.append(f"Generated: {datetime.now().isoformat(timespec='seconds')}")
    lines.append(f"Source: `{R_LOG}`")
    lines.append("")
    lines.append("## 1. Executive Summary")
    lines.append("")
    lines.append(f"- Total D2R events: **{len(rows)}**")
    lines.append(f"- Total theoretical R: **{round(total_r, 2)}R**")
    lines.append(f"- Average R/event: **{avg_r}R**")
    lines.append(f"- Tradeable events: **{tradeable.get('True', 0)}**")
    lines.append(f"- Non-tradeable events: **{tradeable.get('False', 0)}**")
    lines.append(f"- Retroactive SETUP_VALIDO: **{retro.get('True', 0)}**")
    lines.append(f"- Excessive/invalid blockers: **{blocker.get('False', 0)}**")
    lines.append("")
    lines.append("## 2. Outcome Distribution")
    lines.append("")
    for k, v in labels.most_common():
        lines.append(f"- {k}: {v}")
    lines.append("")
    lines.append("## 3. Symbols")
    lines.append("")
    for k, v in symbols.most_common():
        lines.append(f"- {k or 'EMPTY'}: {v}")
    lines.append("")
    lines.append("## 4. Setup Valid Retro — Key Cases")
    lines.append("")
    if not setup_valid_retro:
        lines.append("No setup_valid_retro cases found.")
    for r in setup_valid_retro:
        lines.append("### " + safe(r.get("symbol")) + " " + safe(r.get("timeframe")) + " — " + safe(r.get("direction")))
        lines.append("")
        lines.append(f"- event_id: `{r.get('event_id')}`")
        lines.append(f"- label: **{r.get('r_outcome_label')}**")
        lines.append(f"- R: **{r.get('theoretical_r_outcome')}**")
        lines.append(f"- entry: {r.get('entry_price')}")
        lines.append(f"- stop: {r.get('stop_price')}")
        lines.append(f"- target 1: {r.get('target_1_price')}")
        lines.append(f"- blocker valid: {r.get('main_blocker_was_valid')}")
        lines.append(f"- learning: {short(r.get('suggested_learning'), 500)}")
        lines.append("")
    lines.append("## 5. Excessive Blockers")
    lines.append("")
    if not blocker_false:
        lines.append("No blocker_valid=false cases found.")
    for r in blocker_false:
        lines.append("### " + safe(r.get("symbol")) + " " + safe(r.get("timeframe")) + " — " + safe(r.get("direction")))
        lines.append("")
        lines.append(f"- event_id: `{r.get('event_id')}`")
        lines.append(f"- label: **{r.get('r_outcome_label')}**")
        lines.append(f"- R: **{r.get('theoretical_r_outcome')}**")
        lines.append(f"- setup_valid_retro: {r.get('setup_valid_retro')}")
        lines.append(f"- blocker assessment: {short(r.get('blocker_assessment'), 600)}")
        lines.append(f"- learning: {short(r.get('suggested_learning'), 500)}")
        lines.append("")
    lines.append("## 6. Wins")
    lines.append("")
    for r in wins:
        lines.append(f"- **{r.get('symbol')} {r.get('timeframe')} {r.get('direction')}** — {r.get('r_outcome_label')} / R={r.get('theoretical_r_outcome')} / tradeable={r.get('would_have_been_tradeable')} / setup_valid_retro={r.get('setup_valid_retro')}")
    lines.append("")
    lines.append("## 7. Losses")
    lines.append("")
    for r in losses:
        lines.append(f"- **{r.get('symbol')} {r.get('timeframe')} {r.get('direction')}** — R={r.get('theoretical_r_outcome')} / tradeable={r.get('would_have_been_tradeable')} / blocker_valid={r.get('main_blocker_was_valid')}")
    lines.append("")
    lines.append("## 8. Preliminary Interpretation")
    lines.append("")
    lines.append("- Most events are still not tradeable at the alert moment.")
    lines.append("- The strategy should not be globally loosened.")
    lines.append("- The useful improvement is a promotion path from SETUP_CANDIDATO_FORTE to SETUP_VALIDO after objective confirmation.")
    lines.append("- D2R should continue running until at least 50 events before any final rule change.")
    lines.append("")
    lines.append("## 9. Next Actions")
    lines.append("")
    lines.append("- Continue D2R backfill.")
    lines.append("- Review setup_valid_retro cases manually with screenshots.")
    lines.append("- Review blocker_valid=false cases manually.")
    lines.append("- Prepare D4 promotion-policy experiment, but do not modify strategy_rules.json yet.")
    lines.append("")

    out.write_text("\n".join(lines), encoding="utf-8")

    print("D2R summary created:")
    print(out)


if __name__ == "__main__":
    main()
