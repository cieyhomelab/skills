# Building the graph (steps 1–2)

One node per issue in scope; one directed edge `A → B` when **B depends on A** (A blocks B). Parent/child lines (`Epic:`, `Story:`) are structure, not blocking edges — an epic is never a blocker of its own stories.

## Edge sources, in order of authority

1. **Issue body** — the `Depends on:` line `om-backlog` writes into every story and task. Accept `#<n>`, backlog ids (`E01-S02`), comma or space separated, and `none`. A body line is authoritative for that issue.
2. **Native tracker relations** — only when the descriptor defines **list-issue-dependencies**. Merged with the body edges; an edge present natively but missing from the body is kept and reported as map drift.
3. **`${SPECS_DIR}/backlog.md`** — the `Depends on` column of every selected source section. Used to find nodes and to detect drift; when an issue has no body line at all, the row's edges are used and marked `(from backlog.md)`.

Edges always reach outside the selected scope: a story in `--epic E02` that depends on `E01-S03` loads `E01-S03` as a node, shown as *external*.

## Resolving backlog ids

A backlog id resolves to an issue number only through the issue's `Backlog source:` + complete `Backlog id:` body lines, or through the matching row in the same source's `backlog.md` section. Never resolve by title prefix (`E01` must not match `E01-S01`), never across sources. An id that resolves to nothing, or to more than one issue, is an unresolved blocker (rule C5).

## Node state

Evaluate top to bottom; first match wins.

| State | When |
|---|---|
| `Resolved` | issue closed as completed, **or** its implementation PR is merged (issue still open → add the note "merged, issue not closed") |
| `Dropped` | issue closed as not planned, or closed with no completion reason and no merged PR |
| `In flight` | any claim signal (below), **or** an open PR closes or references it |
| `Free` | open, no claim signal, no open PR |
| `Unknown` | a read needed above failed — name the read |

**Claim signals** (the collection's three-signal check): an assignee; the `in-progress` label; a `🤖`-prefixed claim, take-over, or hand-off comment. `ci-monitoring` is never a claim signal. Record the owner(s) — every distinct login behind any signal — and the time of the newest signal or commit, comment, or label change by the owner.

**Stale.** An `In flight` node whose newest owner activity is older than `STALE_HOURS` (default 24) is `In flight (possibly stale)`. It stays in flight: a stale claim is reported, never treated as free.

## What to read, and how much

- One **get-issue** per node; **list-issue-comments** only for open nodes (claim comments).
- One **search-prs** per open node for PRs whose body closes the issue (`Closes|Fixes|Resolves #n`) or references it (`Refs #n`); a `Refs` PR adding a file under `${SPECS_DIR}` is a spec PR — in flight, but it never touches code, so it is excluded from file overlap.
- **get-pr-files** only for open, non-spec implementation PRs.
- Cap: when the scope exceeds 100 nodes, read the first 100 in backlog order plus every blocker they reach, and state the truncation in the report header.
