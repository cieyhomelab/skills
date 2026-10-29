# Report templates

This file gives the templates for the estimate report (step 9), the baseline block (step 9), and the calibration report (step 10). Take each number from the script output.

## Contents

1. Estimate report
2. Baseline block
3. Calibration report

## Estimate report

A person reads this report. Use this default structure. You can remove a section that has no content. You cannot remove the first line, the totals table, or the baseline block.

```markdown
📋 `mk-estimate` — {POC|MVP}, {devs} FTE: **{sprints} sprints (~{weeks} weeks)**, bound by {binding clock}. Confidence: {high|medium|low}.

{Scope: mode, source of the backlog, --epic, --remaining, date of the tracker read. Default values that the run used. Assumed sizes. POC epic selection. Early-mode range.}

{Changes: only if an earlier estimate for the same target exists. Which rule or tracker change moved which rows, from which value to which value.}

| | Human FTE h | Agent h |
|---|---|---|
| One-time phases | {h} | {h} |
| Work items ({n}: {s} S · {m} M · {l} L) | {h} | {h} |
| In flight ({n}, finishing only) | {h} | {h} |
| Off-backlog ({n} included) | {h} | {h} |
| Base buffer (+{pct}%) | {h} | {h} |
| Blocking questions ({n}: {id → blocked ids}) | {h} | {h} |
| Unplanned allowance ({pct}%) | {h} | {h} |
| **Total** | **{h}** | **{h}** |

{Calendar: human total ÷ human capacity, agent total ÷ agent capacity, binding clock. Dependency floor only if it binds.}

💰 API: ~{M} M tokens → {cost | not configured} · Subscription: {devs} × {months} mo → {cost | not configured} (prices: {catalog, asOf {date} | interview, reason})

⚠️ Split first: {XL work item ids} → `om-backlog {brief} --epic {epic}`
⚠️ Blocking questions: {counted ids and what each blocks}. Not counted: {ids and reasons}.

<details><summary>Off-backlog ({n} open issues)</summary>

| Class | Issues | Result |
|---|---|---|

</details>

<details><summary>One-time phases</summary>

| Phase | Human h | Agent h | Status |
|---|---|---|---|

</details>

<details><summary>Per epic</summary>

| Epic | Work items | Human h | Agent h |
|---|---|---|---|

</details>

<details><summary>All work items ({n})</summary>

| Work item | Size | Why (rule) | Human h | Agent h |
|---|---|---|---|---|

</details>

🔁 Next: `{skill} {argument}`
```

1. Remove a row of the totals table if its value is 0 in both columns. Keep the row "Total".
2. If the run used `--remaining`, keep the section "One-time phases".
3. If the off-backlog scan ran, keep the section "Off-backlog", also when no issue is included.
4. For an in-flight work item, write `{size} · in flight (PR #{n})` in the column "Size".
5. Make the section "Changes" from two results that you calculated separately. Do not edit the earlier result.

## Baseline block

The calibration reads this block. Use exactly this structure. Put it at the end of the estimate file, in a fenced block with the info string `mk-estimate-baseline`.

```json
{
  "date": "YYYY-MM-DD",
  "confidence": "high|medium|low",
  "configHash": "sha256 of .ai/estimate.config.json, or defaults",
  "inputFile": "{report-name}.input.json",
  "script": "{the full JSON output of scripts/estimate.py estimate}",
  "sizeReasons": { "#29": "risk-high" },
  "blocking": [ { "id": "Q14", "counted": true, "blocks": ["#30"] }, { "id": "Q01", "counted": false, "reason": "blocks only finished work items" } ],
  "offBacklog": { "included": [10], "decision": [50], "listed": [100], "excluded": [], "unread": 0 },
  "assumptions": ["..."]
}
```

1. Put the full script output as an object in `script`. Do not copy only some of its keys.
2. Do not add keys to this structure. A different key name breaks the calibration.

## Calibration report

A person reads this report. Use this default structure. You can remove a warning line that does not apply.

```markdown
🎯 `mk-estimate --calibrate` — window {from}..{to}: human clock ×{factor} ({n} evidence points), agent clock ×{factor} ({n}). {The proposed change in one line, or "no change — not sufficient evidence".} Confidence: {high|medium|low}.

{Scope: baseline files read and skipped, delivered work items, unplanned work, evidence sources for each clock, approx values, capacityUsed.}

| Size | Clock | Work items | Estimated h | Actual h | Factor | Current → proposed |
|---|---|---|---|---|---|---|

📋 Buffer check: {pct}% of the work items took more than the estimate and the buffer → {keep | raise to … | lower to …}.
⚠️ Sizing, not hours: {size → work items}
⚠️ Unplanned work: {n} work items, {pct}% of the window — run `mk-estimate --target {target} --remaining`

Proposed diff for `.ai/estimate.config.json`. Apply it by hand, then add an entry to `calibration.history`:

~~~json
{the diff from the script output}
~~~

<details><summary>Evidence for each work item ({n})</summary>

| Work item | PR | Size | Estimated human / agent | Actual human / agent | Source |
|---|---|---|---|---|---|

</details>

🔁 Next: apply the diff, then run `mk-estimate --target {target} --remaining`
```

Calibration confidence:

| Confidence | Condition |
| --- | --- |
| `high` | Both clocks have a factor for each size, without `approx` values. |
| `medium` | One or both clocks use the global factor. |
| `low` | One or both clocks have no proposal. |
