#!/usr/bin/env python3
"""
One-shot backfill: strip 'PEPPERSTONE:' prefix dos records dirty no indicator_signals.jsonl.

Cria backup .bak.YYYYMMDD antes. Não altera signal_hash (preservar dedup histórico).
Normaliza: base_symbol, symbol, payload_full.base_symbol, payload_full.symbol, payload_full.reason.
"""
from __future__ import annotations
import json
import shutil
import sys
from pathlib import Path
from datetime import datetime

PREFIX = "PEPPERSTONE:"
LOG_PATH = Path.home() / "tradingview-mcp" / "alert-bridge" / "logs" / "indicator_signals.jsonl"


def strip_prefix(s):
    if isinstance(s, str) and s.startswith(PREFIX):
        return s[len(PREFIX):]
    return s


def normalize(record: dict) -> tuple[dict, bool]:
    """Return (normalized_record, was_dirty)."""
    dirty = False
    if isinstance(record.get("base_symbol"), str) and record["base_symbol"].startswith(PREFIX):
        record["base_symbol"] = strip_prefix(record["base_symbol"])
        dirty = True
    if isinstance(record.get("symbol"), str) and record["symbol"].startswith(PREFIX):
        record["symbol"] = strip_prefix(record["symbol"])
        dirty = True
    pf = record.get("payload_full")
    if isinstance(pf, dict):
        if isinstance(pf.get("base_symbol"), str) and pf["base_symbol"].startswith(PREFIX):
            pf["base_symbol"] = strip_prefix(pf["base_symbol"])
            dirty = True
        if isinstance(pf.get("symbol"), str) and pf["symbol"].startswith(PREFIX):
            pf["symbol"] = strip_prefix(pf["symbol"])
            dirty = True
        reason = pf.get("reason")
        if isinstance(reason, str) and PREFIX in reason:
            pf["reason"] = reason.replace(PREFIX, "")
            dirty = True
    return record, dirty


def main(dry_run: bool = False) -> int:
    if not LOG_PATH.exists():
        print(f"ERRO: {LOG_PATH} não existe", file=sys.stderr)
        return 1

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    bak_path = LOG_PATH.with_suffix(f".jsonl.bak.{stamp}")

    if not dry_run:
        shutil.copy2(LOG_PATH, bak_path)
        print(f"[backup] {bak_path}")

    total = 0
    cleaned = 0
    errors = 0
    out_lines = []

    with LOG_PATH.open() as f:
        for line_no, raw in enumerate(f, 1):
            raw = raw.rstrip("\n")
            if not raw.strip():
                out_lines.append(raw)
                continue
            total += 1
            try:
                rec = json.loads(raw)
            except json.JSONDecodeError as e:
                print(f"[skip] linha {line_no} JSON inválido: {e}", file=sys.stderr)
                errors += 1
                out_lines.append(raw)
                continue
            rec, was_dirty = normalize(rec)
            if was_dirty:
                cleaned += 1
            out_lines.append(json.dumps(rec, ensure_ascii=False))

    print(f"[stats] total={total} cleaned={cleaned} errors={errors}")

    if dry_run:
        print("[dry-run] nada gravado")
        return 0

    tmp_path = LOG_PATH.with_suffix(".jsonl.tmp")
    tmp_path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")

    with tmp_path.open() as f:
        for line_no, raw in enumerate(f, 1):
            if raw.strip():
                json.loads(raw)
    print(f"[validate] {tmp_path} parse OK")

    tmp_path.replace(LOG_PATH)
    print(f"[done] gravado em {LOG_PATH}")
    return 0


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    sys.exit(main(dry_run=dry))
