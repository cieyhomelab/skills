#!/usr/bin/env python3
"""Validate the JSON files of a PBIR report against their schemas and check the structure.

Usage: python scripts/validate_pbir.py [--offline] [--cache-dir DIR] -- <report name>.Report

The script reads the $schema URL of each file, downloads the schema one time, and keeps it in a cache.
It downloads schemas only from ALLOWED_HOSTS over https. A different URL is an error.
Structure checks: valid JSON, page and visual names equal to folder names, pages.json against the page folders,
unique visual names in a page.

Exit code 0: all files are valid.
Exit code 1: a file has an error.
Exit code 2: no errors, but a schema was not available (offline or download failed). This is not a pass.
"""

import argparse
import hashlib
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

ALLOWED_HOSTS = {"developer.microsoft.com"}  # Microsoft publishes the PBIR schemas only here
TIMEOUT = 30  # seconds; a schema file is small, most downloads end in under 5 seconds
MAX_ERRORS_PER_FILE = 10  # enough to correct a file; more errors make the output hard to read
NEEDS_SCHEMA = {"page.json", "visual.json", "pages.json", "report.json"}

try:
    import jsonschema
    from referencing import Registry, Resource
    from referencing.jsonschema import DRAFT7, specification_with
except ImportError:
    print("ERROR: missing packages. Install command: python -m pip install --upgrade jsonschema referencing")
    sys.exit(1)


def default_cache() -> Path:
    base = os.environ.get("LOCALAPPDATA") or str(Path.home() / ".cache")
    return Path(base) / "mk-pbi-report-edit" / "schema-cache"


class SchemaStore:
    """Download schemas from ALLOWED_HOSTS and keep them in a cache folder."""

    def __init__(self, cache: Path, offline: bool):
        self.cache, self.offline = cache, offline
        self.cache.mkdir(parents=True, exist_ok=True)
        self.default_spec = DRAFT7  # the PBIR schemas use draft-07; a $ref file can omit $schema

    def get(self, url: str):
        u = urlparse(url)
        if u.scheme != "https" or u.hostname not in ALLOWED_HOSTS:
            raise ValueError(f"schema URL is not permitted: {url} (permitted hosts: {sorted(ALLOWED_HOSTS)})")
        path = self.cache / (hashlib.sha256(url.encode()).hexdigest()[:32] + ".json")
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        if self.offline:
            raise LookupError("offline and not in cache")
        req = urllib.request.Request(url, headers={"User-Agent": "mk-pbi-report-edit-validator"})  # noqa: S310 (https and host checked above)
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:  # noqa: S310 (https and host checked above)
            schema = json.loads(r.read().decode("utf-8-sig"))
        path.write_text(json.dumps(schema), encoding="utf-8")
        return schema

    def retrieve(self, uri: str):
        return Resource.from_contents(self.get(uri), default_specification=self.default_spec)


class Result:
    def __init__(self):
        self.errors, self.not_checked, self.checked, self.docs = [], [], 0, {}


def schema_errors(store, registry, schema, doc):
    store.default_spec = specification_with(schema.get("$schema", ""), default=DRAFT7)
    cls = jsonschema.validators.validator_for(schema, default=jsonschema.Draft7Validator)
    return sorted(cls(schema, registry=registry).iter_errors(doc), key=lambda e: list(e.absolute_path))


