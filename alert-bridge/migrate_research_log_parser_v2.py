#!/usr/bin/env python3
"""Migration: re-aplica parser v2 (robusto a markdown) em records antigos.

2026-05-15: fix do extract_stdout_field para aceitar **Field:**, etc.
Records anteriores ao restart pós-fix podem ter campos vazios quando Claude
emitiu markdown bold. Este script re-extrai e preenche APENAS campos vazios.

Uso:
    python3 migrate_research_log_parser_v2.py --dry-run     # report sem alterar
    python3 migrate_research_log_parser_v2.py --apply       # backup + reescreve

Comportamento:
- Backup automático em logs/setup_research_log.jsonl.bak_<timestamp>
- Para cada record, checa cada campo extraído via parser.
- Atualiza APENAS se valor antigo está vazio/None e novo é não-vazio.
- NUNCA sobrescreve dados existentes.
- Re-aplica conversões (_int_or_none, _float_or_none, _bool_or_none) onde aplicável.
"""
import argparse
import json
import re
import sys
import shutil
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).parent
LOG_DIR = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / "setup_research_log.jsonl"

# Replicate the new robust extractor inline (avoid coupling to live receiver)
def extract_field(stdout: str, label: str) -> str:
    if not stdout:
        return ""
    pattern = rf"^\s*[*]{{0,2}}\s*{re.escape(label)}\s*[*]{{0,2}}\s*:\s*[*]{{0,2}}\s*(.+?)\s*[*]{{0,2}}\s*$"
    for line in stdout.splitlines():
        m = re.match(pattern, line.strip(), flags=re.IGNORECASE)
        if m:
            return m.group(1).strip().strip("*").strip()
    return ""


def _bool_or_none(s):
    if s is None or s == "":
        return None
    sl = str(s).strip().lower()
    if sl in ("true", "yes", "sim"):
        return True
    if sl in ("false", "no", "nao", "não"):
        return False
    return None


def _int_or_none(s):
    if s is None or s == "":
        return None
    s = str(s).strip().replace('+', '')
    try:
        return int(s)
    except (ValueError, TypeError):
        return None


def _float_from_first_number(s):
    if s is None or s == "":
        return None
    if isinstance(s, (int, float)):
        return float(s)
    m = re.search(r'[-+]?\d+\.?\d*', str(s))
    if m:
        try:
            return float(m.group(0))
        except (ValueError, TypeError):
            return None
    return None


# Field map: (json_key, label_in_stdout, transform_fn or None)
FIELDS_STRING = [
    ("module_applied", "Strategy Module"),
    ("module_backtest_n", "Module backtest n"),
    ("global_hard_blocks", "Global hard blocks"),
    ("module_checklist", "Module checklist"),
    ("module_checklist_notes", "Module checklist notes"),
    ("module_score", "Module score"),
    ("operational_signal", "Operational signal"),
    ("hard_block_triggered", "Hard block triggered"),
    ("no_trade_reason", "NO_TRADE reason"),
    ("module_checklist_failed_on", "Module checklist failed on"),
    ("promotion_trigger_fired", "Promotion trigger"),
    ("promotion_status", "Promotion status"),
    ("priority_score", "Priority"),
    ("trigger", "Trigger"),
    ("execution_tf", "Execution TF"),
    ("ideal_entry_price_text", "Entrada ideal"),
    ("current_price_at_eval_text", "Preço atual"),
    ("entry_late", "Entrada atrasada"),
    # V3d shadow strings
    ("v3d_shadow_asset", "V3d shadow asset"),
    ("v3d_shadow_event_type", "V3d shadow event type"),
    ("v3d_shadow_ob_zone", "V3d shadow OB zone"),
    ("v3d_shadow_lvb_stop", "V3d shadow LVB stop"),
    ("v3d_shadow_r_potential_pts", "V3d shadow R potential pts"),
    # MTF
    ("mtf_shadow_htf_used", "MTF shadow HTF used"),
    # NAS
    ("nas_signal_active", "NAS signal active"),
    ("direction_intended", "Direction intended"),
    ("bubble_gate_impact_reason", "Bubble gate impact reason"),
    # Direction etc.
    ("direction", "Direção"),
    ("classification", "Classificação"),
    ("summary", "Resumo"),
    ("confluences", "Confluências"),
    ("main_blocker", "Bloqueio principal"),
    ("rr_estimated", "R:R estimado"),
    ("missing_trigger", "Gatilho faltante"),
    ("next_action", "Próxima ação"),
    ("health", "Health"),
    ("action_taken", "Ação tomada"),
    # V4 / Oracle (strings raw)
    ("classification_v4_shadow", "Classificação V4"),
    ("oracle_score_raw", "Oracle Score"),
]

