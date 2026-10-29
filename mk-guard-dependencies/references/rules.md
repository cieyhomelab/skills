# Shared rules

This file gives the rules for all skills in the `mk-` collection. They apply in each run, in addition to `## Rules` in SKILL.md.

## Tracker

1. Use only the operations that the tracker descriptor defines. Do not call the tracker CLI or the tracker API directly.
2. Change a label only through the label guard of the descriptor.
3. If `labels.enabled` is `false`, do no label work. Write in the report that labels are disabled.
4. If a label does not exist in the tracker, do not make it. Record a skip in the report.
5. Do not add a pipeline label, `in-progress`, or `qa-approved`. A different skill owns these labels.

## Claims

1. Before you change an issue, do the claim check. The signals are an assignee, the `in-progress` label, and a 🤖 claim comment.
2. If a different actor holds the claim, do not change the issue. Report the owner.
3. Do not release a claim that a different actor holds. A stale claim is still a claim.
4. The label `ci-monitoring` is not a claim.

## Comments

1. Start each comment with the marker `🤖 \`<skill-name>\` —`.
2. Before you post a comment, look for a comment with the same marker.
3. If a comment with the marker exists, update that comment. Do not post a second comment.

## Secrets

1. Do not write tokens, `.env` content, or credentials in a report, a comment, or a file.
2. If a value looks like a credential, replace it with `[redacted]` before you quote it.

## Emoji

Use each emoji only with this meaning: 🎯 goal · 📋 plan · 📝 spec · 🏷️ labels · 📸 evidence · 🔍 review · 🧪 tests · 💥 breaking · ✅ pass · ❌ fail · ⚠️ needs-human · ⛔ blocked · ⏳ waits · 🔁 resume · 🚀 merge/release. Emoji are decoration. A different skill reads only the text markers.

## Reports

1. Start the report with the result and the next action.
2. Keep facts, conclusions, and checks that did not run separate.
3. When you report that something is missing, tell where you looked.
4. Remove each section that has no content.
5. Write each line that a different skill reads in its exact shape. Do not translate or decorate it.
