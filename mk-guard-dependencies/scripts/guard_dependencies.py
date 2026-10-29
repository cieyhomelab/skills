#!/usr/bin/env python3
"""Find blocking conflicts between issues in a tracker snapshot.

Run this script. Do not read it to do the analysis by hand.
It needs only the Python 3 standard library (Python 3.8 or later).

Commands:
  validate SNAPSHOT [--issue N]               Check the snapshot. Exit 2 if it has errors.
  analyze  SNAPSHOT [--backlog PATH]          Write the full analysis as JSON to stdout.
  gate     SNAPSHOT --issue N [--backlog PATH]
                                              Write the verdict lines for one issue.
  plan     SNAPSHOT --out CHANGES [--backlog PATH] [--sync-labels] [--notify]
                                              Write the planned tracker changes to a file.
  check-plan SNAPSHOT CHANGES                 Check the planned changes. Exit 2 if they have errors.
"""

import argparse
import contextlib
import fnmatch
import json
import re
import sys
from datetime import UTC, datetime

SKILL = "mk-guard-dependencies"  # the skill name in the comment marker
MARKER = "🤖 `" + SKILL + "` —"  # the shared comment marker of the collection
EXIT_INVALID = 2  # a different exit code than a Python crash (1), so callers can tell them apart

DEFAULT_STALE_HOURS = 24  # the stale window of the shared claim protocol
DEFAULT_SPECS_DIR = ".ai/specs"  # the default of paths.specs in the pipeline config
DEFAULT_LABELS = {  # the default label taxonomy of the pipeline config
    "blocked": "blocked",
    "inProgress": "in-progress",
    "doNotMerge": "do-not-merge",
    "hold": [],
    "priority": ["priority-low", "priority-medium", "priority-high", "priority-extreme"],
}
# Lock files and checksum files change in almost each PR. They tell nothing about the design.
DEFAULT_IGNORE_PATHS = ["*.lock", "*-lock.json", "*-lock.yaml", "*.sum"]

# A backlog id: E01, E01-S02, or E01-S02-T03, with any letter prefix of 1 to 6 letters.
ID_RE = re.compile(r"\b[A-Za-z]{1,6}\d{2,}(?:-[ST]\d{2,}){0,2}\b")
NUM_RE = re.compile(  # an issue number, for example #12
    r"#(\d+)"
)
# The body lines that the backlog skill writes, with or without bold and list marks.
FIELD_RE = re.compile(
    r"^[ \t]*(?:[-*][ \t]+)?(?:\*\*)?(Depends on|Backlog source|Backlog id|Spec)(?:\*\*)?[ \t]*:[ "
    r"\t]*(.*)$",
    re.I | re.M,
)
EMPTY_WORDS = {  # words in a Depends on line that mean "no dependency"
    "none",
    "n/a",
    "na",
    "and",
    "or",
    "—",
    "–",  # noqa: RUF001 - an en dash also means "no dependency"
    "-",
}
CLOSE_RE = re.compile(  # the closing keywords of the tracker
    r"\b(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s*:?\s+#(\d+)", re.I
)
REFS_RE = re.compile(  # a reference without a close, for example a spec PR
    r"\brefs?\s*:?\s+#(\d+)", re.I
)
# The release and claim comments of the shared claim protocol.
RELEASE_RE = re.compile(
    r"^\s*🤖.*\b(lock released|released|run complete|aborted|handback|hand(?:ed)? back)\b",
    re.I | re.S,
)
CLAIM_RE = re.compile(
    r"^\s*🤖.*\b(claim\w*|taking over|take-over|handed off|adopting|override)\b", re.I | re.S
)
SECRET_RE = re.compile(  # token formats of common services; a comment must not contain them
    r"(ghp_[A-Za-z0-9]{20,}|github_pat_\w{20,}|glpat-[\w-]{20,}|sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16})"
)

SEVERITY_ORDER = {  # the report shows stop findings first
    "stop": 0,
    "warn": 1,
    "label": 2,
    "note": 3,
}


# ---------- input normalization ----------


def fail(errors):
    for e in errors:
        print("ERROR: " + e, file=sys.stderr)
    sys.exit(EXIT_INVALID)


def parse_time(value):
    if not value:
        return None
    try:
        t = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if t.tzinfo is None:
        t = t.replace(tzinfo=UTC)
    return t


def login_of(x):
    if isinstance(x, dict):
        return x.get("login") or x.get("name") or ""
    return str(x)


def label_of(x):
    if isinstance(x, dict):
        return x.get("name", "")
    return str(x)


def lower_or_none(x):
    return str(x).lower() if x not in (None, "") else None


def norm_comment(c):
    return {
        "id": c.get("id") or c.get("databaseId") or c.get("url"),
        "author": login_of(c.get("author") or c.get("user") or ""),
        "createdAt": c.get("createdAt") or c.get("created_at"),
        "body": c.get("body") or "",
    }


def norm_issue(i):
    out = dict(i)
    out["number"] = int(i["number"]) if str(i.get("number", "")).isdigit() else i.get("number")
    out["state"] = lower_or_none(i.get("state"))
    out["stateReason"] = lower_or_none(i.get("stateReason") or i.get("state_reason"))
    out["labels"] = [label_of(x) for x in i.get("labels") or []]
    out["assignees"] = [login_of(x) for x in i.get("assignees") or []]
    out["body"] = i.get("body") or ""
    if "comments" in i and i["comments"] is not None:
        out["comments"] = [norm_comment(c) for c in i["comments"]]
    return out


