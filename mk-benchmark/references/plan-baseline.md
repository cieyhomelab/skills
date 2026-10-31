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
8. Give a kind to each backlog item. Use the kind rules below.
9. Ask the user the interview questions below. Ask all questions in one message.
10. Write the plan file in the format below. Write `auto` in each *Sprint* cell.
11. Do not write the lines `Baselined` and `Earned at baseline`. Step 5 of SKILL.md writes them with `freeze`.
12. Run `python3 scripts/benchmark.py schedule "${BENCH}/plan.md"`. The script fills the *Sprint* cells.
13. Run `python3 scripts/benchmark.py check "${BENCH}/plan.md"`. If the check fails, correct the file and run the check again.
14. Show the item table, the planned hours, and the planned end date to the user.
15. If backlog items are already closed, tell the user that the baseline is retrospective.
16. Ask the user to confirm the baseline, or to change sizes and kinds.
17. If the user changes a size or a kind, write the change. Run steps 12 and 13 again.
18. Continue only after the user confirms.

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

## Kind rules

| Kind | Use for |
| --- | --- |
| `build` | Code, tests, specs, configuration. Agents can do a large part of this work. |
| `human` | Interviews, workshops, decisions, approvals, research with people. Agents cannot speed up this work. |

1. If one backlog item has both kinds of work, use the kind of the larger part.
2. The script forecasts `build` work with the measured velocity and `human` work with the plan capacity.

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

| Id | Issue | Title | Size | Kind | Sprint |
|---|---|---|---|---|---|
| E01-S01 | #23 | A user signs in with a local account | M | build | auto |
| E04-T01 | #151 | Interview one or two deciders | M | human | auto |
```

1. Keep the order of the rows from `backlog.md`. The order is the dependency order.
2. If the user changes the size table, write the new values in the `Size table:` line.
3. The *Kind* column is optional. A missing kind is `build`.
4. After `freeze`, the header also has `- Baselined: <date>` and `- Earned at baseline: <h> (build <h>, human <h>)`.
5. The script calculates the capacity as FTE × focus hours ÷ (1 + buffer) for each working day.
