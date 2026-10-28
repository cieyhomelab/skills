# Report template

This file gives the structure of the full report and the meaning of each rule code. Step 4 uses it when the run is not in gate mode.

## Rule codes

The script gives these codes. Use the evidence and the next action from `analysis.json`. Do not write new ones.

| Code | Finding | Severity |
| --- | --- | --- |
| C1 | The dependencies make a cycle. | `stop` |
| C2a | An owner started the dependent, but nobody works on its blocker. | `stop` |
| C2b | An owner started the dependent while a different owner works on its blocker. | `warn` (`note` if the owners are the same) |
| C3 | The issue has two or more owners, or two or more open PRs close it. | `stop` |
| C4 | A stale claim holds one or more dependents. | `warn` |
| C5 | A blocker is dropped, missing, ambiguous, or the `Depends on:` entry cannot be read. | `stop` if the dependent has an owner, else `warn` |
| C6 | Two open PRs change the same files, or a PR has merge conflicts. | `warn`, or `stop` for merge conflicts |
| C6b | A footprint shares a path with an open PR or with a different footprint. | `warn` |
| C7 | The `blocked` label does not agree with the dependencies. | `label` |
| C8 | `backlog.md` or a tracker relation does not agree with the issue body. | `label` |

## Emoji

Use only these emoji for these meanings: ⛔ `stop` · ⚠️ `warn` · 🏷️ `label` · ✅ no conflicts · ⏳ waits · 📋 notices · 🔁 resume.

## Structure

Use this default structure. You can change the words. Do not remove the `Next:` line. Remove each section that has no content.

```markdown
⛔ `mk-guard-dependencies` — {stop} stop, {warn} warn, {safe} safe to start, {waiting} waiting.
{One line: sources, --epic, the readAt time. Add each line from `coverage`.}

**Conflicts**
1. ⛔ C2a — #13 E01-S02 (@ana): started while blocker #12 E01-S01 is free. → `om-auto-fix-issue 12`
2. ⚠️ C6b — #21 (@jan): will change `schema.ts`, which PR #40 (@ana) changes. → start on the branch of PR #40.

**Safe to start**
1. #12 E01-S01 — Login. Unlocks 3. → `om-auto-fix-issue 12`

**Critical path**: #12 → #13 → #14.

<details><summary>All issues ({n})</summary>

| Issue | State | Owner | Blocked by | Blocks | Findings |
| --- | --- | --- | --- | --- | --- |
| #13 E01-S02 — Booking | In flight | @ana | #12 | #14 | C2a, C7 |

</details>

🏷️ {n} issues have a `blocked` label that does not agree. Run with `--sync-labels`.

Next: {the `next` value from analysis.json}
```

Write these parts as follows:

1. Write a maximum of 8 lines in *Conflicts*. Put the other findings in the table.
2. Write `stop` findings first, then `warn`, then `note`. Keep the order from `analysis.json`.
3. If a safe issue has a `warning`, add the rule code after its title.
4. If there are no conflicts, start the first line with ✅. Then write *Safe to start* first.
5. Write the 🏷️ line only if `label` findings exist and `--sync-labels` is not set.
6. If `--notify` ran, add one 📋 line with the number of comments posted and updated.
7. Do not give an opinion about code quality or about time. The report shows only order and owners.