def norm_pr(p):
    out = dict(p)
    out["number"] = int(p["number"]) if str(p.get("number", "")).isdigit() else p.get("number")
    state = lower_or_none(p.get("state"))
    if p.get("mergedAt") and state == "closed":
        state = "merged"
    out["state"] = state
    out["isDraft"] = bool(p.get("isDraft"))
    out["author"] = login_of(p.get("author") or "")
    out["mergeable"] = (p.get("mergeable") or "UNKNOWN").upper()
    out["body"] = p.get("body") or ""
    files = p.get("files")
    out["files"] = (
        None if files is None else [f.get("path") if isinstance(f, dict) else str(f) for f in files]
    )
    closing = p.get("closingIssuesReferences") or p.get("closes") or []
    out["closes"] = sorted(
        {int(x.get("number") if isinstance(x, dict) else x) for x in closing}
        | {int(n) for n in CLOSE_RE.findall(out["body"])}
    )
    out["refs"] = sorted({int(n) for n in REFS_RE.findall(out["body"])} - set(out["closes"]))
    return out


def load_snapshot(path):
    try:
        with open(path, encoding="utf-8") as fh:
            raw = json.load(fh)
    except FileNotFoundError:
        fail([f"file not found: {path}"])
    except json.JSONDecodeError as e:
        fail([f"{path} is not valid JSON: line {e.lineno}, column {e.colno}: {e.msg}"])
    if not isinstance(raw, dict):
        fail([f"{path} must contain one JSON object with the fields readAt, issues, prs"])
    snap = dict(raw)
    snap["issues"] = [norm_issue(i) for i in raw.get("issues") or [] if isinstance(i, dict)]
    snap["prs"] = [norm_pr(p) for p in raw.get("prs") or [] if isinstance(p, dict)]
    labels = dict(DEFAULT_LABELS)
    labels.update(raw.get("labelNames") or {})
    snap["labelNames"] = labels
    snap["labelsEnabled"] = bool(raw.get("labelsEnabled", True))
    snap["staleHours"] = float(raw.get("staleHours") or DEFAULT_STALE_HOURS)
    snap["specsDir"] = (raw.get("specsDir") or DEFAULT_SPECS_DIR).rstrip("/")
    snap["ignorePaths"] = DEFAULT_IGNORE_PATHS + list(raw.get("ignorePaths") or [])
    snap["automationUsers"] = set(raw.get("automationUsers") or [])
    snap["footprints"] = {
        int(k): v for k, v in (raw.get("footprints") or {}).items() if str(k).isdigit()
    }
    return raw, snap


# ---------- parsing ----------


def body_fields(body):
    fields = {}
    for m in FIELD_RE.finditer(body or ""):
        key = m.group(1).lower()
        fields.setdefault(key, m.group(2).strip())
    return fields


def parse_depends(text):
    """Return (numbers, ids, leftovers) from a Depends on value."""
    if text is None:
        return [], [], []
    numbers = [int(n) for n in NUM_RE.findall(text)]
    ids = ID_RE.findall(text)
    rest = ID_RE.sub(" ", NUM_RE.sub(" ", text))
    rest = re.sub(r"[()\[\],;.`*]", " ", rest)
    leftovers = [w for w in rest.split() if w.lower() not in EMPTY_WORDS]
    return numbers, ids, leftovers


def parse_backlog(path):
    """Return rows in file order: {source, id, issue, depends}."""
    if not path:
        return []
    try:
        with open(path, encoding="utf-8") as fh:
            lines = fh.read().splitlines()
    except FileNotFoundError:
        return []
    rows, source, header = [], None, None
    for line in lines:
        if line.startswith("## "):
            source, header = line[3:].strip(), None
            continue
        m = re.match(r"^\s*Backlog source:\s*(\S+)", line)
        if m:
            source = m.group(1)
            continue
        if not line.strip().startswith("|"):
            header = None if not line.strip() else header
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if header is None:
            header = [c.lower() for c in cells]
            continue
        if set("".join(cells)) <= set("-: "):
            continue
        row = dict(zip(header, cells, strict=False))
        issue = NUM_RE.search(row.get("issue", ""))
        rows.append(
            {
                "source": source,
                "id": row.get("id", "").strip(),
                "issue": int(issue.group(1)) if issue else None,
                "depends": row.get("depends on"),
            }
        )
    return rows


# ---------- graph ----------


