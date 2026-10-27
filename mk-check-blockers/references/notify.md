# Notifying owners (step 6, `--notify` only)

A report nobody reads changes nothing. `--notify` puts each ⛔ finding where its owner will see it: one marker-idempotent comment on the affected issue. It is the way a scheduled run (hourly, before stand-up) keeps the team informed without anyone invoking the skill.

## What gets a comment

Only ⛔ findings — C1, C2a, C3, C5 with an in-flight dependent, C6 when `CONFLICTING`. ⚠️ and 🏷️ findings stay in the report; a comment for every soft warning trains people to ignore the marker.

The comment goes on the **dependent** issue (the work that is at risk), never on the blocker and never on a PR. Claim etiquette holds: a comment is communication, not an edit — the title, body, labels, and assignees of a claimed item are untouched.

## Shape

Find an existing comment by marker with **list-issue-comments** and rewrite it with **update-comment**; post with **comment-issue** only when none exists.

```
🤖 `mk-check-blockers` — ⛔ {rule}: {one sentence, e.g. "started while blocker #12 (E01-S01, free, nobody on it) is not done"}.
Owner: @{login}. Next: {the finding's next action}.
Checked: {ISO-8601 time}. This comment is updated on every run and marked resolved when the conflict clears.
```

When a later run finds the conflict gone, rewrite the same comment to `` 🤖 `mk-check-blockers` — ✅ resolved: {what changed}. `` — never delete it, so the history stays readable.

## Preconditions

- Interactive run: show the list of comments to post and wait for a yes.
- Unattended run: `--notify` was passed explicitly on the invocation (a scheduled task's prompt counts); never notify from a run that was not asked to.
- Never more than one comment per issue per run; never a comment on an issue whose state is `Unknown`.
- `--notify` and `--sync-labels` may be combined; each keeps its own confirmation.