# Bool fields: extract string then convert
FIELDS_BOOL = [
    ("v3d_shadow_event_present", "V3d shadow event present"),
    ("v3d_shadow_in_zone", "V3d shadow in zone now"),
    ("mtf_shadow_applicable", "MTF shadow applicable"),
    ("mtf_shadow_aligned", "MTF shadow aligned"),
    ("would_promote_without_bubble_gate", "Would promote without bubble gate"),
]

# Int fields
FIELDS_INT = [
    ("bubble_cluster_count", "Bubble cluster count"),
    ("nas_signal_recent_bars", "NAS signal recent bars"),
    ("oracle_score_shadow", "Oracle Score"),  # int parsing from "Oracle Score: 2"
]

# Float-via-first-number fields
FIELDS_FLOAT = [
    ("entry_late_distance_r", "Entry late distance R"),
    ("bubble_cluster_distance_r", "Bubble cluster distance R"),
]


def is_empty(value):
    """Define o que conta como 'vazio' pra justificar overwrite."""
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    return False


def migrate_record(rec):
    """Re-aplica parser. Retorna (updated_record, list_of_changes)."""
    stdout = rec.get("claude_stdout", "") or ""
    if not stdout:
        return rec, []
    changes = []
    new_rec = dict(rec)

    # String fields
    for key, label in FIELDS_STRING:
        old = new_rec.get(key)
        if not is_empty(old):
            continue
        new_val = extract_field(stdout, label)
        if new_val and new_val != old:
            new_rec[key] = new_val
            changes.append((key, old, new_val))

    # Bool fields
    for key, label in FIELDS_BOOL:
        old = new_rec.get(key)
        if old is not None:
            continue
        raw = extract_field(stdout, label)
        new_val = _bool_or_none(raw)
        if new_val is not None:
            new_rec[key] = new_val
            changes.append((key, old, new_val))

    # Int fields
    for key, label in FIELDS_INT:
        old = new_rec.get(key)
        if old is not None:
            continue
        raw = extract_field(stdout, label)
        new_val = _int_or_none(raw)
        if new_val is not None:
            new_rec[key] = new_val
            changes.append((key, old, new_val))

    # Float fields
    for key, label in FIELDS_FLOAT:
        old = new_rec.get(key)
        if old is not None and not (isinstance(old, str) and old.strip() == ""):
            continue
        raw = extract_field(stdout, label)
        new_val = _float_from_first_number(raw)
        if new_val is not None:
            new_rec[key] = new_val
            changes.append((key, old, new_val))

    return new_rec, changes


def main():
    parser = argparse.ArgumentParser(description="Migrate research log with parser v2")
    parser.add_argument("--apply", action="store_true", help="Apply changes (default is dry-run)")
    parser.add_argument("--dry-run", action="store_true", help="Report only, do not modify")
    args = parser.parse_args()

    if not args.apply and not args.dry_run:
        args.dry_run = True

    if not LOG_FILE.exists():
        print(f"❌ Log file not found: {LOG_FILE}")
        return 1

    print(f"Reading {LOG_FILE} ...")
    records = []
    with LOG_FILE.open() as f:
        for ln in f:
            try:
                records.append(json.loads(ln))
            except Exception as e:
                print(f"  ⚠️  parse error: {e}")
    print(f"Total records: {len(records)}")

    # Process
    all_changes = []
    updated_records = []
    records_changed = 0
    for rec in records:
        new_rec, changes = migrate_record(rec)
        if changes:
            records_changed += 1
            all_changes.extend(changes)
        updated_records.append(new_rec)

    print(f"\nRecords with changes: {records_changed}/{len(records)} "
          f"({records_changed/max(len(records),1)*100:.1f}%)")
    print(f"Total field updates: {len(all_changes)}")

    # Breakdown per field
    from collections import Counter
    by_field = Counter(c[0] for c in all_changes)
    print(f"\nField updates breakdown:")
    for field, n in by_field.most_common():
        print(f"  {field:<35} {n}")

    # Sample changes
    if all_changes:
        print(f"\nSample changes (first 10):")
        for key, old, new in all_changes[:10]:
            old_str = repr(old)[:30]
            new_str = repr(new)[:30]
            print(f"  {key:<35} {old_str} → {new_str}")

    if args.dry_run:
        print(f"\n🔍 DRY RUN — nothing written. Run with --apply to commit.")
        return 0

    # Apply: backup + atomic write
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_path = LOG_DIR / f"setup_research_log.jsonl.bak_{timestamp}"
    print(f"\nCreating backup: {backup_path}")
    shutil.copy2(LOG_FILE, backup_path)

    # Atomic write via tmp file
    tmp_path = LOG_FILE.with_suffix(".jsonl.migrating")
    with tmp_path.open("w") as f:
        for rec in updated_records:
            f.write(json.dumps(rec, default=str, ensure_ascii=False) + "\n")
    tmp_path.replace(LOG_FILE)

    print(f"\n✅ Migration applied:")
    print(f"   Updated records: {records_changed}")
    print(f"   Total field updates: {len(all_changes)}")
    print(f"   Backup: {backup_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