class Graph:
    def __init__(self, snap, backlog_rows):
        self.snap = snap
        self.issues = {i["number"]: i for i in snap["issues"] if isinstance(i.get("number"), int)}
        self.rows = backlog_rows
        self.order = {}
        for idx, r in enumerate(backlog_rows):
            if r["issue"] is not None:
                self.order.setdefault(r["issue"], idx)
        for _n, i in self.issues.items():
            f = body_fields(i["body"])
            i["_fields"] = f
            i["_source"] = f.get("backlog source") or None
            i["_id"] = f.get("backlog id") or None
        self.blockers = {n: set() for n in self.issues}
        self.problems = []  # (dependent, kind, token)
        self.drift = []  # (dependent, detail)
        self.from_map = set()
        self._build_edges()

    def resolve_id(self, token, source):
        cands = [
            n
            for n, i in self.issues.items()
            if i["_id"] == token and (source is None or i["_source"] in (None, source))
        ]
        if len(cands) == 1:
            return cands[0], None
        if len(cands) > 1:
            return None, "ambiguous"
        rows = [
            r
            for r in self.rows
            if r["id"] == token
            and r["issue"] is not None
            and (source is None or r["source"] in (None, source))
        ]
        nums = {r["issue"] for r in rows}
        if len(nums) == 1:
            return nums.pop(), None
        return None, ("ambiguous" if len(nums) > 1 else "missing")

    def _edges_from_text(self, dependent, text, source):
        numbers, ids, leftovers = parse_depends(text)
        found = set(numbers)
        for token in ids:
            n, problem = self.resolve_id(token, source)
            if problem:
                self.problems.append((dependent, problem, token))
            else:
                found.add(n)
        for word in leftovers:
            self.problems.append((dependent, "unparseable", word))
        found.discard(dependent)
        return found

    def _build_edges(self):
        row_by_issue = {r["issue"]: r for r in self.rows if r["issue"] is not None}
        for n, i in self.issues.items():
            if i.get("readError"):
                continue
            source = i["_source"] or (row_by_issue.get(n) or {}).get("source")
            body_text = i["_fields"].get("depends on")
            row = row_by_issue.get(n)
            mark = len(self.problems)
            body_edges = (
                self._edges_from_text(n, body_text, source) if body_text is not None else None
            )
            row_edges = None
            if row is not None and row.get("depends") is not None:
                saved = list(self.problems)
                row_edges = self._edges_from_text(n, row["depends"], row["source"])
                if body_edges is not None:
                    self.problems = saved  # the body decides; map problems are not repeated
            if body_edges is None and row_edges is not None:
                self.blockers[n] |= row_edges
                self.from_map.add(n)
            elif body_edges is not None:
                self.blockers[n] |= body_edges
                if row_edges is not None and row_edges != body_edges:
                    self.drift.append(
                        (
                            n,
                            f"backlog.md lists {fmt(row_edges)}, the issue body lists "
                            f"{fmt(body_edges)}",
                        )
                    )
            del mark
        for e in self.snap.get("nativeEdges") or []:
            b, d = int(e["blocker"]), int(e["dependent"])
            if d in self.blockers and b not in self.blockers[d]:
                self.blockers[d].add(b)
                self.drift.append((d, f"the tracker relation #{b} is not in the Depends on line"))

    def dependents(self, n):
        return [d for d, bs in self.blockers.items() if n in bs]


def fmt(nums):
    return ", ".join(f"#{n}" for n in sorted(nums)) if nums else "none"


# ---------- states ----------


def linked_prs(snap):
    by_issue = {}
    for p in snap["prs"]:
        for n in p["closes"]:
            by_issue.setdefault(n, []).append(("close", p))
        for n in p["refs"]:
            by_issue.setdefault(n, []).append(("refs", p))
    return by_issue


def is_spec_pr(p, specs_dir):
    files = p["files"] or []
    return not p["closes"] and any(f.startswith(specs_dir + "/") for f in files)


def claim_authors(comments):
    state, last = {}, {}
    for c in sorted(
        comments or [],
        key=lambda c: parse_time(c["createdAt"]) or datetime.min.replace(tzinfo=UTC),
    ):
        body = c["body"]
        if body.lstrip().startswith(MARKER):
            continue
        if RELEASE_RE.search(body):
            state[c["author"]] = False
        elif CLAIM_RE.search(body):
            state[c["author"]] = True
            last[c["author"]] = parse_time(c["createdAt"])
    return {a: last.get(a) for a, on in state.items() if on}


def classify(graph):
    snap = graph.snap
    read_at = parse_time(snap.get("readAt")) or datetime.now(UTC)
    names = snap["labelNames"]
    prs = linked_prs(snap)
    states = {}
    for n, i in graph.issues.items():
        s = {
            "number": n,
            "id": i["_id"],
            "source": i["_source"],
            "title": i.get("title", ""),
            "labels": i["labels"],
            "owners": [],
            "stale": False,
            "openPrs": [],
            "implPrs": [],
            "notes": [],
        }
        if i.get("readError"):
            s["state"] = "Unknown"
            s["notes"].append(f"read failed: {i['readError']}")
            states[n] = s
            continue
        links = prs.get(n, [])
        merged = [p for kind, p in links if kind == "close" and p["state"] == "merged"]
        open_links = [p for kind, p in links if p["state"] == "open"]
        s["openPrs"] = [p["number"] for p in open_links]
        s["implPrs"] = [
            p["number"]
            for kind, p in links
            if kind == "close" and p["state"] == "open" and not is_spec_pr(p, snap["specsDir"])
        ]
        if i["state"] == "closed":
            if i["stateReason"] in ("not_planned", "duplicate") or (
                i["stateReason"] not in ("completed", None) and not merged
            ):
                s["state"] = "Dropped"
            else:
                s["state"] = "Resolved"
            states[n] = s
            continue
        if merged:
            s["state"] = "Resolved"
            s["notes"].append(f"PR #{merged[0]['number']} merged, issue not closed")
            states[n] = s
            continue
        claims = claim_authors(i.get("comments"))
        owners = (
            set(i["assignees"]) | set(claims) | {p["author"] for p in open_links if p["author"]}
        )
        if len(owners) > 1:
            owners -= snap["automationUsers"] or set()
            owners = owners or (set(i["assignees"]) | set(claims))
        in_progress = snap["labelsEnabled"] and names["inProgress"] in i["labels"]
        s["owners"] = sorted(owners)
        if owners or in_progress or open_links:
            s["state"] = "In flight"
            times = [t for t in claims.values() if t]
            times += [
                parse_time(c["createdAt"]) for c in i.get("comments") or [] if c["author"] in owners
            ]
            times += [parse_time(p.get("updatedAt")) for p in open_links]
            times = [t for t in times if t]
            last = max(times) if times else parse_time(i.get("updatedAt"))
            if last:
                age = (read_at - last).total_seconds() / 3600
                s["stale"] = age > snap["staleHours"]
                s["idleHours"] = round(age)
        else:
            s["state"] = "Free"
        states[n] = s
    return states


