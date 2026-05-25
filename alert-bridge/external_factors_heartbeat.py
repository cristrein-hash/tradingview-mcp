#!/usr/bin/env python3
"""External Factors Heartbeat — monitora bridge iMac e alerta no Telegram quando
o feed v1.2 estiver stale/failing ou voltar ao normal.

Modo passivo: NÃO altera classificação de setups, NÃO interfere no receiver,
NÃO transforma External Factors em filtro ativo. Apenas monitoramento.

Uso:
    python3 external_factors_heartbeat.py --once         # 1 check de teste
    python3 external_factors_heartbeat.py --daemon --sleep 900  # loop 15min

Comportamento:
- Ring buffer dos últimos 8 checks (~2h).
- Alert se >=5/8 fails OU latest.json timestamp >2h stale.
- Recovery alert após 3 OK consecutivos pós-failing.
- Evita spam: estado transition-based.
- State persistente em logs/external_factors_heartbeat_state.json.
- Log append em logs/external_factors_heartbeat.log.
"""
import argparse
import os
import json
import sys
import time
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

def repo_root():
    """Resolve the tradingview-mcp repo root robustly (survives file moves)."""
    import os as _os
    from pathlib import Path as _Path
    env = _os.environ.get("TVMCP_ROOT")
    if env and _Path(env).expanduser().is_dir():
        return _Path(env).expanduser().resolve()
    cur = _Path(__file__).resolve().parent
    for d in (cur, *cur.parents):
        if (d / ".git").exists() or (d / "src" / "server.js").exists() \
           or ((d / "alert-bridge").is_dir() and (d / "my-strategy").is_dir()):
            return d
    raise RuntimeError(f"TVMCP repo root not found from {__file__}; set TVMCP_ROOT or run inside the repo")


BASE_DIR = repo_root() / "alert-bridge"   # was: Path(__file__).parent (same dir, now move-safe)
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

ENV_FILE = BASE_DIR / ".env"
STATE_FILE = LOGS_DIR / "external_factors_heartbeat_state.json"
LOG_FILE = LOGS_DIR / "external_factors_heartbeat.log"

EXTERNAL_URL = os.environ.get("EXTERNAL_URL", "http://192.168.1.90:8765/latest.json")
FETCH_TIMEOUT_S = 5
RING_BUFFER_SIZE = 8
FAIL_THRESHOLD = 5            # >=5/8 fails → alert
STALE_THRESHOLD_MIN = 120     # >2h stale → treated as fail-equivalent
RECOVERY_CONSECUTIVE_OK = 3   # 3 OK consecutive → recovery alert
DEFAULT_SLEEP_S = 900         # 15min


# ---------------------------------------------------------------------------
# Env / Telegram
# ---------------------------------------------------------------------------

def load_env():
    env = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def send_telegram(text: str):
    env = load_env()
    token = env.get("TELEGRAM_BOT_TOKEN")
    chat_ids_raw = env.get("TELEGRAM_CHAT_IDS") or env.get("TELEGRAM_CHAT_ID")
    if not token or not chat_ids_raw:
        return {"ok": False, "error": "telegram_env_missing"}
    chat_ids = [x.strip() for x in chat_ids_raw.split(",") if x.strip()]
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    results = []
    for chat_id in chat_ids:
        data = urlencode({
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": "true",
        }).encode("utf-8")
        req = Request(url, data=data, method="POST")
        try:
            with urlopen(req, timeout=10) as resp:
                results.append(json.loads(resp.read().decode("utf-8")))
        except Exception as e:
            results.append({"ok": False, "error": str(e), "chat_id": chat_id})
    return {"ok": all(r.get("ok") for r in results), "results": results}


# ---------------------------------------------------------------------------
# Fetch + classify
# ---------------------------------------------------------------------------

def fetch_external():
    """Returns (ok: bool, age_minutes: float|None, payload_ts: str|None, error: str|None)."""
    try:
        req = Request(EXTERNAL_URL)
        with urlopen(req, timeout=FETCH_TIMEOUT_S) as resp:
            raw = resp.read().decode("utf-8")
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as e:
            return False, None, None, f"json_decode:{e}"
        # Extract timestamp — try common fields
        ts_str = (
            payload.get("timestamp_utc")
            or payload.get("timestamp")
            or payload.get("generated_at")
            or payload.get("created_at")
            or payload.get("ts")
        )
        if not ts_str:
            return False, None, None, "no_timestamp_field_in_payload"
        try:
            dt = datetime.fromisoformat(str(ts_str).replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
        except Exception as e:
            return False, None, str(ts_str), f"timestamp_parse:{e}"
        now = datetime.now(timezone.utc)
        age_min = (now - dt).total_seconds() / 60.0
        return True, age_min, str(ts_str), None
    except URLError as e:
        return False, None, None, f"url_error:{e.reason if hasattr(e,'reason') else e}"
    except Exception as e:
        return False, None, None, f"unexpected:{type(e).__name__}:{e}"


def classify_check(ok: bool, age_min):
    """Return 'ok' if fetch ok AND age <= STALE_THRESHOLD_MIN; else 'fail'."""
    if not ok:
        return "fail"
    if age_min is None:
        return "fail"
    if age_min > STALE_THRESHOLD_MIN:
        return "fail"
    return "ok"


# ---------------------------------------------------------------------------
# State persistence
# ---------------------------------------------------------------------------

def load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {
        "ring_buffer": [],
        "alert_state": "ok",          # 'ok' | 'failing'
        "last_failing_since_ts": None,
        "consecutive_ok": 0,
    }


def save_state(state):
    tmp = STATE_FILE.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(state, indent=2, default=str))
    tmp.replace(STATE_FILE)


