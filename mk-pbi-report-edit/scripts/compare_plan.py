#!/usr/bin/env python3
"""Compare the changed report files with the files list of the plan.

Usage: python scripts/compare_plan.py -- <plan file> <backup folder> <report folder>

<backup folder> is <report folder>/_backup/<timestamp>. It contains <report name>.Report
and semantic-model-hashes.json (both made by backup_report.py).
The plan file has a section "## Files" with lines "- create: <path>", "- modify: <path>", "- delete: <path>".
Paths are relative to the <report name>.Report folder.

Exit code 0: the changed files are equal to the plan and the semantic model did not change.
Exit code 1: a difference or an error (each line tells the cause).
"""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

LINE_RE = re.compile(r"^\s*-\s*(create|modify|delete):\s*`?([^`]+?)`?\s*$")
FILES_RE = re.compile(r"^## Files\s*$(.*?)(?=^## |\Z)", flags=re.MULTILINE | re.DOTALL)
SKIP_DIRS = {".pbi"}  # Desktop cache and local settings; Desktop changes them without a report change


def tree(root: Path) -> dict:
    out = {}
    for p in sorted(root.rglob("*")):
        rel = p.relative_to(root)
        if p.is_file() and not any(part in SKIP_DIRS for part in rel.parts):
            out[rel.as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def read_plan(path: Path):
    """Return the planned files {path: action} and a list of problems."""
    m = FILES_RE.search(path.read_text(encoding="utf-8-sig"))
    if not m:
        return {}, ["the plan file has no '## Files' section"]
    planned, problems = {}, []
    for line in m.group(1).splitlines():
        if not line.strip():
            continue
        lm = LINE_RE.match(line)
        if not lm:
            problems.append(f"plan line has an unknown shape: {line.strip()}")
            continue
        action, rel = lm.group(1), lm.group(2).strip().replace("\\", "/").removeprefix("./")
        if ".." in rel.split("/"):
            problems.append(f"plan path goes outside the report: {rel}")
            continue
        planned[rel] = action
    return planned, problems


def diff_trees(before: dict, after: dict) -> dict:
    actual = {rel: "create" for rel in after.keys() - before.keys()}
    actual.update({rel: "delete" for rel in before.keys() - after.keys()})
    actual.update({rel: "modify" for rel in before.keys() & after.keys() if before[rel] != after[rel]})
    return actual


def compare(planned: dict, actual: dict) -> list:
    problems = []
    for rel, act in sorted(actual.items()):
        if rel not in planned:
            problems.append(f"{act} {rel}: the plan does not have this file")
        elif planned[rel] != act:
            problems.append(f"{rel}: the plan says {planned[rel]}, the actual change is {act}")
    problems += [
        f"{act} {rel}: in the plan, but the file did not change"
        for rel, act in sorted(planned.items())
        if rel not in actual
    ]
    return problems


def check_model(hashes_file: Path, model_dir: Path) -> list:
    if not hashes_file.exists():
        return ["semantic-model-hashes.json is missing in the backup; the model check did not run"]
    if not model_dir.is_dir():
        return []
    old = json.loads(hashes_file.read_text(encoding="utf-8"))
    new = tree(model_dir)
    changed = sorted(k for k in old.keys() | new.keys() if old.get(k) != new.get(k))
    return [f"semantic model file changed: {rel} (the skill must not change the model)" for rel in changed]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("plan")
    ap.add_argument("backup")
    ap.add_argument("report_folder")
    a = ap.parse_args()

    backup, folder = Path(a.backup).resolve(), Path(a.report_folder).resolve()
    backups = list(backup.glob("*.Report"))
    if len(backups) != 1:
        print(f"ERROR: {backup} must contain one .Report folder; found {[b.name for b in backups]}")
        return 1
    name = backups[0].name
    current_dir = folder / name
    if not current_dir.is_dir():
        print(f"ERROR: {current_dir} does not exist")
        return 1

    planned, problems = read_plan(Path(a.plan))
    actual = diff_trees(tree(backups[0]), tree(current_dir))
    problems += compare(planned, actual)
    problems += check_model(backup / "semantic-model-hashes.json", folder / name.replace(".Report", ".SemanticModel"))

    print(f"Changed files: {len(actual)}, files in the plan: {len(planned)}")
    for rel, act in sorted(actual.items()):
        print(f"  {act}: {rel}")
    for p in problems:
        print("DIFFERENCE: " + p)
    if problems:
        return 1
    print("RESULT: the changed files are equal to the plan, and the semantic model did not change")
    return 0


if __name__ == "__main__":
    sys.exit(main())