# ---------- findings ----------


def cycles(graph):
    index, low, stack, on, out = {}, {}, [], set(), []
    counter = [0]

    def visit(v):
        index[v] = low[v] = counter[0]
        counter[0] += 1
        stack.append(v)
        on.add(v)
        for w in graph.blockers.get(v, ()):
            if w not in graph.blockers:
                continue
            if w not in index:
                visit(w)
                low[v] = min(low[v], low[w])
            elif w in on:
                low[v] = min(low[v], index[w])
        if low[v] == index[v]:
            comp = []
            while True:
                w = stack.pop()
                on.discard(w)
                comp.append(w)
                if w == v:
                    break
            if len(comp) > 1:
                out.append(sorted(comp))

    sys.setrecursionlimit(10000)
    for v in sorted(graph.blockers):
        if v not in index:
            visit(v)
    return out


def ignored(path, patterns):
    name = path.rsplit("/", 1)[-1]
    return any(fnmatch.fnmatch(name, p) or fnmatch.fnmatch(path, p) for p in patterns)


def covers(entry, path):
    entry, path = entry.strip("/"), path.strip("/")
    if entry == path or path.startswith(entry + "/") or entry.startswith(path + "/"):
        return True
    if "/" not in entry and "." not in entry:
        return ("/" + entry + "/") in ("/" + path + "/")
    return False


def overlap(a_paths, b_paths, patterns):
    hits = []
    for a in a_paths:
        if ignored(a, patterns):
            continue
        for b in b_paths:
            if not ignored(b, patterns) and covers(a, b):
                hits.append(b if len(b) >= len(a) else a)
    return sorted(set(hits))


def finding(rule, severity, subject, related, owners, evidence, nxt):
    return {
        "rule": rule,
        "severity": severity,
        "subject": subject,
        "related": sorted(set(related)),
        "owners": sorted(set(owners)),
        "evidence": evidence,
        "next": nxt,
    }


