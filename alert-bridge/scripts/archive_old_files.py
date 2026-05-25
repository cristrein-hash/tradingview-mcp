#!/usr/bin/env python3
"""
Archive automation: move .bak* and old screenshots to backups/.

- .bak* files in alert-bridge/logs/ → backups/bak_archive/  (idempotent, no age filter — anything ending in .bak/.bak_* is finalized)
- screenshots/*.png|.jpg older than 30 days → backups/screenshots_archive/YYYY-MM/

Idempotent: dest names get suffix _N if collision. Atomic move (rename within same fs).
"""
from __future__ import annotations
import argparse
import re
import shutil
import subprocess
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

# --- New retention modes (2026-05-25). DRY-RUN BY DEFAULT: these act only with --apply.
# Not included in mode "all" — preserves the archive-weekly LaunchAgent behavior. ---
BACKTESTS_DIR = LOGS_DIR / "backtests"
BACKTEST_KEEP_VERSIONS = 1   # keep top-N versions per window (1 = only the max version)
LAUNCHD_CAP_MB = 5           # copytruncate launchd_*.log above this size
BAK_RETENTION_DAYS = 90      # prune bak_archive entries older than this
_VERSIONED = re.compile(r"^(?P<win>.+)_v(?P<ver>\d+)\.jsonl$")


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


# ----------------------------------------------------------------------------
# Protections shared by the new destructive modes.
# ----------------------------------------------------------------------------
def _git_ignored(path: Path) -> bool:
    """True only if git treats the path as ignored. Hard gate: never touch tracked files.
    On any error, returns False (treat as tracked → protected)."""
    try:
        r = subprocess.run(["git", "check-ignore", "-q", str(path)], cwd=str(ROOT), timeout=10)
        return r.returncode == 0
    except Exception:
        return False


def _has_open_handle(path: Path) -> bool:
    """True if a process holds the file open. On error, returns True (conservative → protected)."""
    try:
        r = subprocess.run(["lsof", "--", str(path)], capture_output=True, timeout=10)
        return r.returncode == 0 and bool(r.stdout.strip())
    except Exception:
        return True


def _safe_to_delete(path: Path) -> tuple[bool, str]:
    if not _git_ignored(path):
        return False, "tracked (not gitignored)"
    if _has_open_handle(path):
        return False, "open handle"
    return True, ""


def prune_backtests(apply: bool = False) -> int:
    """Keep top BACKTEST_KEEP_VERSIONS versions per window; mark superseded _vN.jsonl and
    orphaned *.checkpoint.json (whose .jsonl is gone) for deletion. Unversioned files are
    always protected. Dry-run unless apply=True."""
    if not BACKTESTS_DIR.exists():
        print(f"[backtests] {BACKTESTS_DIR} não existe — skip", file=sys.stderr)
        return 0

    windows: dict[str, list[tuple[int, Path]]] = {}
    unversioned: list[Path] = []
    for f in sorted(BACKTESTS_DIR.glob("*.jsonl")):
        m = _VERSIONED.match(f.name)
        if m:
            windows.setdefault(m.group("win"), []).append((int(m.group("ver")), f))
        else:
            unversioned.append(f)

    delete_jsonl: list[Path] = []
    for win, items in windows.items():
        versions = sorted({v for v, _ in items}, reverse=True)
        keep = set(versions[:BACKTEST_KEEP_VERSIONS])
        for v, f in items:
            if v not in keep:
                delete_jsonl.append(f)

    # Orphaned checkpoints: a *.checkpoint.json whose sibling .jsonl is missing or being deleted.
    delete_set = set(delete_jsonl)
    orphan_ckpt: list[Path] = []
    for c in sorted(BACKTESTS_DIR.glob("*.checkpoint.json")):
        sibling = c.with_name(c.name.replace(".checkpoint.json", ".jsonl"))
        if not sibling.exists() or sibling in delete_set:
            orphan_ckpt.append(c)

    print(f"[backtests] windows={len(windows)} unversioned_protected={len(unversioned)} "
          f"superseded_jsonl={len(delete_jsonl)} orphan_checkpoints={len(orphan_ckpt)} "
          f"(keep_versions={BACKTEST_KEEP_VERSIONS})")
    for f in unversioned:
        print(f"[backtests][keep] unversioned (protected): {f.name}")

    n = 0
    for f in delete_jsonl + orphan_ckpt:
        ok, why = _safe_to_delete(f)
        size = f.stat().st_size if f.exists() else 0
        if not ok:
            print(f"[backtests][PROTECTED:{why}] {f.name}")
            continue
        if apply:
            f.unlink()
            print(f"[backtests][del] {f.name} ({size/1024/1024:.1f} MB)")
        else:
            print(f"[backtests][dry] would delete {f.name} ({size/1024/1024:.1f} MB)")
        n += 1
    return n


