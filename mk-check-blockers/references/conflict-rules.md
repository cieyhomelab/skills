# Conflict rules (step 3)

Apply every rule to every node; a node can carry several findings. Severity orders the report: ⛔ stops work or wastes it, ⚠️ needs a human decision soon, 🏷️ is bookkeeping. A rule whose evidence could not be read does not fire — the missing read goes to coverage.

| # | Finding | When | Severity | Owner | Next action |
|---|---|---|---|---|---|
| C1 | Cycle | the edges form a loop (A → B → … → A) | ⛔ | backlog owner | break one edge at the source: edit the `Depends on:` line, then `om-backlog <source> --epic <id>` to refresh the map |
| C2a | Started too early, blocker idle | an `In flight` node has a blocker that is `Free` (nobody works on it) | ⛔ | the in-flight node's owner | pause or rescope the dependent, or take the blocker first: `om-auto-fix-issue <blocker>` |
| C2b | Started too early, stacked | an `In flight` node has a blocker that is also `In flight` | ⚠️ | both owners | agree an order: the dependent rebases after the blocker merges; its PR stays draft until then |
| C3 | Double claim | one issue shows claim signals from two or more distinct logins, or two or more open PRs close it | ⛔ | all owners named | one owner keeps it; the other closes their PR or hands back — never decided here |
| C4 | Stale lock holding a chain | a `possibly stale` node has at least one non-resolved dependent | ⚠️ | the stale owner | owner resumes (`om-auto-continue-pr <pr>`) or releases; takeover only through `om-auto-fix-issue <n> --force`, which posts the override comment |
| C5 | Dropped or missing blocker | a blocker is `Dropped`, does not exist, resolves ambiguously, or its `Depends on:` entry is unparseable | ⛔ for in-flight dependents, ⚠️ otherwise | backlog owner | decide whether the dependency still holds; fix the line at the source |
| C6 | File overlap | two open implementation PRs for different issues change at least one same file, or a PR reports `mergeable: CONFLICTING` | ⚠️ (⛔ when CONFLICTING) | both PR owners | merge the one earlier in backlog order first; the other rebases; consider adding a `Depends on:` if the overlap is structural |
| C7 | Label drift | `labels.enabled` and: `blocked` present while every blocker is `Resolved`; or absent on an open, unclaimed node with a non-resolved blocker | 🏷️ | — | `mk-check-blockers --sync-labels` |
| C8 | Map drift | the body's `Depends on:` and the `backlog.md` row (or a native relation) disagree | 🏷️ | backlog owner | `om-backlog <source> --epic <id>` re-syncs the map; the body decided this run's verdict |

## Notes on the rules

- **C2 is the core conflict.** It is what happens when someone picks the next issue by title without checking `Depends on:`. Report the dependent and every non-resolved blocker on one line, with both owners.
- **C3 uses distinct logins.** The automation user plus a human assignee on the same run is one owner when the claim comment names the human's run; otherwise it is two.
- **C6 ignores generated and lock files** (`*.lock`, lockfiles named in the repo's `AGENTS.md`, generated paths listed there): they overlap on almost every PR and say nothing about design. List at most five shared paths per pair, then a count.
- **C6 is a hint, not an edge.** File overlap never adds a dependency to the graph; it suggests one to the owners.
- **Same owner.** C2b and C6 between two items held by the same login are reported once as a note ("your #12 and #15 touch the same files"), not as a conflict.
- **Dropped blocker with all dependents free** stays ⚠️: nobody has wasted work yet, but the next pick will.
