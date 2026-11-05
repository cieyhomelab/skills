#!/usr/bin/env python3
"""Make a backup of the report definition, or restore it.

Backup:  python scripts/backup_report.py -- <report folder> <report name> <timestamp>
Restore: python scripts/backup_report.py --restore -- <report folder> <report name> <timestamp>

Backup copies <report name>.Report to <report folder>/_backup/<timestamp>/<report name>.Report
and writes semantic-model-hashes.json, so that compare_plan.py can prove that the model did not change.
Restore first saves the current folder to _backup/<timestamp>-before-restore/, then copies the backup back.
Exit code 0: success. Exit code 1: error (the message tells the cause).
"""

import argparse
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

TIMESTAMP_RE = re.compile(r"^\d{8}-\d{4}$")  # format YYYYMMDD-HHMM from SKILL.md
NAME_RE = re.compile(r"[^\\/:*?\"<>|]+")  # characters that Windows does not permit in a file name
SKIP_DIRS = {".pbi"}  # Power BI Desktop cache and local settings; not part of the definition


class BackupError(Exception):
    """An error with a message for the user."""


def ignore(_dir, names):
    return [n for n in names if n in SKIP_DIRS]


def hash_tree(root: Path) -> dict:
    result = {}
    for p in sorted(root.rglob("*")):
        rel = p.relative_to(root)
        if p.is_file() and not any(part in SKIP_DIRS for part in rel.parts):
            result[rel.as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
    return result


def check_args(a) -> None:
    if not TIMESTAMP_RE.match(a.timestamp):
        raise BackupError(f"timestamp '{a.timestamp}' does not have the format YYYYMMDD-HHMM.")
    if not NAME_RE.fullmatch(a.report_name) or a.report_name in {".", ".."}:
        raise BackupError(f"report name '{a.report_name}' is not a valid file name.")


def do_backup(folder: Path, report_dir: Path, model_dir: Path, backup_dir: Path) -> None:
    if not report_dir.is_dir():
        found = [p.name for p in folder.glob("*.Report")]
        raise BackupError(f"{report_dir} does not exist. Report folders found: {found or 'none'}.")
    if backup_dir.exists():
        raise BackupError(f"{backup_dir} already exists. Use a new timestamp. Do not overwrite a backup.")
    backup_dir.mkdir(parents=True)
    backup_report = backup_dir / report_dir.name
    shutil.copytree(report_dir, backup_report, ignore=ignore)
    hashes = hash_tree(model_dir) if model_dir.is_dir() else {}
    hashes_file = backup_dir / "semantic-model-hashes.json"
    hashes_file.write_text(json.dumps(hashes, indent=2), encoding="utf-8")
    n = sum(1 for p in backup_report.rglob("*") if p.is_file())
    print(f"OK: backup of {n} files in {backup_report}")
    print(f"OK: hashes of {len(hashes)} semantic model files in {hashes_file}")


def clear_definition(report_dir: Path) -> None:
    """Remove the report files, but keep the .pbi folder: Desktop needs its local settings."""
    for child in report_dir.iterdir():
        if child.name in SKIP_DIRS:
            continue
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()


def do_restore(report_dir: Path, backup_root: Path, timestamp: str) -> None:
    backup_report = backup_root / timestamp / report_dir.name
    if not backup_report.is_dir():
        found = sorted(p.name for p in backup_root.glob("*")) if backup_root.is_dir() else []
        raise BackupError(f"backup {backup_report} does not exist. Backups found: {found or 'none'}.")
    safety_dir = backup_root / f"{timestamp}-before-restore"
    if safety_dir.exists():
        raise BackupError(f"{safety_dir} already exists. A restore was already done. Check it manually.")
    safety_dir.mkdir(parents=True)
    if report_dir.is_dir():
        shutil.copytree(report_dir, safety_dir / report_dir.name)
        clear_definition(report_dir)
    else:
        report_dir.mkdir()
    shutil.copytree(backup_report, report_dir, dirs_exist_ok=True)
    print(f"OK: restored {report_dir} from {backup_report}")
    print(f"OK: the folder before the restore is in {safety_dir}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--restore", action="store_true")
    ap.add_argument("report_folder")
    ap.add_argument("report_name")
    ap.add_argument("timestamp")
    a = ap.parse_args()

    folder = Path(a.report_folder).resolve()
    report_dir = folder / f"{a.report_name}.Report"
    model_dir = folder / f"{a.report_name}.SemanticModel"
    backup_root = folder / "_backup"
    try:
        check_args(a)
        if a.restore:
            do_restore(report_dir, backup_root, a.timestamp)
        else:
            do_backup(folder, report_dir, model_dir, backup_root / a.timestamp)
    except (BackupError, OSError) as e:
        print(f"ERROR: {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