def truncate_launchd(apply: bool = False) -> int:
    """copytruncate launchd_*.log above LAUNCHD_CAP_MB, preserving the inode so launchd's
    open append fd keeps working. Never deletes. Dry-run unless apply=True."""
    cap = LAUNCHD_CAP_MB * 1024 * 1024
    n = 0
    for f in sorted(LOGS_DIR.glob("launchd_*.log")):
        size = f.stat().st_size
        if size <= cap:
            continue
        if not _git_ignored(f):
            print(f"[launchd][PROTECTED:tracked] {f.name}")
            continue
        if apply:
            with open(f, "rb") as fh:
                fh.seek(-cap, 2)
                tail = fh.read()
            with open(f, "wb") as fh:   # truncates the SAME inode (no unlink) → launchd fd survives
                fh.write(tail)
            print(f"[launchd][truncate] {f.name} {size/1024/1024:.1f}MB -> {LAUNCHD_CAP_MB}MB (copytruncate)")
        else:
            print(f"[launchd][dry] would copytruncate {f.name} ({size/1024/1024:.1f}MB -> {LAUNCHD_CAP_MB}MB)")
        n += 1
    if n == 0:
        print(f"[launchd] no logs above {LAUNCHD_CAP_MB}MB")
    return n


def prune_bak_archive(apply: bool = False) -> int:
    """Delete backups/bak_archive entries older than BAK_RETENTION_DAYS. Dry-run unless apply=True."""
    if not BAK_ARCHIVE.exists():
        print(f"[bak-prune] {BAK_ARCHIVE} não existe — skip", file=sys.stderr)
        return 0
    now = time.time()
    cutoff = now - BAK_RETENTION_DAYS * 86400
    n = 0
    for f in sorted(BAK_ARCHIVE.iterdir()):
        if not f.is_file():
            continue
        mtime = f.stat().st_mtime
        if mtime >= cutoff:
            continue
        age = (now - mtime) / 86400
        ok, why = _safe_to_delete(f)
        if not ok:
            print(f"[bak-prune][PROTECTED:{why}] {f.name}")
            continue
        if apply:
            f.unlink()
            print(f"[bak-prune][del] {f.name} (age {age:.0f}d)")
        else:
            print(f"[bak-prune][dry] would delete {f.name} (age {age:.0f}d)")
        n += 1
    if n == 0:
        print(f"[bak-prune] nothing older than {BAK_RETENTION_DAYS}d")
    return n


def main():
    parser = argparse.ArgumentParser(description="Archive .bak/screenshots; retention for backtests/launchd/bak_archive")
    parser.add_argument("--mode", choices=["bak", "screenshots", "all", "backtests", "launchd", "bak-prune"], default="all")
    parser.add_argument("--dry-run", action="store_true", help="legacy modes (bak/screenshots/all): preview only")
    parser.add_argument("--apply", action="store_true",
                        help="new modes (backtests/launchd/bak-prune): actually act. Without it, they DRY-RUN.")
    parser.add_argument("--max-age-days", type=int, default=SCREENSHOT_MAX_AGE_DAYS,
                        help=f"Screenshots age threshold (default {SCREENSHOT_MAX_AGE_DAYS})")
    args = parser.parse_args()

    stamp = datetime.now().isoformat(timespec="seconds")
    print(f"[archive_old_files] start {stamp} mode={args.mode} dry_run={args.dry_run} apply={args.apply}")

    total = 0
    # Legacy modes — behavior unchanged (act unless --dry-run). "all" stays bak+screenshots only.
    if args.mode in ("bak", "all"):
        total += archive_baks(dry_run=args.dry_run)
    if args.mode in ("screenshots", "all"):
        total += archive_screenshots(dry_run=args.dry_run, max_age_days=args.max_age_days)
    # New retention modes — DRY-RUN unless --apply. Never part of "all".
    if args.mode == "backtests":
        total += prune_backtests(apply=args.apply)
    if args.mode == "launchd":
        total += truncate_launchd(apply=args.apply)
    if args.mode == "bak-prune":
        total += prune_bak_archive(apply=args.apply)

    print(f"[archive_old_files] done total={total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
