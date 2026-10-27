# Syncing the `blocked` label (step 6, `--sync-labels` only)

The one write this skill can make. It turns the graph into a label other people and agents already respect: `om-merge-buddy` and `om-approve-merge-pr` treat `blocked` as a hard block, and a repo that installs `references/preflight-overlay.md` stops `om-auto-fix-issue` on it.

## Preconditions

- `labels.enabled` is `true` and the `blocked` label exists (else refuse and name **ensure-label-taxonomy**).
- A user is present. Unattended runs never sync — report the diff and stop.
- Not in gate mode.

## The diff

From rule C7 only — nothing else changes labels:

- **Add `blocked`** to an open node with at least one non-resolved blocker, **unless** it is `In flight` by another actor (claim etiquette: leave a claimed item's labels to its owner; the conflict is already in the report as C2).
- **Remove `blocked`** from a node whose blockers are all `Resolved` **and** whose `blocked` was added by this skill (its marker comment exists). A `blocked` a human applied for another reason is never removed; list it as "blocked by hand — not touched".

Show the diff as a table (issue, change, reason) and wait for "yes", or edits. Nothing is written before that.

## Applying it

For each confirmed row, in order:

1. **label-issue** / **unlabel-issue** through the guard (`apply_issue_label` and its removal counterpart). A missing label degrades to a logged skip.
2. One marker-idempotent comment per issue — find an existing one with **list-issue-comments** and rewrite it with **update-comment**; post with **comment-issue** only when none exists:

   - added: `` 🤖 `mk-check-blockers` — blocked by #{a}, #{b}. Remove when they are done; this comment is updated on every sync. ``
   - removed: `` 🤖 `mk-check-blockers` — unblocked: #{a}, #{b} are done. Safe to start. ``

3. Skip rows whose label and comment already match. Running the sync twice changes nothing the second time.

Report the applied rows in one line each and end with the usual `Next:` line.
