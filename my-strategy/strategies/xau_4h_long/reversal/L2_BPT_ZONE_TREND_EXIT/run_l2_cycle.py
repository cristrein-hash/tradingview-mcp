#!/usr/bin/env python3
"""Runner do ciclo L2/BPT XAU 4H — TAB-PINNED ONLY (sem chart-op, sem lock, sem pausa).

Ciclo:
  1. tab_pin.discover_tab("240")  -> tab 4H dedicada; AUSENTE = HARD_STOP fail-closed
     `blocked_missing_tab_240` (decisão de simplicidade L2: SEM fallback manage-chart — o L1
     é que tem fallback; aqui a tab dedicada é requisito).
  2. runtime_l2.py --once com TVMCP_TARGET_CHART_ID pinado (env do subprocess).

Default = DRY-RUN (sem Telegram). Envio real só com --send-telegram E env
L2_PRODUCTION_AUTHORIZED=1 (hard-lock no runtime/notifier — nasce travado).
Log próprio .runtime_state/l2_cycle.log com rotação (padrão L1). py3.9 stdlib.
"""
import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = None
for d in [HERE] + list(HERE.parents):
    if (d / "my-strategy").is_dir() and (d / "alert-bridge").is_dir():
        REPO = d
        break
RUNTIME = HERE / "runtime_l2.py"
STATE_DIR = HERE / ".runtime_state"
DEDUP = STATE_DIR / "l2_dedup.txt"
LOG = STATE_DIR / "l2_cycle.log"
LOG_MAX_BYTES = 2_000_000
LOG_BACKUPS = 3


def _rotate_log():
    """Rotação mínima: l2_cycle.log -> .1 -> .2 -> .3 (best-effort, nunca derruba o ciclo)."""
    try:
        if LOG.exists() and LOG.stat().st_size > LOG_MAX_BYTES:
            oldest = LOG.with_suffix(LOG.suffix + f".{LOG_BACKUPS}")
            if oldest.exists():
                oldest.unlink()
            for i in range(LOG_BACKUPS - 1, 0, -1):
                src = LOG.with_suffix(LOG.suffix + f".{i}")
                if src.exists():
                    src.rename(LOG.with_suffix(LOG.suffix + f".{i + 1}"))
            LOG.rename(LOG.with_suffix(LOG.suffix + ".1"))
    except Exception:
        pass


def _log(ts, out):
    STATE_DIR.mkdir(exist_ok=True)
    _rotate_log()
    with open(LOG, "a") as f:
        f.write(json.dumps({"ts": ts, **out}, ensure_ascii=False) + "\n")


def cycle(send_telegram=False):
    ts = datetime.now(timezone.utc).isoformat()
    # ---- 1) pin da tab 4H (fail-closed, SEM fallback) ----
    try:
        sys.path.insert(0, str(REPO / "my-strategy/core"))
        import tab_pin
        tid = tab_pin.discover_tab("240")
    except Exception as e:
        tid = None
        pin_err = f"{type(e).__name__}: {e}"
    else:
        pin_err = None
    if not tid:
        out = {"status": "HARD_STOP", "stage": "tab_pin",
               "state": "blocked_missing_tab_240",
               "reason": pin_err or "tab XAUUSD 240 não encontrada — abre/verifica a tab 4H dedicada"}
        _log(ts, out)
        return {"ts": ts, **out}

    # ---- 2) runtime na tab pinada ----
    env = tab_pin.env_pinned(tid)
    argv = [sys.executable, str(RUNTIME), "--once", "--dedup-path", str(DEDUP)]
    if send_telegram:
        argv.append("--send-telegram")
    r = subprocess.run(argv, capture_output=True, text=True, env=env)
    try:
        rj = json.loads(r.stdout)
    except Exception:
        out = {"status": "HARD_STOP", "stage": "runtime",
               "reason": (r.stdout.strip() or r.stderr.strip())[-500:]}
        _log(ts, out)
        return {"ts": ts, **out}
    if rj.get("runtime") != "OK":
        out = {"status": "BLOCKED" if rj.get("runtime") == "BLOCKED" else "HARD_STOP",
               "stage": "runtime", "state": rj.get("state"), "reason": rj.get("reason"),
               "tab_240": tid[:8]}
        _log(ts, out)
        return {"ts": ts, **out}
    out = {"status": "OK", "tab_240": tid[:8], "chart_mode": "pinned",
           "panel": rj.get("panel"), "guard": rj.get("guard"),
           "new_bars": rj.get("new_bars"), "alerts_n": rj.get("alerts_n"),
           "alerts": rj.get("alerts"), "open_positions": rj.get("open_positions"),
           "bar_results": rj.get("bar_results"),
           "initialized_first_cycle": rj.get("initialized_first_cycle"),
           "telegram_real": bool(send_telegram),
           "production_authorized": rj.get("production_authorized")}
    _log(ts, out)
    return {"ts": ts, **out}


def main():
    ap = argparse.ArgumentParser(description="Minimal XAU L2 cycle runner (tab-pinned only).")
    ap.add_argument("--once", action="store_true", help="roda 1 ciclo (default já é 1 ciclo)")
    ap.add_argument("--send-telegram", action="store_true",
                    help="envio real (opt-in; hard-lock L2_PRODUCTION_AUTHORIZED continua a mandar)")
    args = ap.parse_args()
    res = cycle(send_telegram=args.send_telegram)
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 2 if res.get("status") in ("HARD_STOP", "BLOCKED") else 0


if __name__ == "__main__":
    sys.exit(main())
