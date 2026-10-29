# Write back

This file gives the procedure to change labels and post comments. Step 5 uses it when `--sync-labels` or `--notify` is set.

## What changes

- `--sync-labels` adds `blocked` to an issue that waits for a blocker. It removes `blocked` when all blockers are resolved.
- The script removes `blocked` only if a comment from this skill exists on the issue. A person added the other labels. The script lists them under `skipped`.
- `--notify` writes one comment on each issue with a `stop` finding. The comment names the owner and the next action.
- When a later run finds no conflict, `--notify` changes the comment to "✅ resolved". It does not delete the comment.
- Each issue gets a maximum of one comment from this skill. Each run updates the same comment.

## Procedure

1. Make the plan. Run `python3 scripts/guard_dependencies.py plan "$WORK/snapshot.json" --out "$WORK/changes.json"`.
2. Add `--sync-labels`, `--notify`, and `--backlog` to the command as the user gave them.
3. Check the plan. Run `python3 scripts/guard_dependencies.py check-plan "$WORK/snapshot.json" "$WORK/changes.json"`.
4. If the check shows errors, do not correct `changes.json` by hand. Report the errors and stop.
5. Show the user a table with each change: the issue, the operation, and the reason.
6. Show the `skipped` list below the table.
7. Make sure that the task permits each change. Each change must come from `--sync-labels` or `--notify`.
8. Ask the user for "yes". Do not continue without "yes".
9. If the run is unattended, continue only if the invocation contains the flag. The prompt of a scheduled run counts as the invocation.
10. Do each change in the sequence of `changes.json`:
   - `add-label` and `remove-label`: use the label guard from the tracker descriptor.
   - `create-comment`: use **comment-issue** with the `body` exactly.
   - `update-comment`: use **update-comment** with `commentId` and the `body` exactly.
11. If an operation fails, record it. Continue with the next change.

## Verification

1. Collect a new snapshot for the changed issues. Use step 1 of the workflow.
2. Run `analyze` again.
3. Make sure that no `C7` finding remains for an issue with a label change.
4. Make sure that each changed issue has exactly one comment from this skill.
5. If a check fails, report the issue and the failed operation. Do not try the change again in this run.
6. Give the list of applied changes and failed operations to step 5 of the workflow.
