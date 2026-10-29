# Off-backlog issues

This file tells how to find and classify the off-backlog issues. Step 3 uses it. Step 3 runs only in `artifacts` mode and only when `--epic` is not set.

## Collect

1. Run **search-issues** for open issues. Use a limit of 200.
2. Remove each issue that `backlog.md` contains. Also remove the epics.
3. Read each remaining issue with **get-issue**. Read its labels and its body.
4. If the search reached the limit, write in the report how many issues you did not read.

## Classify

Use the first row that matches. Take the label names from the label taxonomy of the agentic config. If `labels.enabled` is false, classify from the body and say this in the report.

| # | Class | Condition | Result |
| --- | --- | --- | --- |
| 1 | Excluded | The issue is in `--exclude`. | List it. Do not count it. |
| 2 | Included | The issue is in `--include`. | Size it and give it hours. |
| 3 | Decision | The issue asks open product or design questions. It does not change code. Example: a list of open questions, a title that starts with "Decide". | Count it as a blocking question. List the work items or phases that its body names. |
| 4 | Included (auto) | The issue is a bug or a security issue, **and** it has the label `priority-high` or `risk-high`. | Size it and give it hours. |
| 5 | Listed | All other issues. | List it with its labels. Do not count it. |

In the report, list each issue with its class and its number. Then the user can move an issue with `--include` or `--exclude` in the next run.

## Size of a fix

A bug fix or a security fix goes through `om-prepare-issue` and `om-auto-fix-issue`. It does not get a written spec. Mark it `fix: true` in the input file. Then the script subtracts the spec share.

Size a fix by the scope of the change. Do not size it by its risk label. The risk label tells how carefully to review the fix. It does not tell how much work the fix is.

Use the first row that matches:

| Size | Condition in the issue body |
| --- | --- |
| L | The fix needs a data migration. Or it changes a business rule, the permission model, or a public contract. |
| M | The fix changes more than one layer, for example the UI and the API. Or it changes more than one module, or it needs a new test suite. |
| S | All other fixes. Example: one module, one configuration change, one behavior. |

1. If a fix has the label `risk-high` or `security`, add this note to its row: "review by a model of a different family is necessary".
2. This review is part of the human hours. The label does not add hours.

## Other included issues

1. If an included issue is a feature or an improvement, use the size rules for backlog items.
2. Do not mark it `fix: true`. It gets the full hours, with the spec share.

## Design-system check

If an open off-backlog issue of any class says that it blocks the design system, the `designSystem` phase is not done. Give the number of that issue as the reason in the report.
