#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, timezone, timedelta
import argparse
import json
import time
import urllib.request
import urllib.error

BASE = Path.home() / "tradingview-mcp"
BRIDGE = BASE / "alert-bridge"
LOGS = BRIDGE / "logs"

RESEARCH_LOG = LOGS / "setup_research_log.jsonl"
WATCH_STATE = LOGS / "setup_watch_state.json"
WATCH_LOG = LOGS / "setup_watch_log.jsonl"

LOCAL_WEBHOOK = "http://127.0.0.1:8787/webhook/local-test"


def now_utc():
    return datetime.now(timezone.utc)


def parse_ts(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except Exception:
        return None


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


def append_jsonl(path, row):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def load_state():
    if not WATCH_STATE.exists():
        return {"watches": {}}
    try:
        return json.loads(WATCH_STATE.read_text(encoding="utf-8"))
    except Exception:
        return {"watches": {}}


def save_state(state):
    WATCH_STATE.parent.mkdir(parents=True, exist_ok=True)
    WATCH_STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def text_of(row):
    return "\n".join([
        row.get("classification") or "",
        row.get("direction") or "",
        row.get("main_blocker") or "",
        row.get("next_action") or "",
        row.get("telegram_reason") or "",
        row.get("claude_stdout") or "",
    ])


def line_value(stdout, prefix):
    for line in (stdout or "").splitlines():
        if line.strip().lower().startswith(prefix.lower()):
            return line.split(":", 1)[1].strip() if ":" in line else line.strip()
    return ""


def is_bad_for_watch(row):
    text = text_of(row).lower()
    alert_type = (row.get("alert_type") or "").lower()

    bad_terms = [
        "test_connectivity",
        "teste recebido",
        "system_test",
        "setup_perdido_nao_perseguir",
        "setup perdido",
        "não perseguir",
        "nao perseguir",
        "entrada atrasada: sim",
        "promotion status: no_trade",
        "no_trade",
        "test_or_non_operational",
        "setup_watch_recheck",
    ]

    if "test" in alert_type:
        return True

    return any(t in text for t in bad_terms)


def is_fresh(row, create_grace_minutes):
    received_at = parse_ts(row.get("received_at"))
    if not received_at:
        return False
    return now_utc() - received_at <= timedelta(minutes=create_grace_minutes)


def is_watch_candidate(row):
    if is_bad_for_watch(row):
        return False

    text = text_of(row)
    low = text.lower()
    alert_type = (row.get("alert_type") or "").lower()

    # Strong candidates (V3 canonical + legacy aliases for backward compat).
    strong_terms = [
        "setup_candidato_forte",
        "setup_candidato_forte_intraday",  # legacy alias — maps to SETUP_CANDIDATO_FORTE
        "candidato forte: sim",
        "priority: a",
        "priority: b",
        "promotion status: keep_as_candidato_forte",
    ]

    if any(t in low for t in strong_terms):
        return True

    # PREPARE / OBSERVATION watches:
    # This is the important fix. A zone touch can be observation now,
    # but become entry on the next 15M candle close.
    operational_alert = alert_type in [
        "monitor_dynamic_bb_zone",
        "monitor_zone",
        "monitor_dynamic_line",
        "monitor_trendline_lta",
        "monitor_trendline_ltb",
        "monitor_breakout",
        "monitor_invalidation",
    ]

    missing_trigger_terms = [
        "gatilho faltante",
        "trigger faltante",
        "rejection close",
        "sweep",
        "reentry",
        "choch",
        "bos",
        "retest",
        "reteste",
        "fechamento",
    ]

    if operational_alert and any(t in low for t in missing_trigger_terms):
        if "entrada atrasada: não" in low or "entrada atrasada: nao" in low or "entrada atrasada: n/a" in low:
            return True

        # If no explicit late-entry field exists, still watch fresh zone alerts
        # that are waiting for a trigger.
        if "entrada atrasada" not in low and "not_promoted" in low:
            return True

    return False


# --- V3 Watch Manager caps (MODULE_AWARE_GLOBAL_RULES_V3.watch_manager_caps) ---
MAX_ACTIVE_WATCHES = 6
PRIORITY_ORDER = {"a": 0, "b": 1, "c": 2}  # lower index = higher priority


def _priority_key(priority_str: str) -> int:
    """Map 'A'/'B'/'C' to 0/1/2. Unknown → 3 (lowest)."""
    if not priority_str:
        return 3
    k = priority_str.strip().lower()
    # Handle prefixes like "a — priority a" or "priority: a"
    for candidate in (k, k[-1:]):
        if candidate in PRIORITY_ORDER:
            return PRIORITY_ORDER[candidate]
    return 3


def _module_backtest_n(stdout: str) -> int:
    """Extract module_backtest_n from stdout. Returns 0 if absent/invalid."""
    raw = line_value(stdout, "Module backtest n:")
    if not raw:
        return 0
    try:
        return int("".join(ch for ch in raw if ch.isdigit()) or "0")
    except Exception:
        return 0


def _active_watches(state):
    return [w for w in state["watches"].values() if w.get("status") == "ACTIVE_WATCH"]


def _watch_rank(watch):
    """
    Lower rank = higher priority (better candidate to KEEP).
    Tiebreakers per strategy_rules.json module_aware_policy:
      1. Priority A > B > C.
      2. Higher module_backtest_n wins.
      3. FIFO (older created_at wins) as final tiebreak.
    """
    pri = _priority_key(watch.get("priority") or "")
    n = -int(watch.get("module_backtest_n") or 0)  # negative so higher n sorts first
    created = watch.get("created_at") or ""
    return (pri, n, created)


def evict_lowest_priority_watch(state, candidate_rank) -> tuple[bool, str]:
    """
    If we are at cap, try to evict the lowest-priority ACTIVE watch
    if it is strictly LOWER priority than candidate_rank.

    Returns (evicted, evicted_watch_id).
    """
    actives = _active_watches(state)
    if len(actives) < MAX_ACTIVE_WATCHES:
        return False, ""  # No eviction needed

    # Sort actives by rank ASCENDING (best first); the LAST one is the worst.
    sorted_actives = sorted(actives, key=_watch_rank)
    worst = sorted_actives[-1]
    worst_rank = _watch_rank(worst)

    if candidate_rank < worst_rank:
        # New candidate is strictly better → evict the worst.
        worst_id = worst.get("watch_id")
        worst["status"] = "EVICTED_BY_PRIORITY"
        worst["evicted_at"] = now_utc().isoformat()
        append_jsonl(WATCH_LOG, {
            "event": "watch_evicted_for_priority",
            "evicted_at": worst["evicted_at"],
            "evicted_watch_id": worst_id,
            "evicted_rank": list(worst_rank),
            "incoming_rank": list(candidate_rank),
            "policy": "MODULE_AWARE_GLOBAL_RULES_V3.watch_manager_caps"
        })
        return True, worst_id

    return False, ""


def floor_to_interval(dt, minutes):
    minute = (dt.minute // minutes) * minutes
    return dt.replace(minute=minute, second=0, microsecond=0)


def next_bar_closes(base_dt, tf_minutes, count, delay_seconds=20):
    start = floor_to_interval(base_dt, tf_minutes)
    if start <= base_dt:
        start += timedelta(minutes=tf_minutes)

    out = []
    t = start
    for _ in range(count):
        out.append(t + timedelta(seconds=delay_seconds))
        t += timedelta(minutes=tf_minutes)
    return out


def build_due_schedule(row):
    received_at = parse_ts(row.get("received_at")) or now_utc()
    tf = str(row.get("timeframe") or "").lower().strip()

    due = []

    # Intraday execution should always be checked on 15M closes first.
    if tf in ["15", "15m", "30", "30m", "60", "1h", "h1"]:
        for dt in next_bar_closes(received_at, 15, 4):
            due.append({
                "kind": "15m_close",
                "due_at": dt.isoformat(),
                "execution_tf": "15"
            })

        # Also check 30M closes for structure confirmation.
        for dt in next_bar_closes(received_at, 30, 3):
            due.append({
                "kind": "30m_close",
                "due_at": dt.isoformat(),
                "execution_tf": "30"
            })

    elif tf in ["240", "4h", "h4"]:
        for dt in next_bar_closes(received_at, 60, 4):
            due.append({
                "kind": "1h_close",
                "due_at": dt.isoformat(),
                "execution_tf": "60"
            })
        for dt in next_bar_closes(received_at, 240, 2):
            due.append({
                "kind": "4h_close",
                "due_at": dt.isoformat(),
                "execution_tf": "240"
            })
    else:
        for dt in next_bar_closes(received_at, 15, 3):
            due.append({
                "kind": "15m_close",
                "due_at": dt.isoformat(),
                "execution_tf": "15"
            })

    # Sort and remove duplicates by due_at/kind.
    seen = set()
    clean = []
    for item in sorted(due, key=lambda x: x["due_at"]):
        key = (item["kind"], item["due_at"])
        if key in seen:
            continue
        seen.add(key)
        clean.append(item)

    return clean


def add_new_watches(state, rows, hours, create_grace_minutes):
    cutoff = now_utc() - timedelta(hours=hours)
    created = 0

    for row in rows:
        received_at = parse_ts(row.get("received_at"))
        if not received_at or received_at < cutoff:
            continue

        if not is_fresh(row, create_grace_minutes):
            continue

        if not is_watch_candidate(row):
            continue

        event_id = row.get("event_id")
        if not event_id:
            continue

        if event_id in state["watches"]:
            continue

        stdout = row.get("claude_stdout") or ""

        priority_val = line_value(stdout, "Priority:")
        module_n = _module_backtest_n(stdout)

        watch = {
            "watch_id": event_id,
            "created_at": now_utc().isoformat(),
            "source_event_id": event_id,
            "received_at": row.get("received_at"),
            "symbol": row.get("symbol"),
            "base_symbol": row.get("base_symbol"),
            "timeframe": row.get("timeframe"),
            "alert_type": row.get("alert_type"),
            "drawing_name": row.get("drawing_name"),
            "classification": row.get("classification"),
            "direction": row.get("direction"),
            "strategy_module": line_value(stdout, "Strategy Module:"),
            "module_backtest_n": module_n,
            "priority": priority_val,
            "execution_tf": line_value(stdout, "Execution TF:"),
            "promotion_trigger": line_value(stdout, "Promotion trigger:"),
            "promotion_status": line_value(stdout, "Promotion status:"),
            "entry_ideal": line_value(stdout, "Entrada ideal:"),
            "current_price": line_value(stdout, "Preço atual:"),
            "late_entry": line_value(stdout, "Entrada atrasada:"),
            "missing_trigger": line_value(stdout, "Gatilho faltante:"),
            "due_rechecks": build_due_schedule(row),
            "fired_rechecks": [],
            "status": "ACTIVE_WATCH",
        }

        # V3 cap enforcement: max 6 ACTIVE_WATCH; evict lowest priority if needed.
        candidate_rank = _watch_rank(watch)
        actives_count = len(_active_watches(state))

        if actives_count >= MAX_ACTIVE_WATCHES:
            evicted, evicted_id = evict_lowest_priority_watch(state, candidate_rank)
            if not evicted:
                # Candidate is not strictly better than the worst active watch — reject.
                append_jsonl(WATCH_LOG, {
                    "event": "watch_rejected_at_cap",
                    "rejected_at": now_utc().isoformat(),
                    "rejected_event_id": event_id,
                    "rejected_rank": list(candidate_rank),
                    "actives_count": actives_count,
                    "cap": MAX_ACTIVE_WATCHES,
                    "policy": "MODULE_AWARE_GLOBAL_RULES_V3.watch_manager_caps"
                })
                continue

        state["watches"][event_id] = watch
        created += 1

        append_jsonl(WATCH_LOG, {
            "event": "watch_created",
            "created_at": now_utc().isoformat(),
            "watch": watch,
        })

    return created


def post_recheck(watch, due_item):
    payload = {
        "symbol": watch.get("symbol"),
        "base_symbol": watch.get("base_symbol") or (watch.get("symbol") or "").split(":")[-1],
        "timeframe": watch.get("timeframe"),
        "alert_type": "setup_watch_recheck",
        "event": f"setup_watch_recheck_{due_item.get('kind')}",
        "drawing_name": watch.get("drawing_name") or "",
        "strategy_layer": "ActiveSetupWatch",
        "source_timeframe": watch.get("timeframe"),
        "execution_timeframe": due_item.get("execution_tf"),
        "original_event_id": watch.get("source_event_id"),
        "watch_id": watch.get("watch_id"),
        "watch_recheck_kind": due_item.get("kind"),
        "is_active_watch_recheck": True,
        "reason": (
            "ACTIVE WATCH BAR-CLOSE RECHECK: reavaliar setup/candidato no fechamento do candle. "
            "Objetivo é capturar o gatilho no timing correto, não depois do movimento."
        ),
        "expected_recheck": (
            "Reavaliar se o candle fechado confirmou gatilho objetivo. "
            "Verificar REJECTION_CLOSE, SWEEP_REENTRY, CHOCH/BOS, RETEST_HOLD, NAS signal at zone, bubbles, RSI, stop e R:R. "
            "Se o gatilho apareceu e a entrada ainda não está atrasada, classificar como SETUP_VALIDO/SETUP_VALIDO_INTRADAY. "
            "Se o preço já se afastou >0.7R da entrada ideal, marcar LATE/nao perseguir. "
            "Se invalidou, marcar INVALIDATED. "
            "Não desenhar, não criar alerta, não executar trade."
        )
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        LOCAL_WEBHOOK,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            ok = 200 <= resp.status < 300
            return ok, body
    except urllib.error.URLError as e:
        return False, str(e)


def fire_due_rechecks(state, max_recheck_lag_minutes):
    fired = 0
    n = now_utc()

    for watch_id, watch in list(state["watches"].items()):
        if watch.get("status") != "ACTIVE_WATCH":
            continue

        fired_ids = set(watch.get("fired_rechecks") or [])

        for item in watch.get("due_rechecks") or []:
            recheck_id = f"{item.get('kind')}|{item.get('due_at')}"
            if recheck_id in fired_ids:
                continue

            due_at = parse_ts(item.get("due_at"))
            if not due_at or n < due_at:
                continue

            if n - due_at > timedelta(minutes=max_recheck_lag_minutes):
                watch.setdefault("fired_rechecks", []).append(recheck_id)
                append_jsonl(WATCH_LOG, {
                    "event": "watch_recheck_skipped_stale",
                    "skipped_at": n.isoformat(),
                    "watch_id": watch_id,
                    "recheck_id": recheck_id,
                    "due_at": item.get("due_at"),
                    "reason": "bar_close_due_time_too_old"
                })
                continue

            ok, body = post_recheck(watch, item)

            append_jsonl(WATCH_LOG, {
                "event": "watch_recheck_fired",
                "fired_at": n.isoformat(),
                "watch_id": watch_id,
                "recheck_id": recheck_id,
                "kind": item.get("kind"),
                "execution_tf": item.get("execution_tf"),
                "due_at": item.get("due_at"),
                "ok": ok,
                "response": body[:1000],
            })

            if ok:
                watch.setdefault("fired_rechecks", []).append(recheck_id)
                fired += 1

            # Avoid bursts: fire only one due recheck per watch per cycle.
            break

        all_ids = {f"{i.get('kind')}|{i.get('due_at')}" for i in (watch.get("due_rechecks") or [])}
        fired_ids = set(watch.get("fired_rechecks") or [])
        if all_ids and fired_ids >= all_ids:
            watch["status"] = "COMPLETED"
            watch["completed_at"] = n.isoformat()

    return fired


def prune_old_watches(state, max_age_hours):
    cutoff = now_utc() - timedelta(hours=max_age_hours)
    removed = 0

    for watch_id, watch in list(state["watches"].items()):
        created_at = parse_ts(watch.get("created_at"))
        if created_at and created_at < cutoff:
            del state["watches"][watch_id]
            removed += 1

    return removed


def print_status(state):
    active = [w for w in state["watches"].values() if w.get("status") == "ACTIVE_WATCH"]
    completed = [w for w in state["watches"].values() if w.get("status") == "COMPLETED"]

    print("=== Setup Watch Manager v2 Status ===")
    print("State:", WATCH_STATE)
    print("Watch log:", WATCH_LOG)
    print("Active watches:", len(active))
    print("Completed watches:", len(completed))

    for w in active[-10:]:
        print("----")
        print("watch_id:", w.get("watch_id"))
        print("symbol:", w.get("symbol"))
        print("tf:", w.get("timeframe"))
        print("classification:", w.get("classification"))
        print("module:", w.get("strategy_module"))
        print("priority:", w.get("priority"))
        print("entry:", w.get("entry_ideal"))
        print("late:", w.get("late_entry"))
        print("missing:", w.get("missing_trigger"))
        due = w.get("due_rechecks") or []
        fired = set(w.get("fired_rechecks") or [])
        pending = [d for d in due if f"{d.get('kind')}|{d.get('due_at')}" not in fired]
        print("pending_rechecks:", pending[:5])


def cycle(args):
    rows = load_jsonl(RESEARCH_LOG)
    state = load_state()

    created = add_new_watches(state, rows, args.hours, args.create_grace_minutes)
    fired = 0 if args.scan_only else fire_due_rechecks(state, args.max_recheck_lag_minutes)
    removed = prune_old_watches(state, args.max_age_hours)

    save_state(state)

    print_status(state)
    print("")
    print("Created watches:", created)
    print("Fired rechecks:", fired)
    print("Pruned old watches:", removed)


def main():
    parser = argparse.ArgumentParser(description="Active setup watch manager v2")
    parser.add_argument("--hours", type=int, default=12)
    parser.add_argument("--max-age-hours", type=int, default=24)
    parser.add_argument("--create-grace-minutes", type=int, default=10)
    parser.add_argument("--max-recheck-lag-minutes", type=int, default=10)
    parser.add_argument("--scan-only", action="store_true")
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--daemon", action="store_true")
    parser.add_argument("--sleep", type=int, default=30)
    args = parser.parse_args()

    if args.daemon:
        while True:
            try:
                cycle(args)
            except Exception as e:
                append_jsonl(WATCH_LOG, {
                    "event": "watch_manager_error",
                    "time": now_utc().isoformat(),
                    "error": str(e),
                })
                print("ERROR:", e)
            time.sleep(args.sleep)
    else:
        cycle(args)


if __name__ == "__main__":
    main()
