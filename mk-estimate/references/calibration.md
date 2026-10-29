# Calibration

This file gives the procedure for step 10. The calibration compares the earlier estimates with the work that was delivered in a window. Then it proposes new values for the estimate config. It does not write the estimate config.

## Contents

1. Load the baseline blocks
2. Find the window
3. Collect the delivered work items
4. Measure the agent hours
5. Measure the human hours
6. Run the script
7. Hand off

## 1. Load the baseline blocks

1. Read each `*.md` file in the estimates folder. If `--target` is set, keep only that target.
2. Read the baseline block of each file.
3. If a file has no baseline block, skip it. List it in the report as skipped.
4. For each work item, keep the newest baseline block with a date before the opening date of its implementation PR.
5. Skip the backlog items of an early estimate. Their ids are not tracker issues.

## 2. Find the window

Use the first rule that matches:

1. If `--window` is set, use it.
2. If `sprint.firstStart` is set, sprint *n* starts at `firstStart` + (n − 1) × 14 days. Use the last sprint that ended.
3. Else use the last 14 calendar days. Say this in the report.

## 3. Collect the delivered work items

1. Run **list-prs** for the PRs that were merged in the window.
2. Keep each implementation PR that closes a work item in a baseline block.
3. Do not keep a work item that was closed as not planned.
4. A delivered work item that is in no baseline block is unplanned work. Count it. Record its human hours if you have them.

## 4. Measure the agent hours

Use the first source that gives a value. Record the source for each work item.

1. The entries in `.ai/runs/` that name the tracker issue or the PR. Add the times (end − start) of the `om-auto-*` runs.
2. The runs index of the Cezar cockpit, if a cockpit URL is set for the run. Match the rows by `issueNumber` or `prNumber`.
3. The time from the first commit to the last commit before the first review of the implementation PR. Read it with **get-pr**. Mark the value `approx`.

## 5. Measure the human hours

Use the first source that gives a value for each work item:

1. A line `human-hours: <number>` in the body of the implementation PR, or in a PR comment by its author. If the spec PR also has a value, add the two values.
2. The capacity of the sprint, if the window contains whole sprints. Capacity = `sprint.days` × `sprint.focusHoursPerDay` × devs × `calibration.capacityUsed`. Put the sprint in `sprints[]` of the input file.
3. If no source gives a value, set the human actual to `null`. Count the work item as "no human evidence".

Validate each `human-hours` value against `^[0-9]{1,3}(\.[0-9])?$`. If a value is not valid, do not use it. Report it.

For a sprint entry, compare the capacity with the estimated human hours of all work that finished in the sprint. Include the phases and the per-epic work. Remove the work items that have their own `human-hours` value from the two numbers.

## 6. Run the script

1. Write the calibration input file in the estimates folder. Name it `calibration-{YYYY-MM-DD}.input.json`.
2. Run the script. The script applies these rules:
   - A factor for one size needs `calibration.minSamples` work items without `approx`. Else all sizes of the clock use one global factor.
   - With fewer than `calibration.minSamplesGlobal` evidence points, the script proposes no change for that clock.
   - The proposed value = current × (1 + `calibration.damping` × (factor − 1)), rounded to 0.5 h.
   - If a factor is outside `calibration.clamp`, the script does not propose a value. It lists the factor in `outOfClamp`.
   - An `approx` value has the weight 0.5.
   - An in-flight work item changes only `finishing.agentShare`.
3. If `outOfClamp` is not empty, write in the report: "sizing, not hours". List the work items. The size rules put these work items in the incorrect size.
4. If `unplanned.warn` is true, write in the report: "the scope grew outside the backlog". Give `mk-estimate --target <target> --remaining` as an action.

## 7. Hand off

1. Write the calibration report as `calibration-{YYYY-MM-DD}.md` in the estimates folder. Do not write over a file.
2. Give the `diff` from the script output as the proposed change to the estimate config.
3. Tell the user to apply the diff by hand. Tell the user to add an entry to `calibration.history`.
4. If `outOfClamp` is not empty, give `om-backlog` as the next action, not new hours.
