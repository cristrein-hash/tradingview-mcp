#!/usr/bin/env python3
"""Caminho A — D2R re-evaluation cirúrgica pós-migration parser v2.

Objetivo: processar até 60 records elegíveis (CANDIDATO_FORTE + OBSERVACAO)
que foram pulados pelo D2R pré-migration. Foco em 12-13 mai (records com
2-3 dias de forward data já disponível).

Limites:
- 20 batches × 3 events = 60 records máximo
- 80 minutos wall-time
- Pulará records já processados (lógica do select_events)
"""
import json
import subprocess
import sys
import os
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent  # tradingview-mcp/
EVAL_SCRIPT = BASE_DIR / "alert-bridge" / "evaluate_r_outcomes.py"
R_OUTCOME_LOG = BASE_DIR / "alert-bridge" / "logs" / "setup_r_outcome_log.jsonl"
LOG_FILE = BASE_DIR / "alert-bridge" / "logs" / "d2r_caminho_a.log"

MAX_BATCHES = 20
MAX_WALL_TIME_SECONDS = 4800  # 80 min
BATCH_LIMIT = 3
BATCH_TIMEOUT = 900  # 15min per batch
SINCE = "2026-05-04"  # cover all that the migration might have unblocked
CLASSIFICATIONS = (
    "SETUP_CANDIDATO_FORTE,"
    "SETUP_CANDIDATO_FORTE_INTRADAY,"
    "SETUP_EM_OBSERVACAO,"
    "SETUP_EM_OBSERVACAO_INTRADAY,"
    "INTRADAY_EM_OBSERVACAO"
)


def count_outcomes():
    if not R_OUTCOME_LOG.exists():
        return 0
    with R_OUTCOME_LOG.open() as f:
        return sum(1 for _ in f)


def append_log(line):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with LOG_FILE.open("a") as f:
        f.write(f"[{ts}] {line}\n")


def main():
    start_ts = datetime.now(timezone.utc)
    n_start = count_outcomes()
    append_log(f"START — caminho A. n_outcomes_before={n_start}")
    print(f"[caminho_a] start — current D2R outcomes: {n_start}")

    for batch_n in range(1, MAX_BATCHES + 1):
        elapsed = (datetime.now(timezone.utc) - start_ts).total_seconds()
        if elapsed > MAX_WALL_TIME_SECONDS:
            append_log(f"WALL_TIME_REACHED at batch {batch_n}")
            print(f"[caminho_a] wall time reached")
            break

        ts_batch = datetime.now(timezone.utc).strftime("%H:%M:%S")
        append_log(f"BATCH {batch_n}/{MAX_BATCHES} starting")
        print(f"[caminho_a] [{ts_batch}] batch {batch_n}/{MAX_BATCHES} starting...")

        cmd = [
            "python3", str(EVAL_SCRIPT),
            "--limit", str(BATCH_LIMIT),
            "--since", SINCE,
            "--classifications", CLASSIFICATIONS,
            "--timeout", str(BATCH_TIMEOUT),
        ]
        try:
            result = subprocess.run(
                cmd,
                cwd=str(BASE_DIR),
                capture_output=True,
                text=True,
                timeout=BATCH_TIMEOUT + 60,
            )
            n_after = count_outcomes()
            added = n_after - n_start - sum(0 for _ in range(batch_n - 1))
            n_now = count_outcomes()
            stdout_tail = (result.stdout or "")[-200:]
            append_log(
                f"BATCH {batch_n} exit={result.returncode} "
                f"new_outcomes_total={n_now} stdout_tail={stdout_tail!r}"
            )
            print(f"[caminho_a] batch {batch_n} exit={result.returncode} total_D2R={n_now}")
            # Detectar fim natural: stdout indica "Eventos avaliados D2R: 0" ou similar
            if "Eventos avaliados D2R: 0" in (result.stdout or ""):
                append_log("BATCH returned 0 events evaluated — natural stop")
                print(f"[caminho_a] no more eligible — stopping")
                break
        except subprocess.TimeoutExpired:
            append_log(f"BATCH {batch_n} TIMEOUT")
            print(f"[caminho_a] batch {batch_n} TIMEOUT")
            continue
        except Exception as e:
            append_log(f"BATCH {batch_n} EXCEPTION: {e}")
            print(f"[caminho_a] batch {batch_n} exception: {e}")
            continue

    n_end = count_outcomes()
    elapsed_min = (datetime.now(timezone.utc) - start_ts).total_seconds() / 60.0
    summary = (
        f"END — caminho A. n_outcomes_before={n_start}, n_outcomes_after={n_end}, "
        f"added={n_end - n_start}, elapsed_min={elapsed_min:.1f}"
    )
    append_log(summary)
    print(f"\n[caminho_a] {summary}")


if __name__ == "__main__":
    main()
