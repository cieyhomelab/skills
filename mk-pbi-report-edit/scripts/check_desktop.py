#!/usr/bin/env python3
"""Check if Power BI Desktop has the report open.

Usage: python scripts/check_desktop.py -- "<report name>"
Exit code 0: the report is not open.
Exit code 2: a Power BI Desktop window has the report name in its title.
Exit code 3: Power BI Desktop runs, but the window titles are not available. Ask the user.
Exit code 4: the check cannot run on this system (not Windows). Ask the user.
"""

import argparse
import csv
import io
import os
import subprocess
import sys
from pathlib import Path

PROCESS = "PBIDesktop.exe"
TIMEOUT = 30  # seconds; tasklist ends in a few seconds
NO_TITLE = {"N/A", ""}  # tasklist shows N/A when the window title is not available


def tasklist_path() -> str:
    """Use the full path, so that a different tasklist.exe in PATH cannot run."""
    root = os.environ.get("SYSTEMROOT", r"C:\Windows")
    return str(Path(root) / "System32" / "tasklist.exe")


def window_titles() -> list:
    args = [tasklist_path(), "/v", "/fo", "csv", "/fi", f"imagename eq {PROCESS}"]
    # fixed arguments, no shell, no untrusted input
    out = subprocess.run(args, capture_output=True, text=True, timeout=TIMEOUT, check=False).stdout  # noqa: S603
    rows = [r for r in csv.reader(io.StringIO(out)) if r and r[0].lower() == PROCESS.lower()]
    return [r[-1] for r in rows]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("report_name")
    args = ap.parse_args()

    if not sys.platform.startswith("win"):
        print("UNKNOWN: this check runs only on Windows. Ask the user if the report is closed.")
        return 4
    try:
        titles = window_titles()
    except (OSError, subprocess.TimeoutExpired) as e:
        print(f"UNKNOWN: tasklist failed ({e}). Ask the user if the report is closed.")
        return 3

    if not titles:
        print("OK: Power BI Desktop does not run.")
        return 0
    name = args.report_name.lower()
    for t in titles:
        if name in t.lower():
            print(f"OPEN: Power BI Desktop has the report open (window title: {t}). Ask the user to close it.")
            return 2
    if all(t.strip().upper() in NO_TITLE for t in titles):
        print("UNKNOWN: Power BI Desktop runs, but the window titles are not available. Ask the user.")
        return 3
    print("OK: Power BI Desktop runs, but no window has the report name. Open windows: " + "; ".join(titles))
    return 0


if __name__ == "__main__":
    sys.exit(main())
