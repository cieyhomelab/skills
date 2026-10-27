# Gate mode as a preflight for the implementing skills

The claim check in `om-auto-fix-issue`, `om-fix`, and `om-auto-write-spec` answers "is someone else already on this issue?". It does not answer "are this issue's blockers done?". To make every run ask both, a repository adds a repo-local overlay — the extension contract every skill in this collection honors (`.ai/skills/<skill>/SKILL.md`, applied on top of the installed skill). This file is the text to put there; this skill never writes it.

## `.ai/skills/om-auto-fix-issue/SKILL.md`

```markdown
> **Repo-local override.** Adds a dependency preflight to the installed `om-auto-fix-issue`.

## Step 1 — before the concurrency check

Run `mk-check-blockers --issue {issueId}` and parse its `Verdict:` line.

- `clear` → continue with the concurrency check as usual.
- `wait` → stop before any claim. Report the `Blocked by:` issues and their owners. Do not claim, do not open a worktree. `--force` does not bypass this; resolving the blocker or editing the `Depends on:` line does.
- `conflict` → stop before any claim and relay the reported conflict and its owner.

If `mk-check-blockers` is not installed, continue and say in the final report that dependencies were not checked.
```

Use the same block, with the skill's own name and step, in `.ai/skills/om-fix/SKILL.md` (before step 1, *Claim the issue*) and `.ai/skills/om-auto-write-spec/SKILL.md` (before its claim). A batch driver that picks issues by itself (an `*-loop` skill, a scheduler) should take its candidates from the *Safe to start* list instead of the raw backlog.

## Why the stop is before the claim

A claim that is released a minute later still shows up in everyone's three-signal check. Stopping before the claim leaves the tracker exactly as it was, which is the point of a preflight.
