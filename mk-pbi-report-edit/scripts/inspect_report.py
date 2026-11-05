#!/usr/bin/env python3
"""Show the pages, visuals, fields, and layout problems of a PBIR report.

Usage:
  python scripts/inspect_report.py -- <report definition>            overview + layout warnings
  python scripts/inspect_report.py --fields -- <report definition>   all fields as JSON
  python scripts/inspect_report.py --json -- <report definition>     overview as JSON

<report definition> is the folder <report name>.Report/definition (the .Report folder also works).
Exit code 0: done. Exit code 1: the folder is not a PBIR definition.
"""

import argparse
import json
import sys
from pathlib import Path

DEFAULT_PAGE = (1280, 720)  # Power BI Desktop default page size (16:9)
MIN_OVERLAP = 4  # pixels; smaller overlaps come from rounding and are not reported
TOLERANCE = 0.5  # pixels; positions can have decimals after a resize in Desktop


def load(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as e:
        return {"__error__": f"{type(e).__name__}: {e}"}


def literal(v):
    try:
        return v["expr"]["Literal"]["Value"]
    except (KeyError, TypeError):
        return None


def title_of(visual: dict):
    for key in ("visualContainerObjects", "objects"):
        for entry in (visual.get("visual", {}).get(key, {}) or {}).get("title", []) or []:
            t = literal(entry.get("properties", {}).get("text", {}))
            if t:
                return t.strip("'")
    return None


def add(out, table, prop, kind, where):
    out.setdefault((table, prop, kind), set()).add(where)


def table_of(ref: dict, aliases: dict):
    src = (ref.get("Expression") or {}).get("SourceRef") or {}
    return src.get("Entity") or aliases.get(src.get("Source"))


def collect_fields(node, where, out, aliases=None):
    """Walk any JSON node. Record Column, Measure, and hierarchy references with their table."""
    aliases = dict(aliases or {})
    if isinstance(node, list):
        for v in node:
            collect_fields(v, where, out, aliases)
        return
    if not isinstance(node, dict):
        return
    for f in node.get("From", []) if isinstance(node.get("From"), list) else []:
        if isinstance(f, dict) and "Name" in f and "Entity" in f:
            aliases[f["Name"]] = f["Entity"]
    for key, kind in (("Column", "column"), ("Measure", "measure"), ("PropertyVariationSource", "column")):
        ref = node.get(key)
        if isinstance(ref, dict) and "Property" in ref and table_of(ref, aliases):
            add(out, table_of(ref, aliases), ref["Property"], kind, where)
    for v in node.values():
        collect_fields(v, where, out, aliases)


def visual_item(v: dict, folder: str) -> dict:
    pos = v.get("position", {})
    vtype = "group" if "visualGroup" in v else v.get("visual", {}).get("visualType", "unknown")
    return {
        "name": v.get("name", folder),
        "type": vtype,
        "title": title_of(v),
        "x": pos.get("x", 0),
        "y": pos.get("y", 0),
        "width": pos.get("width", 0),
        "height": pos.get("height", 0),
        "z": pos.get("z", 0),
        "parent": v.get("parentGroupName"),
    }


def outside(item: dict, pw, ph) -> bool:
    return (
        item["x"] < 0
        or item["y"] < 0
        or item["x"] + item["width"] > pw + TOLERANCE
        or item["y"] + item["height"] > ph + TOLERANCE
    )


def overlaps(top: list) -> list:
    pairs = []
    for i, p in enumerate(top):
        for q in top[i + 1 :]:
            ox = min(p["x"] + p["width"], q["x"] + q["width"]) - max(p["x"], q["x"])
            oy = min(p["y"] + p["height"], q["y"] + q["height"]) - max(p["y"], q["y"])
            if ox > MIN_OVERLAP and oy > MIN_OVERLAP:
                pairs.append((p["name"], q["name"]))
    return pairs


def inspect_page(pd: Path, order: list, fields: dict, warnings: list):
    rel_page = f"pages/{pd.name}/page.json"
    page = load(pd / "page.json")
    if "__error__" in page:
        warnings.append(f"{rel_page}: cannot read ({page['__error__']})")
        return None
    collect_fields(page.get("filterConfig", {}), rel_page, fields)
    pw, ph = page.get("width", DEFAULT_PAGE[0]), page.get("height", DEFAULT_PAGE[1])
    visuals = []
    vroot = pd / "visuals"
    for vd in sorted(vroot.iterdir()) if vroot.is_dir() else []:
        rel = f"pages/{pd.name}/visuals/{vd.name}/visual.json"
        v = load(vd / "visual.json")
        if "__error__" in v:
            warnings.append(f"{rel}: cannot read ({v['__error__']})")
            continue
        collect_fields(v.get("visual", {}).get("query", {}), rel, fields)
        collect_fields(v.get("filterConfig", {}), rel, fields)
        item = visual_item(v, vd.name)
        visuals.append(item)
        if outside(item, pw, ph):
            warnings.append(f"{rel}: the visual is outside the page ({pw}x{ph})")
    top = [v for v in visuals if v["type"] != "group" and not v["parent"]]
    warnings += [f"pages/{pd.name}: visuals {a} and {b} overlap" for a, b in overlaps(top)]
    return {
        "name": page.get("name", pd.name),
        "displayName": page.get("displayName"),
        "width": pw,
        "height": ph,
        "in_page_order": pd.name in order,
        "free_space_below_y": max([v["y"] + v["height"] for v in top], default=0),
        "visuals": visuals,
    }


def print_overview(pages: list, fields: dict, warnings: list) -> None:
    for p in pages:
        flag = "" if p["in_page_order"] else "  [not in pages.json pageOrder]"
        print(
            f"PAGE {p['displayName']!r} ({p['name']}) {p['width']}x{p['height']}, "
            f"{len(p['visuals'])} visuals, free space below y={p['free_space_below_y']}{flag}"
        )
        for v in sorted(p["visuals"], key=lambda v: (v["y"], v["x"])):
            t = f" {v['title']!r}" if v["title"] else ""
            print(f"  {v['type']}{t} ({v['name']}) x={v['x']} y={v['y']} w={v['width']} h={v['height']} z={v['z']}")
    print(f"FIELDS: {len(fields)} unique (use --fields for the list)")
    for w in warnings:
        print("WARNING: " + w)
    if not warnings:
        print("LAYOUT: no warnings")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fields", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("definition")
    a = ap.parse_args()

    d = Path(a.definition).resolve()
    if (d / "definition").is_dir():
        d = d / "definition"
    pages_dir = d / "pages"
    if not pages_dir.is_dir():
        print(
            f"ERROR: {d} is not a PBIR definition folder (no pages/ folder). "
            "If the report has report.json only, it uses the old format."
        )
        return 1

    meta = load(pages_dir / "pages.json") if (pages_dir / "pages.json").exists() else {}
    order = meta.get("pageOrder", []) if isinstance(meta, dict) else []
    page_dirs = sorted(
        (p for p in pages_dir.iterdir() if p.is_dir()),
        key=lambda p: order.index(p.name) if p.name in order else len(order),
    )

    fields, warnings = {}, []
    if (d / "report.json").exists():
        collect_fields(load(d / "report.json").get("filterConfig", {}), "report.json", fields)
    pages = [p for p in (inspect_page(pd, order, fields, warnings) for pd in page_dirs) if p]

    if a.fields:
        print(
            json.dumps(
                [
                    {"table": t, "name": n, "kind": k, "ref": f"{t}[{n}]", "used_in": sorted(w)}
                    for (t, n, k), w in sorted(fields.items())
                ],
                indent=2,
                ensure_ascii=False,
            )
        )
    elif a.json:
        print(json.dumps({"pages": pages, "warnings": warnings}, indent=2, ensure_ascii=False))
    else:
        print_overview(pages, fields, warnings)
    return 0


if __name__ == "__main__":
    sys.exit(main())
