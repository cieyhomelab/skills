#!/usr/bin/env python3
"""Deterministic calculations for the mk-benchmark skill.

Commands:
  schedule <plan.md>                      Fill the empty or "auto" Sprint cells of the plan in place.
  check <plan.md>                         Validate the plan. Exit 1 on errors.
  analyze <plan.md> <snapshot.json> [--history DIR] [--save]
                                          Print the benchmark result as JSON.
                                          With --save, write DIR/<today>.json.

Needs only Python 3.8 or later. The model runs this script. It does not read it.
"""
import argparse
import datetime as dt
import json
import math
import os
import re
import sys

DEFAULT_SIZES = {"XS": 2, "S": 4, "M": 8, "L": 16, "XL": 32}  # hours of human focus work per size
SPI_ON_TRACK = 0.95  # SPI at or above this value: on track
SPI_AT_RISK = 0.80   # SPI at or above this value and below SPI_ON_TRACK: at risk
TREND_POINTS = 3     # the last 3 snapshots give the velocity trend
MAX_FORECAST_DAYS = 2000  # stop the forecast after about 8 years of working days

# Credit for each status: the part of the item's planned hours that counts as earned value.
CREDIT = {
    "Done": 1.0,
    "Done (no PR)": 1.0,
    "Ready to merge": 0.9,
    "In review": 0.7,
    "Building": 0.4,
    "Spec": 0.2,
    "Not started": 0.0,
    "Unknown": 0.0,
    "Dropped": 0.0,
}
UX_CREDIT = {"present": 1.0, "partial": 0.5, "missing": 0.0}
ID_RE = re.compile(r"^[A-Za-z0-9._-]+$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class PlanError(Exception):
    pass


# ---------- dates ----------

def parse_date(value, field):
    if not isinstance(value, str) or not DATE_RE.match(value):
        raise PlanError(f"{field}: expected YYYY-MM-DD, got {value!r}")
    return dt.date.fromisoformat(value)


def working_days_between(start, end):
    """Working days (Mon-Fri) in the range [start, end). Negative if end < start."""
    if end < start:
        return -working_days_between(end, start)
    days = 0
    d = start
    while d < end:
        if d.weekday() < 5:
            days += 1
        d += dt.timedelta(days=1)
    return days


def add_working_days(start, n):
    d = start
    left = int(math.ceil(n))
    while left > 0:
        d += dt.timedelta(days=1)
        if d.weekday() < 5:
            left -= 1
    return d


# ---------- plan ----------

HEADER_KEYS = {
    "type": "type",
    "start": "start",
    "sprint length (working days)": "sprint_days",
    "team fte": "fte",
    "focus hours per day": "focus_hours",
    "buffer": "buffer",
    "size table": "sizes",
    "baselined": "baselined",
}


def parse_table_row(line):
    cells = [c.strip() for c in line.strip().strip("|").split("|")]
    return cells


def read_plan(path):
    with open(path, encoding="utf-8") as f:
        lines = f.read().split("\n")
    header = {}
    table_start = None
    for i, line in enumerate(lines):
        m = re.match(r"^\s*-?\s*([A-Za-z ()]+):\s*(.+?)\s*$", line)
        if m and m.group(1).strip().lower() in HEADER_KEYS and table_start is None:
            header[HEADER_KEYS[m.group(1).strip().lower()]] = m.group(2)
        if line.strip().startswith("|") and table_start is None:
            table_start = i
    if table_start is None:
        raise PlanError("no item table found (a Markdown table with the columns Id | Issue | Title | Size | Sprint)")
    cols = [c.lower() for c in parse_table_row(lines[table_start])]
    need = ["id", "issue", "title", "size", "sprint"]
    missing = [c for c in need if c not in cols]
    if missing:
        raise PlanError(f"item table: missing columns {missing}; found {cols}")
    items = []
    row_lines = []
    for j in range(table_start + 2, len(lines)):
        line = lines[j]
        if not line.strip().startswith("|"):
            break
        cells = parse_table_row(line)
        if len(cells) < len(cols):
            cells += [""] * (len(cols) - len(cells))
        row = dict(zip(cols, cells))
        items.append(row)
        row_lines.append(j)
    return header, items, lines, table_start, cols, row_lines


def normalize_plan(header, items):
    errors = []
    plan = {}
    try:
        plan["start"] = parse_date(header.get("start", ""), "Start")
    except PlanError as e:
        errors.append(str(e))
    plan["type"] = (header.get("type") or "MVP").strip().upper()
    if plan["type"] not in ("POC", "MVP"):
        errors.append(f"Type: expected POC or MVP, got {plan['type']!r}")
    for key, label, default in (("sprint_days", "Sprint length (working days)", 10),
                                ("fte", "Team FTE", 1),
                                ("focus_hours", "Focus hours per day", 6)):
        raw = header.get(key)
        try:
            plan[key] = float(raw) if raw is not None else float(default)
            if plan[key] <= 0:
                raise ValueError
        except ValueError:
            errors.append(f"{label}: expected a positive number, got {raw!r}")
            plan[key] = float(default)
    raw_buffer = header.get("buffer")
    if raw_buffer is None:
        plan["buffer"] = 0.2 if plan["type"] == "POC" else 0.3
    else:
        m = re.match(r"^\s*(\d+(?:\.\d+)?)\s*%?\s*$", raw_buffer)
        if not m:
            errors.append(f"Buffer: expected a percent such as 30%, got {raw_buffer!r}")
            plan["buffer"] = 0.3
        else:
            plan["buffer"] = float(m.group(1)) / 100.0
    sizes = dict(DEFAULT_SIZES)
    if header.get("sizes"):
        sizes = {}
        for part in header["sizes"].split(","):
            m = re.match(r"^\s*([A-Za-z]+)\s*=\s*(\d+(?:\.\d+)?)\s*$", part)
            if not m:
                errors.append(f"Size table: cannot read {part.strip()!r}; use the form XS=2, S=4")
                continue
            sizes[m.group(1).upper()] = float(m.group(2))
    plan["sizes"] = sizes
    seen = set()
    norm_items = []
    for n, row in enumerate(items, 1):
        iid = row.get("id", "")
        if not ID_RE.match(iid):
            errors.append(f"row {n}: Id {iid!r} is not valid")
            continue
        if iid in seen:
            errors.append(f"row {n}: Id {iid} is a duplicate")
        seen.add(iid)
        issue_raw = re.sub(r"[^0-9]", "", row.get("issue", ""))
        size = row.get("size", "").strip().upper()
        if size not in sizes:
            errors.append(f"row {n} ({iid}): Size {size!r} is not in the size table {sorted(sizes)}")
            hours = 0.0
        else:
            hours = sizes[size]
        sprint = row.get("sprint", "").strip().lower()
        if sprint not in ("", "auto") and not sprint.isdigit():
            errors.append(f"row {n} ({iid}): Sprint {sprint!r} must be a number, auto, or empty")
        norm_items.append({
            "id": iid,
            "issue": int(issue_raw) if issue_raw else None,
            "title": row.get("title", ""),
            "size": size,
            "hours": hours,
            "sprint": int(sprint) if sprint.isdigit() else None,
        })
    if not norm_items:
        errors.append("the item table has no rows")
    plan["items"] = norm_items
    return plan, errors


def daily_capacity(plan):
    """Planned effort hours per working day, after the buffer."""
    return plan["fte"] * plan["focus_hours"] / (1.0 + plan["buffer"])


def cmd_check(path):
    header, items, *_ = read_plan(path)
    plan, errors = normalize_plan(header, items)
    total = sum(i["hours"] for i in plan["items"])
    out = {"ok": not errors, "errors": errors, "items": len(plan["items"]), "plannedHours": total}
    if not errors:
        days = math.ceil(total / daily_capacity(plan))
        out["plannedEnd"] = add_working_days(plan["start"], days).isoformat()
        out["plannedWorkingDays"] = days
    print(json.dumps(out, indent=2))
    return 0 if not errors else 1


def cmd_schedule(path):
    header, items, lines, table_start, cols, row_lines = read_plan(path)
    plan, errors = normalize_plan(header, items)
    if errors:
        print(json.dumps({"ok": False, "errors": errors}, indent=2))
        return 1
    per_sprint = daily_capacity(plan) * plan["sprint_days"]
    cum = 0.0
    sprint_idx = cols.index("sprint")
    changed = 0
    for item, j in zip(plan["items"], row_lines):
        cum += item["hours"]
        if item["sprint"] is None:
            cells = parse_table_row(lines[j])
            cells += [""] * (len(cols) - len(cells))
            cells[sprint_idx] = str(max(1, math.ceil(cum / per_sprint - 1e-9)))
            lines[j] = "| " + " | ".join(cells) + " |"
            changed += 1
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(json.dumps({"ok": True, "filledSprints": changed,
                      "sprints": max(1, math.ceil(cum / per_sprint - 1e-9))}, indent=2))
    return 0


# ---------- status ----------

def classify(snap_item):
    if snap_item is None:
        return "Unknown", "not in the snapshot"
    if snap_item.get("readError"):
        return "Unknown", f"read failed: {snap_item['readError']}"
    state = (snap_item.get("state") or "").lower()
    reason = (snap_item.get("stateReason") or "").lower()
    labels = [str(x).lower() for x in snap_item.get("labels") or []]
    impl = snap_item.get("implPr") or None
    spec = snap_item.get("specPr") or None
    impl_state = (impl or {}).get("state", "").lower()
    if state == "closed" and reason in ("not_planned", "not planned"):
        return "Dropped", "closed as not planned"
    if state == "closed":
        if impl and impl_state == "merged":
            return "Done", f"PR #{impl.get('number')} merged"
        return "Done (no PR)", "closed as completed, no merged implementation PR"
    if impl and impl_state == "open":
        if impl.get("isDraft"):
            return "Building", f"draft PR #{impl.get('number')}"
        if (impl.get("reviewDecision") or "").upper() == "APPROVED":
            return "Ready to merge", f"PR #{impl.get('number')} approved"
        return "In review", f"PR #{impl.get('number')} open"
    if "in-progress" in labels:
        return "Building", "in-progress label, no PR"
    if spec and (spec.get("state") or "").lower() in ("open", "merged"):
        return "Spec", f"spec PR #{spec.get('number')} {spec.get('state')}"
    return "Not started", "no PR"


# ---------- analysis ----------

def load_history(history_dir, today):
    points = []
    if not history_dir or not os.path.isdir(history_dir):
        return points
    for name in sorted(os.listdir(history_dir)):
        m = re.match(r"^(\d{4}-\d{2}-\d{2})\.json$", name)
        if not m or m.group(1) >= today.isoformat():
            continue
        try:
            with open(os.path.join(history_dir, name), encoding="utf-8") as f:
                data = json.load(f)
            points.append((dt.date.fromisoformat(m.group(1)), float(data["result"]["earnedHours"])))
        except (OSError, ValueError, KeyError, TypeError):
            continue
    return points


def ux_coverage(ux):
    if not ux or not ux.get("entries"):
        return None
    out = {"reference": ux.get("reference"), "method": ux.get("method"), "groups": {}, "missing": []}
    total_credit = 0.0
    total_n = 0
    for e in ux["entries"]:
        kind = e.get("kind", "screen")
        status = (e.get("status") or "missing").lower()
        if status not in UX_CREDIT:
            status = "missing"
        g = out["groups"].setdefault(kind, {"present": 0, "partial": 0, "missing": 0, "credit": 0.0, "n": 0})
        g[status] += 1
        g["credit"] += UX_CREDIT[status]
        g["n"] += 1
        total_credit += UX_CREDIT[status]
        total_n += 1
        if status != "present":
            out["missing"].append({"id": e.get("id"), "name": e.get("name"), "kind": kind, "status": status})
    for g in out["groups"].values():
        g["coveragePct"] = round(100.0 * g["credit"] / g["n"], 1)
        del g["credit"]
    out["coveragePct"] = round(100.0 * total_credit / total_n, 1)
    return out


def analyze(plan, snap, history_dir):
    today = parse_date(snap.get("today", ""), "snapshot today")
    by_issue = {}
    by_id = {}
    for s in snap.get("items") or []:
        if s.get("issue") is not None:
            by_issue[int(s["issue"])] = s
        if s.get("id"):
            by_id[str(s["id"])] = s
    rows = []
    planned_ids = set()
    for item in plan["items"]:
        planned_ids.add(item["id"])
        s = by_issue.get(item["issue"]) if item["issue"] is not None else None
        if s is None:
            s = by_id.get(item["id"])
        status, why = classify(s)
        credit = CREDIT[status]
        rows.append({
            "id": item["id"], "issue": item["issue"], "title": item["title"], "size": item["size"],
            "hours": item["hours"], "sprint": item["sprint"], "status": status, "reason": why,
            "earned": round(item["hours"] * credit, 2),
            "blocked": bool(s and any(str(x).lower() in ("blocked", "do-not-merge", "qa-failed")
                                      for x in s.get("labels") or [])),
        })
    planned_issues = {i["issue"] for i in plan["items"] if i["issue"] is not None}
    unplanned = [
        {"id": s.get("id"), "issue": s.get("issue"), "title": s.get("title")}
        for s in snap.get("items") or []
        if s.get("id") not in planned_ids and s.get("issue") not in planned_issues
    ]
    active = [r for r in rows if r["status"] != "Dropped"]
    total = sum(r["hours"] for r in active)
    earned = sum(r["earned"] for r in active)
    strict = sum(r["hours"] for r in active if r["status"] in ("Done", "Done (no PR)"))
    cap = daily_capacity(plan)
    elapsed = max(0, working_days_between(plan["start"], today))
    planned_value = min(total, elapsed * cap)
    planned_days = math.ceil(total / cap) if cap > 0 else 0
    planned_end = add_working_days(plan["start"], planned_days)

    if total == 0:
        verdict, spi = "unknown", None
    elif planned_value == 0:
        verdict, spi = "not started", None
    else:
        spi = earned / planned_value
        if spi >= SPI_ON_TRACK:
            verdict = "on track"
        elif spi >= SPI_AT_RISK:
            verdict = "at risk"
        else:
            verdict = "late"
    if total > 0 and earned >= total:
        verdict = "complete"

    history = load_history(history_dir, today)
    velocity, velocity_source = None, None
    trend = history[-(TREND_POINTS - 1):] if history else []
    if trend:
        d0, ev0 = trend[0]
        days = working_days_between(d0, today)
        if days > 0 and earned - ev0 > 0:
            velocity = (earned - ev0) / days
            velocity_source = f"trend since {d0.isoformat()} ({len(trend) + 1} points)"
    if velocity is None and elapsed > 0 and earned > 0:
        velocity = earned / elapsed
        velocity_source = f"average since start ({elapsed} working days)"
    remaining = max(0.0, total - earned)
    forecast_end, delay = None, None
    if remaining == 0 and total > 0:
        forecast_end, delay = today, working_days_between(planned_end, today)
    elif velocity:
        need = remaining / velocity
        if need <= MAX_FORECAST_DAYS:
            forecast_end = add_working_days(today, need)
            delay = working_days_between(planned_end, forecast_end)

    actuals = snap.get("actuals") or None
    cost = None
    if actuals and actuals.get("humanHours"):
        ah = float(actuals["humanHours"])
        cost = {"humanHours": ah, "cpi": round(earned / ah, 2) if ah > 0 else None}
        for k in ("agentHours", "cost", "currency"):
            if actuals.get(k) is not None:
                cost[k] = actuals[k]

    counts = {}
    for r in rows:
        counts[r["status"]] = counts.get(r["status"], 0) + 1

    result = {
        "today": today.isoformat(),
        "planType": plan["type"],
        "start": plan["start"].isoformat(),
        "plannedHours": round(total, 2),
        "plannedValueHours": round(planned_value, 2),
        "earnedHours": round(earned, 2),
        "doneHours": round(strict, 2),
        "progressPct": round(100.0 * earned / total, 1) if total else None,
        "donePct": round(100.0 * strict / total, 1) if total else None,
        "plannedPct": round(100.0 * planned_value / total, 1) if total else None,
        "spi": round(spi, 2) if spi is not None else None,
        "verdict": verdict,
        "plannedEnd": planned_end.isoformat(),
        "forecastEnd": forecast_end.isoformat() if forecast_end else None,
        "delayWorkingDays": delay,
        "velocityHoursPerDay": round(velocity, 2) if velocity else None,
        "velocitySource": velocity_source,
        "statusCounts": counts,
        "items": rows,
        "unplanned": unplanned,
        "cost": cost,
        "cezar": snap.get("cezar") or None,
        "ux": ux_coverage(snap.get("ux")),
        "coverage": snap.get("coverage") or [],
    }
    return result


def cmd_analyze(plan_path, snap_path, history_dir, save):
    header, items, *_ = read_plan(plan_path)
    plan, errors = normalize_plan(header, items)
    if errors:
        print(json.dumps({"ok": False, "errors": errors}, indent=2))
        return 1
    try:
        with open(snap_path, encoding="utf-8") as f:
            snap = json.load(f)
        result = analyze(plan, snap, history_dir)
    except (OSError, ValueError, PlanError) as e:
        print(json.dumps({"ok": False, "errors": [f"snapshot: {e}"]}, indent=2))
        return 1
    out = {"ok": True, "result": result}
    if save:
        if not history_dir:
            print(json.dumps({"ok": False, "errors": ["--save needs --history DIR"]}, indent=2))
            return 1
        os.makedirs(history_dir, exist_ok=True)
        path = os.path.join(history_dir, f"{result['today']}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"snapshot": snap, "result": result}, f, indent=2)
        out["saved"] = path
    print(json.dumps(out, indent=2))
    return 0


def main(argv):
    p = argparse.ArgumentParser(description="mk-benchmark calculations")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("schedule"); s.add_argument("plan")
    c = sub.add_parser("check"); c.add_argument("plan")
    a = sub.add_parser("analyze"); a.add_argument("plan"); a.add_argument("snapshot")
    a.add_argument("--history"); a.add_argument("--save", action="store_true")
    args = p.parse_args(argv)
    try:
        if args.cmd == "schedule":
            return cmd_schedule(args.plan)
        if args.cmd == "check":
            return cmd_check(args.plan)
        return cmd_analyze(args.plan, args.snapshot, args.history, args.save)
    except (OSError, PlanError) as e:
        print(json.dumps({"ok": False, "errors": [str(e)]}, indent=2))
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
