# Gate for om-auto-fix-issue

This file gives the text of a local extension that makes `om-auto-fix-issue` check the blockers. Step 6 uses it when the user asks to add the gate.

The claim check in `om-auto-fix-issue` finds out if a different actor works on the issue. It does not find out if the blockers are resolved. This extension adds that check before the claim.

## Procedure

1. Tell the user to put the text below in `.ai/skills/om-auto-fix-issue/SKILL.md`.
2. Do not write the file yourself. The user decides.
3. If the user also uses `om-fix` or `om-auto-write-spec`, give the same text with the name of that skill.

## Text of the extension

```markdown
> **Repo-local override.** Adds a dependency gate to the installed `om-auto-fix-issue`.

## Step 1 — before the concurrency check

1. Run `mk-guard-dependencies --issue {issueId}`.
2. Read the `Verdict:` line.
3. If the verdict is `clear`, continue with the concurrency check.
4. If the verdict is `wait`, stop before the claim. Report the `Blocked by:` issues.
5. If the verdict is `conflict`, stop before the claim. Report the conflict and its owner.
6. Do not let `--force` skip this check.
7. If `mk-guard-dependencies` is not installed, continue. Write in the report that the blockers were not checked.
```

## Reason for the stop before the claim

A claim that the skill releases one minute later is still visible in the claim check of other actors. A stop before the claim keeps the tracker without changes.
