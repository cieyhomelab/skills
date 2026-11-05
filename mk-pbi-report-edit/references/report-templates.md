# Plan and Report Templates

This file gives the template of the plan file. Step 4 uses it to make the plan. Step 12 uses it to complete the change log.

## Plan template

Use exactly this structure. The script `compare_plan.py` reads the `## Files` section.

```markdown
# Power BI report edit: <report name>

- Timestamp: <timestamp>
- Report: <path of the .pbip file>
- Request: <the short command, or the path of the change spec>
- Status: draft
- Model snapshot: pbi-edit-<timestamp>-model.json
- Backup: not yet

## Changes

| # | Type | Page | Visual | Description | Fields | Status |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | new-visual | Sales | new | Column chart of sales by category | Product[Category], Sales[Total Sales] | planned |

## Files

- create: definition/pages/<page name>/visuals/<visual name>/visual.json
- modify: definition/pages/pages.json

## Validation

| Check | Result | Details |
| --- | --- | --- |
| Schema and structure | not run | |
| Fields | not run | |
| Files against plan | not run | |
| Check in Power BI Desktop | not run | |

## Log

- <timestamp>: plan made
```

Rules for the template:

1. Write each file path relative to the folder `<report name>.Report/`.
2. Start each file line with `- create: `, `- modify: `, or `- delete: `.
3. Use one of these values for the change status: `planned`, `blocked`, `done`, `failed`.
4. Use one of these values for the plan status: `draft`, `approved`, `done`, `failed`, `restored`.
5. For a `blocked` change, write the reason in the description.

## Report update

In step 12, update the plan file:

1. Set `Status` to `done`, `failed`, or `restored`.
2. Set `Backup` to the backup path.
3. Set the status of each change.
4. Write the result of each check in the validation table. Use `passed`, `failed`, or `not checked`.
5. Add one line to the log for each event: approval, backup, each change, each validation run, the Desktop check.

The response to the user has this default structure. You can change the order:

1. The plan file path.
2. The number of changes with each status.
3. The result of each check.
4. The backup path.
5. The blocked changes and their reasons, if there are blocked changes.