def analyze(snap, backlog_rows, current_user=None):
    g = Graph(snap, backlog_rows)
    st = classify(g)
    names = snap["labelNames"]
    out = []

    def source_of(n):
        return (st.get(n) or {}).get("source") or "<source>"

    in_cycle = set()
    for comp in cycles(g):
        in_cycle |= set(comp)
        path = " → ".join(f"#{n}" for n in comp)
        for n in comp:
            out.append(
                finding(
                    "C1",
                    "stop",
                    n,
                    comp,
                    [],
                    f"cycle {path}",
                    "remove one edge of the cycle in a Depends on line, then run om-backlog "
                    f"{source_of(n)}",
                )
            )

    for d, bs in g.blockers.items():
        sd = st[d]
        for b in sorted(bs):
            sb = st.get(b)
            if sb is None or sb["state"] in ("Dropped",):
                kind = (
                    "missing from the tracker" if sb is None else "dropped (closed as not planned)"
                )
                sev = "stop" if sd["state"] == "In flight" else "warn"
                out.append(
                    finding(
                        "C5",
                        sev,
                        d,
                        [b],
                        sd["owners"],
                        f"blocker #{b} is {kind}",
                        "decide if the dependency still applies, then correct the Depends on line",
                    )
                )
                continue
            if sd["state"] != "In flight" or sb["state"] in ("Resolved", "Unknown"):
                continue
            if sb["state"] == "Free":
                out.append(
                    finding(
                        "C2a",
                        "stop",
                        d,
                        [b],
                        sd["owners"],
                        f"#{d} started while blocker #{b} is free (no owner)",
                        f"take the blocker first: om-auto-fix-issue {b}; keep the work on #{d} in "
                        "draft until then",
                    )
                )
            elif sb["state"] == "In flight":
                same = set(sd["owners"]) & set(sb["owners"])
                sev = "note" if same and set(sd["owners"]) == set(sb["owners"]) else "warn"
                out.append(
                    finding(
                        "C2b",
                        sev,
                        d,
                        [b],
                        sd["owners"] + sb["owners"],
                        f"#{d} started while blocker #{b} is also in flight",
                        f"agree the order: #{d} waits until #{b} merges, then rebases",
                    )
                )
    for d, kind, token in g.problems:
        sev = "stop" if st[d]["state"] == "In flight" else "warn"
        out.append(
            finding(
                "C5",
                sev,
                d,
                [],
                st[d]["owners"],
                f"Depends on entry '{token}' is {kind}",
                "decide if the dependency still applies, then correct the Depends on line",
            )
        )

    for n, s in st.items():
        if s["state"] != "In flight":
            continue
        closing = [p for p in snap["prs"] if n in p["closes"] and p["state"] == "open"]
        if len(s["owners"]) > 1 or len({p["number"] for p in closing}) > 1:
            out.append(
                finding(
                    "C3",
                    "stop",
                    n,
                    [p["number"] for p in closing],
                    s["owners"],
                    f"#{n} has more than one owner or more than one open closing PR",
                    f"the owners agree who keeps #{n}; the other owner hands it back",
                )
            )
        waiting = [
            d for d in g.dependents(n) if st.get(d, {}).get("state") not in ("Resolved", "Dropped")
        ]
        if s["stale"] and waiting:
            pr = s["implPrs"][0] if s["implPrs"] else None
            nxt = (
                f"the owner resumes: om-auto-continue-pr {pr}"
                if pr
                else f"the owner resumes or releases #{n}"
            )
            out.append(
                finding(
                    "C4",
                    "warn",
                    n,
                    waiting,
                    s["owners"],
                    f"claim idle for {s.get('idleHours')} h and holds {len(waiting)} waiting "
                    "issue(s)",
                    nxt + f"; a takeover only with om-auto-fix-issue {n} --force",
                )
            )

    impl = [
        p
        for p in snap["prs"]
        if p["state"] == "open" and p["closes"] and not is_spec_pr(p, snap["specsDir"])
    ]
    for p in impl:
        if p["mergeable"] == "CONFLICTING":
            subj = p["closes"][0]
            out.append(
                finding(
                    "C6",
                    "stop",
                    subj,
                    [p["number"]],
                    [p["author"]],
                    f"PR #{p['number']} has merge conflicts",
                    f"rebase PR #{p['number']} on the base branch",
                )
            )
    for x in range(len(impl)):
        for y in range(x + 1, len(impl)):
            a, b = impl[x], impl[y]
            if set(a["closes"]) & set(b["closes"]) or a["files"] is None or b["files"] is None:
                continue
            shared = overlap(a["files"], b["files"], snap["ignorePaths"])
            if not shared:
                continue
            first, second = sorted(
                [a, b], key=lambda p: min(g.order.get(n, 10**6 + n) for n in p["closes"])
            )
            sev = "note" if a["author"] == b["author"] else "warn"
            shown = ", ".join(shared[:5]) + (
                f" (+{len(shared) - 5} more)" if len(shared) > 5 else ""
            )
            out.append(
                finding(
                    "C6",
                    sev,
                    second["closes"][0],
                    [first["number"], second["number"]],
                    [a["author"], b["author"]],
                    f"PR #{a['number']} and PR #{b['number']} both change {shown}",
                    f"merge PR #{first['number']} first; PR #{second['number']} rebases",
                )
            )

    hold = set(names["hold"]) | {names["blocked"], names["doNotMerge"]}
    stop_subjects = {
        f["subject"] for f in out if f["severity"] == "stop" or f["rule"] in ("C1", "C5")
    }

    def blockers_resolved(n):
        return all(st.get(b, {}).get("state") == "Resolved" for b in g.blockers.get(n, ()))

    candidates = [
        n
        for n, s in st.items()
        if s["state"] == "Free"
        and blockers_resolved(n)
        and n not in in_cycle
        and not (snap["labelsEnabled"] and hold & set(s["labels"]))
        and n not in stop_subjects
    ]

    fps = snap["footprints"]
    no_footprint = 0
    eligible = [
        n for n, s in st.items() if s["state"] == "In flight" and not s["implPrs"]
    ] + candidates
    for n in eligible:
        fp = fps.get(n)
        if not fp:
            no_footprint += 1
            continue
        paths = fp.get("paths") if isinstance(fp, dict) else fp
        mine = set(st[n]["owners"])
        for p in impl:
            if n in p["closes"] or p["files"] is None:
                continue
            shared = overlap(paths, p["files"], snap["ignorePaths"])
            if shared:
                sev = "note" if mine and mine == {p["author"]} else "warn"
                out.append(
                    finding(
                        "C6b",
                        sev,
                        n,
                        [p["number"]],
                        [*list(mine), p["author"]],
                        f"#{n} is expected to change {', '.join(shared[:5])}, which PR "
                        f"#{p['number']} changes",
                        f"start #{n} on the branch of PR #{p['number']}, or wait until it merges",
                    )
                )
        for m in eligible:
            if (
                m <= n
                or m not in fps
                or st[m]["state"] != "In flight"
                or st[n]["state"] != "In flight"
            ):
                continue
            other = fps[m].get("paths") if isinstance(fps[m], dict) else fps[m]
            shared = overlap(paths, other, snap["ignorePaths"])
            if shared and set(st[m]["owners"]) != mine:
                out.append(
                    finding(
                        "C6b",
                        "warn",
                        m,
                        [n],
                        list(mine) + st[m]["owners"],
                        f"#{n} and #{m} are both expected to change {', '.join(shared[:5])}",
                        "the owners agree who goes first",
                    )
                )

    if snap["labelsEnabled"]:
        blocked = names["blocked"]
        for n, s in st.items():
            if s["state"] in ("Resolved", "Dropped", "Unknown"):
                continue
            issue = g.issues[n]
            has_marker = any(
                c["body"].lstrip().startswith(MARKER)
                and "label" in c["body"].split("\n", 1)[0].lower()
                for c in issue.get("comments") or []
            )
            open_blockers = [
                b for b in g.blockers.get(n, ()) if st.get(b, {}).get("state") != "Resolved"
            ]
            others = set(s["owners"]) - ({current_user} if current_user else set())
            if blocked in s["labels"] and not open_blockers and (g.blockers.get(n) or has_marker):
                f = finding(
                    "C7",
                    "label",
                    n,
                    sorted(g.blockers.get(n, ())),
                    [],
                    f"#{n} carries `{blocked}`, but all of its blockers are resolved",
                    "run this skill with --sync-labels",
                )
                f["change"], f["addedByGuard"] = "remove", has_marker
                out.append(f)
            elif blocked not in s["labels"] and open_blockers and not others:
                f = finding(
                    "C7",
                    "label",
                    n,
                    open_blockers,
                    [],
                    f"#{n} waits for {fmt(open_blockers)} but does not carry `{blocked}`",
                    "run this skill with --sync-labels",
                )
                f["change"], f["addedByGuard"] = "add", False
                out.append(f)

    for d, detail in g.drift:
        out.append(
            finding(
                "C8",
                "label",
                d,
                [],
                [],
                detail,
                f"run om-backlog {source_of(d)} to correct the map; the issue body decided this "
                "result",
            )
        )

    out.sort(
        key=lambda f: (
            SEVERITY_ORDER[f["severity"]],
            g.order.get(f["subject"], 10**6 + f["subject"]),
            f["rule"],
        )
    )

    pending = {n for n, s in st.items() if s["state"] not in ("Resolved", "Dropped")}

    def unlocks(n):
        seen, todo = set(), [n]
        while todo:
            for d in g.dependents(todo.pop()):
                if d in pending and d not in seen:
                    seen.add(d)
                    todo.append(d)
        return len(seen)

    prio = names["priority"]

    def prio_rank(n):
        ranks = [prio.index(lbl) for lbl in st[n]["labels"] if lbl in prio]
        return max(ranks) if ranks else -1

    warn_subjects = {f["subject"]: f["rule"] for f in out if f["severity"] == "warn"}
    safe = sorted(candidates, key=lambda n: (-prio_rank(n), g.order.get(n, 10**6 + n), -unlocks(n)))
    safe_list = [
        {
            "issue": n,
            "id": st[n]["id"],
            "title": st[n]["title"],
            "unlocks": unlocks(n),
            "warning": warn_subjects.get(n),
            "next": f"om-auto-fix-issue {n}",
        }
        for n in safe
    ]

    memo = {}

    def longest(n, trail):
        if n in memo:
            return memo[n]
        best = [n]
        for d in g.dependents(n):
            if d in pending and d not in in_cycle and d not in trail:
                cand = [n, *longest(d, trail | {d})]
                if len(cand) > len(best):
                    best = cand
        memo[n] = best
        return best

    critical = []
    for n in sorted(pending - in_cycle, key=lambda n: g.order.get(n, 10**6 + n)):
        if any(b in pending for b in g.blockers.get(n, ())):
            continue
        path = longest(n, {n})
        if len(path) > len(critical):
            critical = path

    coverage = []
    if "nativeEdges" not in snap:
        coverage.append("native tracker relations were not read")
    if not snap["labelsEnabled"]:
        coverage.append(
            "labels are disabled: claims use assignees and comments only; label drift is not "
            "checked"
        )
    if no_footprint:
        coverage.append(
            f"{no_footprint} issue(s) have no footprint, so predicted overlap (C6b) was not "
            "checked for them"
        )
    unknown = [n for n, s in st.items() if s["state"] == "Unknown"]
    if unknown:
        coverage.append(f"state unknown for {fmt(unknown)}")
    if g.from_map:
        coverage.append(
            f"Depends on taken from backlog.md for {fmt(g.from_map)} (no line in the issue body)"
        )

    first_stop = next((f for f in out if f["severity"] == "stop"), None)
    nxt = first_stop["next"] if first_stop else (safe_list[0]["next"] if safe_list else "none")
    m = re.search(r"(om-[a-z-]+(?: [^\s;]+)*)", nxt)
    nxt_line = m.group(1) if m and nxt != "none" else "none"

    counts = {k: sum(1 for f in out if f["severity"] == k) for k in SEVERITY_ORDER}
    return {
        "readAt": snap.get("readAt"),
        "counts": {
            "stop": counts["stop"],
            "warn": counts["warn"],
            "label": counts["label"],
            "note": counts["note"],
            "safe": len(safe_list),
            "waiting": sum(
                1 for n in pending if st[n]["state"] == "Free" and not blockers_resolved(n)
            ),
        },
        "issues": [
            dict(
                st[n],
                blockedBy=sorted(g.blockers.get(n, ())),
                blocks=sorted(g.dependents(n)),
                findings=[f["rule"] for f in out if f["subject"] == n],
            )
            for n in sorted(st, key=lambda n: g.order.get(n, 10**6 + n))
        ],
        "findings": out,
        "safeToStart": safe_list,
        "criticalPath": critical,
        "coverage": coverage,
        "next": nxt_line,
        "_graph": g,
        "_states": st,
    }


