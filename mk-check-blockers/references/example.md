# Worked example (calibration)

A small backlog and the report it must produce. Use it to check your own classification before reporting: the same input must give the same findings.

## Input

`backlog.md` for `.ai/specs/product-brief.md`:

| Id | Issue | Depends on |
|---|---|---|
| E01-S01 | #12 | — |
| E01-S02 | #13 | E01-S01 |
| E01-S03 | #14 | E01-S02 |
| E02-S01 | #20 | — |
| E02-S02 | #21 | E02-S01, E01-S01 |

Tracker, read at 2026-10-27T09:00Z, `labels.enabled: true`, `STALE_HOURS` 24:

- #12 open, no assignee, no label, no PR. Body `Depends on: none`.
- #13 open, assignee `ana`, `in-progress`, claim comment 2026-10-27T08:10Z, open PR #40 (`Closes #13`), files `src/modules/booking/service.ts`, `src/modules/booking/schema.ts`.
- #14 open, no signals. Body `Depends on: E01-S02`.
- #20 closed as completed, PR #38 merged.
- #21 open, assignee `jan`, `in-progress`, claim comment 2026-10-25T07:00Z, no PR, no comments since. Body `Depends on: E02-S01, E01-S01`. Spec lists `src/modules/booking/schema.ts`.

## Expected classification

| Node | State | Findings |
|---|---|---|
| #12 | Free | C2a (blocker of #13), C2a (blocker of #21) |
| #13 | In flight (`ana`) | C2a — started while #12 is free |
| #14 | Free, waiting | — |
| #20 | Resolved | — |
| #21 | In flight (`jan`, possibly stale: 50 h) | C2a — #12 free; C4 — stale, holds nothing downstream so **C4 does not fire**; C6b — predicted `schema.ts` overlaps PR #40 |

Note the C4 decision: `#21` has no dependents, so a stale lock on it wastes nobody's time but its owner's; it is reported as `(possibly stale)` in the table, not as a conflict.

## Expected report (abridged)

```markdown
⛔ `mk-check-blockers` — 3 conflicts (2 need a human now), 1 safe to start, 2 waiting on blockers.
Scope: product-brief.md, all epics, read 2026-10-27 09:00Z. Native relations not read (no list-issue-dependencies). 1 footprint skipped (#14 has no spec).

**Conflicts**
1. ⛔ C2a — #13 E01-S02 (@ana) started while blocker #12 E01-S01 is free, nobody on it. → take #12 first: `om-auto-fix-issue 12`, or keep #40 draft until it merges.
2. ⛔ C2a — #21 E02-S02 (@jan, possibly stale 50 h) started while blocker #12 E01-S01 is free. → same blocker; agree who takes #12.
3. ⚠️ C6b — #21 (@jan, no PR yet) is expected to change `src/modules/booking/schema.ts`, which PR #40 (@ana) already changes. → #21 branches from #40 or waits for it.

**Safe to start** (for jan)
1. #12 E01-S01 — unlocks 3 (#13, #14, #21). → `om-auto-fix-issue 12`

**Critical path**: #12 → #13 → #14 (3 items; 1 in flight, 2 free).

Next: om-auto-fix-issue 12
```

Gate mode on `#14` from the same input:

```markdown
⏳ `mk-check-blockers` — #14 E01-S03: blocker #13 is in flight (@ana, PR #40 open), and #13 itself waits on #12 (free).
Verdict: wait
Blocked by: #13 #12
Next: om-auto-fix-issue 12
```

`Blocked by:` lists direct blockers first, then transitive ones; `Next:` points at the nearest **free** blocker, because taking it is the fastest way to unblock the chain.
