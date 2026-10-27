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

Read in bulk first, per item only where bulk cannot answer. The order below keeps a 40-issue backlog at roughly five tracker calls plus one per open implementation PR, instead of five per issue.

1. **search-issues**, once per selected source, with the fields `number,title,state,stateReason,labels,assignees,body,updatedAt` and `--state all`, limit 200. This yields every node's body (`Depends on:`, `Backlog source:`, `Backlog id:`), labels, and assignees in one call — enough for the edges, two of the three claim signals, and `Resolved`/`Dropped`.
2. **list-prs** once, open PRs, fields `number,title,body,isDraft,author,headRefName,mergeable,updatedAt,files`. Map each PR to its issue through `Closes|Fixes|Resolves #n` (implementation) and `Refs #n` (spec PR when it adds a file under `${SPECS_DIR}`). The `files` field covers rule C6 without a per-PR call; use **get-pr-files** only when the tracker omits it.
3. **search-prs** for merged PRs closing the open nodes that have no closing PR in step 2 (`merged, closes #n`), one call per source using an `in:body` query; a hit makes the node `Resolved (merged, issue not closed)`.
4. **list-issue-comments** only for open nodes with no assignee and no `in-progress` label — the third claim signal can only change the state of those. Also for every `In flight` node, to date its newest owner activity for the stale check.
5. **get-issue** only for a blocker outside the selected sources (an external dependency the bulk search did not return), and in gate mode for the target and its transitive blockers.

Spec PRs count as in flight but never touch code, so they are excluded from C6.

**Predicted footprint** (rule C6b). For every `In flight` node that has no open implementation PR yet, and for every *Safe to start* candidate, read the files the work is expected to touch from the first of: the spec's *Files to change* / *Affected modules* section (`Spec:` line in the issue, or the merged spec PR); the issue's *Out of scope*/*Expected outcome* module names; a module label. Keep it as a list of paths or module names marked `(predicted)`; it feeds only C6b and never the graph.

Cap: when the scope exceeds 100 nodes, read the first 100 in backlog order plus every blocker they reach, and state the truncation in the report header.