# ---------- gate ----------


def gate(snap, rows, target, current_user):
    res = analyze(snap, rows, current_user)
    g, st = res["_graph"], res["_states"]
    s = st.get(target)
    if s is None:
        return "conflict", [], "none", f"#{target} is not in the snapshot"
    if s["state"] == "Unknown":
        return "conflict", [], "none", f"#{target} could not be read ({'; '.join(s['notes'])})"
    if s["state"] in ("Resolved", "Dropped"):
        return (
            "conflict",
            [],
            "none",
            f"#{target} is already {s['state'].lower()}; there is nothing to start",
        )
    others = [o for o in s["owners"] if o != current_user]
    if others:
        return (
            "conflict",
            [],
            "none",
            f"#{target} is claimed by {', '.join('@' + o for o in others)}",
        )
    order, seen, todo = [], set(), [target]
    while todo:
        n = todo.pop(0)
        for b in sorted(g.blockers.get(n, ())):
            if b not in seen:
                seen.add(b)
                order.append(b)
                todo.append(b)
    open_chain = [b for b in order if st.get(b, {}).get("state") != "Resolved"]
    own = [f for f in res["findings"] if f["subject"] == target]
    bad = [f for f in own if f["rule"] in ("C1", "C3", "C5")]
    bad += [f for f in res["findings"] if f["rule"] in ("C1", "C5") and f["subject"] in seen]
    unread = [b for b in order if b not in st or st[b]["state"] in ("Unknown", "Dropped")]
    if bad or unread:
        reason = (
            bad[0]["evidence"]
            if bad
            else f"blocker {fmt(unread)} is missing, dropped, or unreadable"
        )
        return "conflict", open_chain, "none", reason
    names = snap["labelNames"]
    hold = set(names["hold"]) | {names["blocked"], names["doNotMerge"]}
    labels = hold & set(s["labels"]) if snap["labelsEnabled"] else set()
    if open_chain or labels:
        nxt = "none"
        free = [
            b
            for b in open_chain
            if st[b]["state"] == "Free"
            and all(st.get(x, {}).get("state") == "Resolved" for x in g.blockers.get(b, ()))
        ]
        stale = [
            b
            for b in open_chain
            if st[b]["state"] == "In flight" and st[b]["stale"] and st[b]["implPrs"]
        ]
        if free:
            nxt = f"om-auto-fix-issue {free[0]}"
        elif stale:
            nxt = f"om-auto-continue-pr {st[stale[0]]['implPrs'][0]}"
        parts = [
            f"#{b} is {st[b]['state'].lower()}"
            + (f" (@{', @'.join(st[b]['owners'])})" if st[b]["owners"] else "")
            for b in open_chain
        ]
        if labels:
            parts.append("the issue carries " + ", ".join(f"`{lbl}`" for lbl in sorted(labels)))
        return "wait", open_chain, nxt, "; ".join(parts)
    return (
        "clear",
        [],
        f"om-auto-fix-issue {target}",
        "all blockers are resolved and nobody else works on the issue",
    )


