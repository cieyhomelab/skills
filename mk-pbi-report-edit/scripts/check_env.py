#!/usr/bin/env python3
"""Check the Python environment for mk-pbi-report-edit.

Usage: python scripts/check_env.py
Exit code 0: the environment is ready. Exit code 1: a package or a version is missing.
"""

import importlib
import sys

MIN_PYTHON = (3, 9)  # pathlib and json features used by the scripts need 3.9
PACKAGES = {
    # module name: pip package name
    "jsonschema": "jsonschema",
    "referencing": "referencing",  # installed with jsonschema 4.18 and later
}


def main() -> int:
    problems = []
    if sys.version_info < MIN_PYTHON:
        problems.append(
            f"Python {sys.version_info.major}.{sys.version_info.minor} is too old. "
            f"Install Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]} or later from https://www.python.org/downloads/"
        )
    missing = []
    for module, package in PACKAGES.items():
        try:
            importlib.import_module(module)
        except ImportError:
            missing.append(package)
    if missing:
        problems.append(
            "Missing packages: "
            + ", ".join(missing)
            + ". Install command: python -m pip install --upgrade "
            + " ".join(sorted(set(missing)))
        )
    if problems:
        for p in problems:
            print("PROBLEM: " + p)
        return 1
    print(f"OK: Python {sys.version.split()[0]}, packages: " + ", ".join(PACKAGES))
    return 0


if __name__ == "__main__":
    sys.exit(main())
