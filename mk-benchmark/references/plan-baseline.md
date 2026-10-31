# Plan baseline

This file gives the procedure to make the plan file. Step 1 uses it when the plan file is missing or `--rebaseline` is set.

## Procedure

1. If `--rebaseline` is set, rename `${BENCH}/plan.md` to `${BENCH}/plan-<date>.md`. Use the `Baselined:` date of the old file.
2. Read the rows of `${SPECS_DIR}/backlog.md` in the scope of `--source` and `--epic`.
3. Do not add the epic rows. An epic row has `—` in the *Epic* column.
4. Do not add the rows in the section *Reserved, not filed*.
5. If `backlog.md` is missing, ask the user for the list of backlog items and their issue numbers.
6. Call **get-issue** for each backlog item. Read the acceptance criteria and the spec link.
7. Give a size to each backlog item. Use the size rules below.
8. Ask the user the interview questions below. Ask all questions in one message.
9. Write the plan file in the format below. Write `auto` in each *Sprint* cell.
10. Run `python3 scripts/benchmark.py schedule "${BENCH}/plan.md"`. The script fills the *Sprint* cells.
11. Run `python3 scripts/benchmark.py check "${BENCH}/plan.md"`. If the check fails, correct the file and run the check again.
12. Show the item table, the planned hours, and the planned end date to the user.
13. Ask the user to confirm the baseline or to change sizes.
14. If the user changes a size, write the change. Run steps 10 and 11 again.
15. Continue only after the user confirms.

## Size rules

| Size | Hours | Use for |
| --- | --- | --- |
| XS | 2 | A change in one file, or a setting. No new test. |
| S | 4 | One screen or one endpoint with 1–3 acceptance criteria. |
| M | 8 | One screen and its endpoint, or 4–6 acceptance criteria. |
| L | 16 | A flow over 2–3 screens, or 7–10 acceptance criteria, or a new integration. |
| XL | 32 | More than 10 acceptance criteria, or a new module. Ask the user to split it. |

1. The hours are hours of human focus work with agents. They include the review and the QA of the human.
2. If a backlog item is closed as completed, still give it a size. Its hours are part of the plan.
3. If the acceptance criteria are not clear, give the larger of the two possible sizes. Write the reason in your message.

## Interview questions

Give the default value in each question. If the user gives no answer, use the default value.

1. Is this a POC or an MVP? Default: MVP.
2. What is the start date of the delivery? Default: the date of the first merged implementation PR in the scope.
3. How many people work on the project, in FTE? Default: 1.
4. How many focus hours does one person have in one day? Default: 6.
5. How many working days does one sprint have? Default: 10.
6. What is the buffer? Default: 20% for a POC, 30% for an MVP.

## File format

Use exactly this structure. The script reads the header lines and the table.

```markdown
# Benchmark plan

- Type: MVP
- Start: 2026-10-12
- Sprint length (working days): 10
- Team FTE: 1
- Focus hours per day: 6
- Buffer: 30%
- Size table: XS=2, S=4, M=8, L=16, XL=32
- Baselined: 2026-10-31

| Id | Issue | Title | Size | Sprint |
|---|---|---|---|---|
| E01-S01 | #23 | A user signs in with a local account | M | auto |
```

1. Keep the order of the rows from `backlog.md`. The order is the dependency order.
2. If the user changes the size table, write the new values in the `Size table:` line.
3. The script calculates the capacity as FTE × focus hours ÷ (1 + buffer) for each working day.