# ---------- write-back ----------


def plan(snap, rows, current_user, sync, notify):
    res = analyze(snap, rows, current_user)
    st, g = res["_states"], res["_graph"]
    names = snap["labelNames"]
    per_issue, changes, skipped = {}, [], []
    if sync and snap["labelsEnabled"]:
        for f in res["findings"]:
            if f["rule"] != "C7":
                continue
            n = f["subject"]
            if f["change"] == "remove" and not f["addedByGuard"]:
                skipped.append(
                    {"issue": n, "reason": f"`{names['blocked']}` was added by hand; not changed"}
                )
                continue
            op = "add-label" if f["change"] == "add" else "remove-label"
            changes.append(
                {"issue": n, "op": op, "label": names["blocked"], "reason": f["evidence"]}
            )
            line = (
                f"🏷️ label `{names['blocked']}` added: waits for {fmt(f['related'])}."
                if op == "add-label"
                else f"🏷️ label `{names['blocked']}` removed: {fmt(f['related'])} are resolved."
            )
            per_issue.setdefault(n, []).append(line)
    stop = [f for f in res["findings"] if f["severity"] == "stop"] if notify else []
    for f in stop:
        if st.get(f["subject"], {}).get("state") == "Unknown":
            continue
        owners = (" Owner: " + ", ".join("@" + o for o in f["owners"]) + ".") if f["owners"] else ""
        per_issue.setdefault(f["subject"], []).append(
            f"⛔ {f['rule']}: {f['evidence']}.{owners} Next: {f['next']}."
        )
    for n, i in g.issues.items():
        existing = [
            c
            for c in i.get("comments") or []
            if c["body"].lstrip().startswith(MARKER)
            and (not current_user or c["author"] == current_user)
        ]
        lines = per_issue.get(n)
        if lines:
            head = "label" if all(line.startswith("🏷️") for line in lines) else "conflicts"
            body = (
                f"{MARKER} {head}\n"
                + "\n".join("- " + line for line in lines)
                + f"\n\nChecked: {snap.get('readAt')}. This comment is updated on every run."
            )
        elif existing and notify and "✅ resolved" not in existing[-1]["body"].split("\n", 1)[0]:
            body = f"{MARKER} ✅ resolved\n\nNo blocking conflict at {snap.get('readAt')}."
        else:
            continue
        if existing:
            if existing[-1]["body"].strip() == body.strip():
                continue
            changes.append(
                {"issue": n, "op": "update-comment", "commentId": existing[-1]["id"], "body": body}
            )
        else:
            changes.append({"issue": n, "op": "create-comment", "body": body})
    return {"skill": SKILL, "readAt": snap.get("readAt"), "changes": changes, "skipped": skipped}


def check_plan(snap, plan_doc, current_user):
    errors = []
    issues = {i["number"]: i for i in snap["issues"]}
    st = classify(Graph(snap, []))
    names = snap["labelNames"]
    comment_ops = {}
    for k, c in enumerate(plan_doc.get("changes") or []):
        where = f"change {k} (issue #{c.get('issue')})"
        n, op = c.get("issue"), c.get("op")
        if n not in issues:
            errors.append(f"{where}: the issue is not in the snapshot")
            continue
        if st[n]["state"] == "Unknown":
            errors.append(f"{where}: the issue state is unknown; do not write to it")
        if op in ("add-label", "remove-label"):
            if not snap["labelsEnabled"]:
                errors.append(f"{where}: labels are disabled in the config")
            if c.get("label") != names["blocked"]:
                errors.append(
                    f"{where}: only the label `{names['blocked']}` can change, not "
                    f"`{c.get('label')}`"
                )
            others = set(st[n]["owners"]) - ({current_user} if current_user else set())
            if others:
                errors.append(
                    f"{where}: the issue is claimed by "
                    f"{', '.join('@' + o for o in sorted(others))}; do not change its labels"
                )
            if op == "remove-label" and not any(
                x["body"].lstrip().startswith(MARKER) for x in issues[n].get("comments") or []
            ):
                errors.append(
                    f"{where}: no {SKILL} comment exists, so a person added the label; do not "
                    "remove it"
                )
        elif op in ("create-comment", "update-comment"):
            comment_ops[n] = comment_ops.get(n, 0) + 1
            if not str(c.get("body", "")).startswith(MARKER):
                errors.append(f"{where}: the comment must start with the marker {MARKER}")
            if op == "update-comment" and not c.get("commentId"):
                errors.append(f"{where}: update-comment needs commentId")
            if SECRET_RE.search(str(c.get("body", ""))):
                errors.append(
                    f"{where}: the comment contains a string that looks like a credential"
                )
        else:
            errors.append(
                f"{where}: unknown op '{op}'; allowed: add-label, remove-label, create-comment, "
                "update-comment"
            )
    for n, count in comment_ops.items():
        if count > 1:
            errors.append(f"issue #{n}: {count} comment changes; the maximum is 1 per run")
    return errors