def check_file(p: Path, rel: str, store, registry, res: Result) -> None:
    try:
        doc = json.loads(p.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as e:
        res.errors.append(f"{rel}: invalid JSON ({e})")
        return
    res.docs[rel] = doc
    url = doc.get("$schema") if isinstance(doc, dict) else None
    if not url:
        if p.name in NEEDS_SCHEMA:
            res.errors.append(f"{rel}: the $schema field is missing")
        return
    try:
        schema = store.get(url)
    except ValueError as e:
        res.errors.append(f"{rel}: {e}")
        return
    except (LookupError, urllib.error.URLError, OSError, json.JSONDecodeError) as e:
        res.not_checked.append(f"{rel}: schema not available ({type(e).__name__}: {e})")
        return
    try:
        found = schema_errors(store, registry, schema, doc)
    # A schema problem (unresolved remote $ref, unknown draft, download error in a $ref) must not stop
    # the run. The file is then reported as "not checked", which is not a pass.
    except Exception as e:  # noqa: BLE001
        res.not_checked.append(f"{rel}: schema could not be used ({type(e).__name__}: {e})")
        return
    res.checked += 1
    for e in found[:MAX_ERRORS_PER_FILE]:
        loc = "/".join(str(x) for x in e.absolute_path) or "(root)"
        res.errors.append(f"{rel}: {loc}: {e.message[:300]}")
    if len(found) > MAX_ERRORS_PER_FILE:
        res.errors.append(f"{rel}: {len(found) - MAX_ERRORS_PER_FILE} more schema errors")


def check_page_order(pj, page_folders: list, errors: list) -> None:
    if not isinstance(pj, dict):
        errors.append("definition/pages/pages.json is missing or invalid")
        return
    order = pj.get("pageOrder", [])
    errors += [
        f"pages.json: pageOrder has '{n}', but the folder pages/{n} does not exist"
        for n in order
        if n not in page_folders
    ]
    errors += [f"pages.json: the folder pages/{n} is not in pageOrder" for n in page_folders if n not in order]
    if len(order) != len(set(order)):
        errors.append("pages.json: pageOrder has a duplicate name")
    act = pj.get("activePageName")
    if act and act not in order:
        errors.append(f"pages.json: activePageName '{act}' is not in pageOrder")


def check_visuals(vdir: Path, page: str, docs: dict, errors: list) -> None:
    names = set()
    folders = sorted(p.name for p in vdir.iterdir() if p.is_dir()) if vdir.is_dir() else []
    for vf in folders:
        vrel = f"definition/pages/{page}/visuals/{vf}/visual.json"
        v = docs.get(vrel)
        if not isinstance(v, dict):
            errors.append(f"{vrel} is missing or invalid")
            continue
        if v.get("name") != vf:
            errors.append(f"{vrel}: name '{v.get('name')}' is not equal to the folder name '{vf}'")
        if v.get("name") in names:
            errors.append(f"{vrel}: duplicate visual name '{v.get('name')}' on the page")
        names.add(v.get("name"))
        parent = v.get("parentGroupName")
        if parent and not (vdir / parent).is_dir():
            errors.append(f"{vrel}: parentGroupName '{parent}' does not exist on the page")


def check_structure(d: Path, res: Result) -> None:
    pages_dir = d / "pages"
    if not pages_dir.is_dir():
        res.errors.append("definition/pages/ is missing")
        return
    page_folders = sorted(p.name for p in pages_dir.iterdir() if p.is_dir())
    check_page_order(res.docs.get("definition/pages/pages.json"), page_folders, res.errors)
    for pf in page_folders:
        rel = f"definition/pages/{pf}/page.json"
        page = res.docs.get(rel)
        if not isinstance(page, dict):
            res.errors.append(f"{rel} is missing or invalid")
        elif page.get("name") != pf:
            res.errors.append(f"{rel}: name '{page.get('name')}' is not equal to the folder name '{pf}'")
        check_visuals(pages_dir / pf / "visuals", pf, res.docs, res.errors)


def report(files: int, res: Result) -> int:
    print(
        f"Files: {files}, checked against a schema: {res.checked}, "
        f"errors: {len(res.errors)}, schema not checked: {len(res.not_checked)}"
    )
    for e in res.errors:
        print("ERROR: " + e)
    for n in res.not_checked:
        print("NOT CHECKED: " + n)
    if res.errors:
        return 1
    if res.not_checked:
        print("RESULT: no errors, but some files have no schema check. This is not a pass.")
        return 2
    print("RESULT: all files are valid")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true", help="use only the schema cache")
    ap.add_argument("--cache-dir", default=None)
    ap.add_argument("report_dir")
    a = ap.parse_args()

    root = Path(a.report_dir).resolve()
    if root.name == "definition":
        root = root.parent
    d = root / "definition"
    if not d.is_dir():
        print(f"ERROR: {d} does not exist. Give the <report name>.Report folder.")
        return 1

    store = SchemaStore(Path(a.cache_dir) if a.cache_dir else default_cache(), a.offline)
    registry = Registry(retrieve=store.retrieve)
    res = Result()
    files = [p for p in sorted(d.rglob("*.json")) if ".pbi" not in p.relative_to(root).parts]
    for p in files:
        check_file(p, p.relative_to(root).as_posix(), store, registry, res)
    check_structure(d, res)
    return report(len(files), res)


if __name__ == "__main__":
    sys.exit(main())
