#!/usr/bin/env python3
"""
Archive automation: move .bak* and old screenshots to backups/.

- .bak* files in alert-bridge/logs/ → backups/bak_archive/  (idempotent, no age filter — anything ending in .bak/.bak_* is finalized)
- screenshots/*.png|.jpg older than 30 days → backups/screenshots_archive/YYYY-MM/

Idempotent: dest names get suffix _N if collision. Atomic move (rename within same fs).
"""
from __future__ import annotations
import argparse
import shutil
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path.home() / "tradingview-mcp"
LOGS_DIR = ROOT / "alert-bridge" / "logs"
SCREENSHOTS_DIR = ROOT / "screenshots"
BACKUPS_DIR = ROOT / "backups"
BAK_ARCHIVE = BACKUPS_DIR / "bak_archive"
SHOTS_ARCHIVE = BACKUPS_DIR / "screenshots_archive"

SCREENSHOT_MAX_AGE_DAYS = 30
BAK_PATTERNS = ("*.bak", "*.bak_*", "*.bak.*", "*.backup", "*.backup_*", "*.backup.*")
SHOT_PATTERNS = ("*.png", "*.jpg", "*.jpeg")


def unique_dest(dest: Path) -> Path:
    """Avoid overwrite: foo.bak → foo.bak_1, foo.bak_2, ..."""
    if not dest.exists():
        return dest
    stem, suffix = dest.name, ""
    n = 1
    while True:
        candidate = dest.with_name(f"{dest.name}_{n}")
        if not candidate.exists():
            return candidate
        n += 1


def archive_baks(dry_run: bool = False) -> int:
    BAK_ARCHIVE.mkdir(parents=True, exist_ok=True)
    moved = 0
    if not LOGS_DIR.exists():
        print(f"[bak] {LOGS_DIR} não existe — skip", file=sys.stderr)
        return 0
    seen = set()
    for pattern in BAK_PATTERNS:
        for src in LOGS_DIR.glob(pattern):
            if src in seen:
                continue
            seen.add(src)
            if not src.is_file():
                continue
            dest = unique_dest(BAK_ARCHIVE / src.name)
            size = src.stat().st_size
            if dry_run:
                print(f"[bak][dry] {src.name} ({size/1024:.1f} KB) → {dest}")
            else:
                shutil.move(str(src), str(dest))
                print(f"[bak] moved {src.name} ({size/1024:.1f} KB) → {dest.relative_to(BACKUPS_DIR)}")
            moved += 1
    # Also scan alert-bridge/ root for stray .bak (e.g. tv_webhook_receiver.py.bak_*)
    src_root = ROOT / "alert-bridge"
    for pattern in BAK_PATTERNS:
        for src in src_root.glob(pattern):
            if src in seen:
                continue
            seen.add(src)
            if not src.is_file():
                continue
            dest = unique_dest(BAK_ARCHIVE / src.name)
            size = src.stat().st_size
            if dry_run:
                print(f"[bak][dry] {src.name} ({size/1024:.1f} KB) → {dest}")
            else:
                shutil.move(str(src), str(dest))
                print(f"[bak] moved {src.name} ({size/1024:.1f} KB) → {dest.relative_to(BACKUPS_DIR)}")
            moved += 1
    return moved


def archive_screenshots(dry_run: bool = False, max_age_days: int = SCREENSHOT_MAX_AGE_DAYS) -> int:
    SHOTS_ARCHIVE.mkdir(parents=True, exist_ok=True)
    if not SCREENSHOTS_DIR.exists():
        print(f"[shots] {SCREENSHOTS_DIR} não existe — skip", file=sys.stderr)
        return 0
    cutoff = time.time() - max_age_days * 86400
    moved = 0
    bytes_moved = 0
    for pattern in SHOT_PATTERNS:
        for src in SCREENSHOTS_DIR.glob(pattern):
            if not src.is_file():
                continue
            mtime = src.stat().st_mtime
            if mtime >= cutoff:
                continue
            ym = datetime.fromtimestamp(mtime).strftime("%Y-%m")
            subdir = SHOTS_ARCHIVE / ym
            subdir.mkdir(parents=True, exist_ok=True)
            dest = unique_dest(subdir / src.name)
            size = src.stat().st_size
            if dry_run:
                print(f"[shots][dry] {src.name} (mtime={datetime.fromtimestamp(mtime):%Y-%m-%d}, {size/1024:.0f} KB) → {dest}")
            else:
                shutil.move(str(src), str(dest))
                bytes_moved += size
            moved += 1
    if not dry_run and moved:
        print(f"[shots] moved {moved} files, {bytes_moved/1024/1024:.1f} MB freed")
    elif not dry_run:
        print(f"[shots] no files older than {max_age_days} days")
    return moved


def main():
    parser = argparse.ArgumentParser(description="Archive .bak and old screenshots")
    parser.add_argument("--mode", choices=["bak", "screenshots", "all"], default="all")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--max-age-days", type=int, default=SCREENSHOT_MAX_AGE_DAYS,
                        help=f"Screenshots age threshold (default {SCREENSHOT_MAX_AGE_DAYS})")
    args = parser.parse_args()

    stamp = datetime.now().isoformat(timespec="seconds")
    print(f"[archive_old_files] start {stamp} mode={args.mode} dry_run={args.dry_run}")

    total = 0
    if args.mode in ("bak", "all"):
        total += archive_baks(dry_run=args.dry_run)
    if args.mode in ("screenshots", "all"):
        total += archive_screenshots(dry_run=args.dry_run, max_age_days=args.max_age_days)

    print(f"[archive_old_files] done total_moved={total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