# ---------- validation ----------


def validate(raw, snap, issue=None):
    errors, warnings = [], []
    for field in ("readAt", "issues"):
        if field not in raw:
            errors.append(
                f"missing top-level field '{field}'; the snapshot has: "
                f"{', '.join(sorted(raw)) or 'nothing'}"
            )
    if "readAt" in raw and parse_time(raw["readAt"]) is None:
        errors.append(
            f"readAt '{raw['readAt']}' is not an ISO 8601 time, for example 2026-10-27T09:00:00Z"
        )
    if issue is not None and not raw.get("currentUser"):
        errors.append(
            "gate mode needs 'currentUser'; read it with the tracker operation current-user"
        )
    known = set()
    for k, i in enumerate(snap["issues"]):
        if not isinstance(i.get("number"), int):
            errors.append(f"issues[{k}] has no number; its fields are: {', '.join(sorted(i))}")
            continue
        known.add(i["number"])
        if i.get("readError"):
            continue
        if i.get("state") not in ("open", "closed"):
            errors.append(
                f"issue #{i['number']}: state must be open or closed, not '{i.get('state')}'"
            )
        if i.get("state") == "open" and "comments" not in i:
            errors.append(
                f"issue #{i['number']} is open but has no 'comments'; read them with "
                "list-issue-comments (use [] if none)"
            )
    for p in snap["prs"]:
        if p["state"] == "open" and p["closes"] and p["files"] is None:
            errors.append(
                f"PR #{p['number']} is open but has no 'files'; read them with get-pr-files"
            )
    for i in snap["issues"]:
        if i.get("readError") or not isinstance(i.get("number"), int):
            continue
        text = body_fields(i["body"]).get("depends on")
        if text:
            for n in parse_depends(text)[0]:
                if n not in known:
                    errors.append(
                        f"issue #{n} is a blocker of #{i['number']} but is not in the snapshot; "
                        f'read it with get-issue and add it, or add {{"number": {n}, "readError": '
                        '"<reason>"}'
                    )
    if issue is not None and issue not in known:
        errors.append(f"the gate issue #{issue} is not in the snapshot; read it with get-issue")
    if "nativeEdges" not in raw:
        warnings.append("no nativeEdges: native tracker relations will not be used")
    return errors, warnings


# ---------- CLI ----------


def strip_private(res):
    return {k: v for k, v in res.items() if not k.startswith("_")}


def use_utf8_output():
    # The Windows console uses a code page such as cp1250. The output has emoji and arrows.
    for stream in (sys.stdout, sys.stderr):
        with contextlib.suppress(AttributeError, ValueError):
            stream.reconfigure(encoding="utf-8")


def main(argv=None):
    use_utf8_output()
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("validate", "analyze", "gate", "plan"):
        p = sub.add_parser(name)
        p.add_argument("snapshot")
        p.add_argument("--backlog", help="path to backlog.md")
        p.add_argument("--issue", type=int, required=(name == "gate"))
        if name == "plan":
            p.add_argument("--out", required=True)
            p.add_argument("--sync-labels", action="store_true")
            p.add_argument("--notify", action="store_true")
    cp = sub.add_parser("check-plan")
    cp.add_argument("snapshot")
    cp.add_argument("changes")
    a = ap.parse_args(argv)

    raw, snap = load_snapshot(a.snapshot)
    user = raw.get("currentUser")
    if a.cmd == "check-plan":
        try:
            with open(a.changes, encoding="utf-8") as fh:
                doc = json.load(fh)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            fail([f"cannot read {a.changes}: {e}"])
        errors = check_plan(snap, doc, user)
        if errors:
            fail(errors)
        print(f"OK: {len(doc.get('changes') or [])} change(s) passed the check")
        return
    errors, warnings = validate(raw, snap, getattr(a, "issue", None))
    for w in warnings:
        print("WARNING: " + w, file=sys.stderr)
    if errors:
        fail(errors)
    rows = parse_backlog(a.backlog)
    if a.backlog and not rows:
        print(f"WARNING: no backlog rows read from {a.backlog}", file=sys.stderr)
    if a.cmd == "validate":
        print(f"OK: {len(snap['issues'])} issue(s), {len(snap['prs'])} PR(s)")
    elif a.cmd == "analyze":
        res = analyze(snap, rows, user)
        if a.issue is not None:
            v, b, n, r = gate(snap, rows, a.issue, user)
            res["gate"] = {"issue": a.issue, "verdict": v, "blockedBy": b, "next": n, "reason": r}
        json.dump(strip_private(res), sys.stdout, ensure_ascii=False, indent=2)
        print()
    elif a.cmd == "gate":
        v, b, n, r = gate(snap, rows, a.issue, user)
        print(f"Reason: {r}")
        print(f"Verdict: {v}")
        if v != "clear" and b:
            print("Blocked by: " + " ".join(f"#{x}" for x in b))
        print(f"Next: {n}")
    elif a.cmd == "plan":
        doc = plan(snap, rows, user, a.sync_labels, a.notify)
        with open(a.out, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, ensure_ascii=False, indent=2)
        print(f"Wrote {len(doc['changes'])} change(s) and {len(doc['skipped'])} skip(s) to {a.out}")


if __name__ == "__main__":
    main()