def append_log(line: str):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    with LOG_FILE.open("a") as f:
        f.write(f"[{ts}Z] {line}\n")


# ---------------------------------------------------------------------------
# Main check logic
# ---------------------------------------------------------------------------

def run_one_check(state, send_alerts=True):
    """Execute single check, update state, optionally send Telegram. Return summary dict."""
    ok_fetch, age_min, payload_ts, error = fetch_external()
    status = classify_check(ok_fetch, age_min)
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    check_entry = {
        "ts": now_iso,
        "status": status,
        "fetch_ok": ok_fetch,
        "age_minutes": round(age_min, 1) if age_min is not None else None,
        "payload_ts": payload_ts,
        "error": error,
    }

    # Update ring buffer
    rb = state.get("ring_buffer", [])
    rb.append(check_entry)
    if len(rb) > RING_BUFFER_SIZE:
        rb = rb[-RING_BUFFER_SIZE:]
    state["ring_buffer"] = rb

    fails_in_buffer = sum(1 for e in rb if e["status"] == "fail")
    is_failing_now = fails_in_buffer >= FAIL_THRESHOLD

    # Track consecutive OK for recovery detection
    if status == "ok":
        state["consecutive_ok"] = state.get("consecutive_ok", 0) + 1
    else:
        state["consecutive_ok"] = 0

    prev_state = state.get("alert_state", "ok")
    transition = None
    alert_sent = None

    # Transition ok → failing
    if prev_state == "ok" and is_failing_now:
        state["alert_state"] = "failing"
        state["last_failing_since_ts"] = now_iso
        transition = "ok→failing"
        if send_alerts:
            since_hhmm = now_iso[11:16]
            msg = (
                "⚠️ <b>External Factors stale/failing</b> — technical signals "
                "still work, but macro validation degraded.\n\n"
                f"iMac bridge unreachable/stale since {since_hhmm} UTC.\n"
                f"Last 8 checks: {fails_in_buffer}/{RING_BUFFER_SIZE} fails.\n"
                f"Last error: <code>{error or 'stale (>2h)'}</code>"
            )
            tg = send_telegram(msg)
            alert_sent = "alert_sent" if tg.get("ok") else f"telegram_fail:{tg}"

    # Transition failing → ok (after RECOVERY_CONSECUTIVE_OK consecutive OK)
    elif prev_state == "failing" and state["consecutive_ok"] >= RECOVERY_CONSECUTIVE_OK:
        state["alert_state"] = "ok"
        state["last_failing_since_ts"] = None
        transition = "failing→ok"
        if send_alerts:
            msg = "✅ <b>External Factors recovered</b> — macro validation feed is healthy again."
            tg = send_telegram(msg)
            alert_sent = "recovery_sent" if tg.get("ok") else f"telegram_fail:{tg}"

    return {
        "check": check_entry,
        "fails_in_buffer": fails_in_buffer,
        "buffer_size": len(rb),
        "alert_state": state["alert_state"],
        "consecutive_ok": state["consecutive_ok"],
        "transition": transition,
        "alert_sent": alert_sent,
    }


# ---------------------------------------------------------------------------
# Entrypoints
# ---------------------------------------------------------------------------

def run_once(send_alerts=True):
    state = load_state()
    summary = run_one_check(state, send_alerts=send_alerts)
    save_state(state)
    append_log(json.dumps(summary, default=str))
    return summary


def run_daemon(sleep_s):
    append_log(f"daemon_start sleep_s={sleep_s}")
    print(f"[external_factors_heartbeat] daemon started, sleep={sleep_s}s", flush=True)
    try:
        while True:
            try:
                summary = run_once(send_alerts=True)
                print(
                    f"[{summary['check']['ts']}] status={summary['check']['status']} "
                    f"fails={summary['fails_in_buffer']}/{summary['buffer_size']} "
                    f"alert_state={summary['alert_state']} "
                    f"transition={summary['transition']} alert={summary['alert_sent']}",
                    flush=True,
                )
            except Exception as e:
                append_log(f"check_exception:{type(e).__name__}:{e}")
                print(f"[external_factors_heartbeat] check_exception: {e}", flush=True)
            time.sleep(sleep_s)
    except KeyboardInterrupt:
        append_log("daemon_stop_keyboard_interrupt")
        print("\n[external_factors_heartbeat] daemon stopped", flush=True)


def main():
    parser = argparse.ArgumentParser(description="External Factors v1.2 bridge heartbeat monitor")
    g = parser.add_mutually_exclusive_group(required=True)
    g.add_argument("--once", action="store_true", help="Run single check and exit")
    g.add_argument("--daemon", action="store_true", help="Run in loop (sleep between checks)")
    parser.add_argument("--sleep", type=int, default=DEFAULT_SLEEP_S,
                        help=f"Sleep seconds between checks in daemon mode (default {DEFAULT_SLEEP_S})")
    parser.add_argument("--no-telegram", action="store_true",
                        help="Skip Telegram (only log) — useful for test runs")
    args = parser.parse_args()

    if args.once:
        summary = run_once(send_alerts=not args.no_telegram)
        print(json.dumps(summary, indent=2, default=str))
        return 0 if summary["check"]["status"] == "ok" else 1
    if args.daemon:
        run_daemon(args.sleep)
        return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
