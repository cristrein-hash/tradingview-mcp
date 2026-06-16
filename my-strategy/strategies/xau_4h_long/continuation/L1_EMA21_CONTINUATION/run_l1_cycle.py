#!/usr/bin/env python3
"""Runner mínimo do ciclo XAU-only L1 (Production v2). Orquestra scripts EXISTENTES.

Ciclo:
  1) refresh_regime_l1_v4.py --write   (mantém regime D-1 fresco; already_fresh se nada novo)
  2) runtime_xau.py --once [--send-telegram] --dedup-path <persistente>

Default = DRY-RUN (sem Telegram). Telegram real só com --send-telegram, e só para
operational_candidate (o runtime decide). Dedup persistente garante ≤1 Telegram por signal_hash.
FALHA FECHADO: se o refresh ou o runtime der HARD_STOP, aborta sem Telegram.

NÃO reimplementa scanner/regime/telegram. NÃO toca legacy/broker/strategy_rules/catalog/RAW.
NÃO escreve em logs legacy (log próprio em .runtime_state/). DST-agnóstico (lê a barra live + dedup).
"""
import json, sys, subprocess, argparse
from pathlib import Path
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
REPO = None
for d in [HERE] + list(HERE.parents):
    if (d / "my-strategy").is_dir() and (d / "alert-bridge").is_dir():
        REPO = d; break
REFRESH = REPO / "my-strategy/core/regime_l1/refresh_regime_l1_v4.py"
RUNTIME = HERE / "runtime_xau.py"
STATE_DIR = HERE / ".runtime_state"
DEDUP = STATE_DIR / "l1_dedup.txt"
LOG = STATE_DIR / "l1_cycle.log"
LOG_MAX_BYTES = 2_000_000   # ~2 MB
LOG_BACKUPS = 3


def _rotate_log():
    """Rotação mínima sem dep externa: l1_cycle.log -> .1 -> .2 -> .3 (mantém 3 backups)."""
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
        pass  # rotação é best-effort; nunca derruba o ciclo


def _run(argv):
    return subprocess.run([sys.executable] + argv, capture_output=True, text=True)


def cycle(send_telegram=False):
    STATE_DIR.mkdir(exist_ok=True)
    ts = datetime.now(timezone.utc).isoformat()
    # 1) refresh do regime (fail-closed)
    r = _run([str(REFRESH), "--write"])
    try:
        rj = json.loads(r.stdout)
    except Exception:
        return {"status": "HARD_STOP", "stage": "refresh", "reason": r.stdout.strip() or r.stderr.strip()}
    if rj.get("status") == "HARD_STOP":
        return {"status": "HARD_STOP", "stage": "refresh", "reason": rj.get("reason")}
    refresh_status = rj.get("status")
    # 2) runtime (lê 240 + regime fresco)
    rt_argv = [str(RUNTIME), "--once", "--dedup-path", str(DEDUP)]
    if send_telegram:
        rt_argv.append("--send-telegram")
    rt = _run(rt_argv)
    try:
        rtj = json.loads(rt.stdout)
    except Exception:
        return {"status": "HARD_STOP", "stage": "runtime", "reason": rt.stdout.strip() or rt.stderr.strip()}
    if rtj.get("runtime") == "HARD_STOP":
        return {"status": "HARD_STOP", "stage": "runtime", "reason": rtj.get("reason")}
    cand = rtj.get("candidate", {})
    notify = rtj.get("notify", {})
    state = cand.get("state")
    # fail-closed extra: regime stale não deveria ocorrer (refresh roda antes)
    if isinstance(cand.get("reason"), str) and "regime_l1_v4_stale" in cand.get("reason"):
        out = {"status": "STALE", "stage": "runtime", "reason": cand.get("reason")}
    else:
        out = {"status": "OK", "refresh": refresh_status, "state": state,
               "telegram_real": bool(send_telegram), "notify_sent": notify.get("sent"),
               "notify_skip": notify.get("skip"), "signal_hash": cand.get("signal_hash")}
    # log próprio (não-legacy) com rotação mínima
    _rotate_log()
    with open(LOG, "a") as f:
        f.write(json.dumps({"ts": ts, **out}, ensure_ascii=False) + "\n")
    return {"ts": ts, **out}


def main():
    ap = argparse.ArgumentParser(description="Minimal XAU L1 cycle runner.")
    ap.add_argument("--once", action="store_true", help="roda 1 ciclo (default já é 1 ciclo)")
    ap.add_argument("--send-telegram", action="store_true", help="envio real (opt-in; default dry-run)")
    args = ap.parse_args()
    res = cycle(send_telegram=args.send_telegram)
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 2 if res.get("status") in ("HARD_STOP", "STALE") else 0


if __name__ == "__main__":
    sys.exit(main())
