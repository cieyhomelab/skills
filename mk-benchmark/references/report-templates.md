# Report templates

This file gives the report template. Step 6 uses it.

## Report

Use this default structure. Remove each section that has no content. Write the numbers exactly as the script gives them.

```markdown
🎯 `mk-benchmark` — {verdict}: SPI {spi}, {progressPct}% of the plan earned ({donePct}% done), {plannedPct}% planned on {today}.
Planned end {plannedEnd}, forecast end {forecastEnd} ({delayWorkingDays} working days). UX coverage {ux.coveragePct}%.
{Scope: plan file, --source, --epic, read date. Coverage limits from `coverage`. Backlog items with the status Unknown.}

**Next action**
1. {one action that changes the verdict most, with the backlog item and the reason}

**Schedule**

| Measure | Value |
|---|---|
| Planned hours | {plannedHours} |
| Planned value (PV) | {plannedValueHours} h |
| Earned value (EV) | {earnedHours} h |
| Done (strict) | {doneHours} h |
| Velocity | {velocityHoursPerDay} h/day ({velocitySource}) |

**Status of the backlog items:** {statusCounts as "Done 4 · In review 2 · ..."}

**Unplanned scope:** {unplanned items, or remove this line}

**Cost:** {humanHours} human h, {agentHours} agent h, {cost} {currency}, CPI {cpi}. {Remove if `cost` is null.}

**Agents (Cezar):** {running} running · {waiting} waiting for you · {queued} queued. {Remove if `cezar` is null.}

**UX coverage vs {ux.reference}** ({ux.method})

| Kind | Present | Partial | Missing | Coverage |
|---|---|---|---|---|
| Screens | {n} | {n} | {n} | {pct}% |
| Flows | {n} | {n} | {n} | {pct}% |

{List of partial and missing entries with the evidence.}

<details><summary>All backlog items ({n})</summary>

| Item | Size | Sprint | Status | Earned |
|---|---|---|---|---|
| {id} — {title} (#{issue}) | {size} | {sprint} | {status}{ ⛔ if blocked} | {earned}/{hours} h |

</details>

📋 Files: {list of files that the skill wrote}
```

## Verdict lines

| Verdict | Meaning to write |
|---|---|
| `on track` | ✅ The earned value is at or above 95% of the planned value. |
| `at risk` | ⚠️ The earned value is 80–95% of the planned value. |
| `late` | ❌ The earned value is below 80% of the planned value. |
| `complete` | 🚀 All planned hours are earned. |
| `not started` | ⏳ The plan expects no work before this date. |
| `unknown` | The plan has no hours. Give the reason. |

## Rules for the text

1. Start with the verdict and the next action.
2. If the SPI and the forecast disagree, write both and give the reason. Example: the velocity of the last week is higher than the plan capacity.
3. Write the credit rule one time: an open PR earns part of the hours, a done backlog item earns all hours.
4. Do not give a judgement about the product quality or the code quality.
