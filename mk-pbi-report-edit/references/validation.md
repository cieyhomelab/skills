# Validation Loop

This file tells how to validate the changed report. Step 10 uses it.

## Checks

| # | Check | Command or tool | Pass condition |
| --- | --- | --- | --- |
| 1 | Schema and structure | `python scripts/validate_pbir.py -- <report name>.Report` | Exit code 0 |
| 2 | Fields | `python scripts/inspect_report.py --fields -- <report definition>` | Each field is in the model snapshot or in a `search_model` result |
| 3 | Files against plan | `python scripts/compare_plan.py -- <plan file> <backup folder> <report folder>` | Exit code 0 |

## Procedure

1. Do check 1.
2. Do check 2. For each field that is not in the model snapshot, call `mcp__powerbi-dax__search_model`.
3. Do check 3.
4. Write the result of each check in the validation table of the plan file.
5. If all checks pass, go to step 11 of the workflow.
6. If a check fails, read the error. Correct only the file that the error names.
7. Do the checks again.
8. Stop after 3 corrections. Also stop if a correction makes no progress.

## Exit codes of validate_pbir.py

| Code | Meaning | Action |
| --- | --- | --- |
| 0 | All files are valid | Continue |
| 1 | A file has an error | Correct the file |
| 2 | A schema was not available | Write "schema not checked" for these files. Do not report the check as passed. |

## When the validation fails

1. Set the plan status to `failed`.
2. Tell the user which changes are complete and which changes have no verification.
3. Give the restore command. Do not run it without approval:

   `python scripts/backup_report.py --restore -- <report folder> <report name> <timestamp>`

WARNING: The restore replaces the current `<report name>.Report` folder with the backup. Run it only after the user approves it. The script saves the current folder first, as `_backup/<timestamp>-before-restore/`.

4. If the user approves the restore, run the command. Set the plan status to `restored`.
