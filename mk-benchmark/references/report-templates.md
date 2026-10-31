# Report templates

This file gives the report template. Step 6 uses it.

## Report

Use this default structure. Remove each section that has no content. Write the numbers exactly as the script gives them.

```markdown
🎯 `mk-benchmark` — {verdict}: SPI {spi}, {progressPct}% of the plan earned ({donePct}% done), {plannedPct}% planned on {today}.
Planned end {plannedEnd}, forecast end {forecastEnd} ({delayWorkingDays} working days). UX coverage {ux.coveragePct}%.
{Scope: plan file, --source, --epic, read date. Baseline: {baselineMode}, {baselined}. Coverage limits from `coverage`. Backlog items with the status Unknown.}

**Warnings**
- ⚠️ {each line of `warnings`, without changes}

**Next action**
1. {the first entry of `readyUnowned`: assign an owner, with the number of items it blocks}
2. {else: the backlog item that most changes the verdict, with the reason}

**Schedule**

| Measure | Value |
|---|---|
| Planned hours | {plannedHours} |
| Planned value (PV) | {plannedValueHours} h |
| Earned value (EV) | {earnedHours} h |
| Done (strict) | {doneHours} h |
| Plan capacity | {planCapacityHoursPerDay} h/day |
| Velocity (build) | {velocityHoursPerDay} h/day ({velocitySource}) |
| Forecast | {forecastBuildDays} days of build + {forecastHumanDays} days of human work |

**Status of the backlog items:** {statusCounts as "Done 4 · In review 2 · ..."}

**Waiting on dependencies:** {each entry of `waiting`: item → #issues. Remove if empty.}

**Ready, no owner:** {each entry of `readyUnowned`, with `blocks`. Remove if empty.}

**Unplanned scope:** {unplanned items, or remove this line}

**Cost:** {humanHours} human h, {agentHours} agent h, {cost} {currency}, CPI {cpi}. {Remove if `cost` is null.}

**Agents (Cezar):** {running} running · {waiting} waiting for you · {queued} queued. {If `selfIncluded`, add "(includes this run)". Remove if `cezar` is null.}

**UX coverage vs {ux.reference}** ({ux.method})

| Kind | Present | Partial | Missing | Coverage |
|---|---|---|---|---|
| Screens | {n} | {n} | {n} | {pct}% |
| Flows | {n} | {n} | {n} | {pct}% |

{List of partial and missing entries with the evidence.}

<details><summary>All backlog items ({n})</summary>

| Item | Size | Kind | Sprint | Status | Owner | Earned |
|---|---|---|---|---|---|---|
| {id} — {title} (#{issue}) | {size} | {kind} | {sprint} | {status}{ ⛔ if blocked} | {assignees or —} | {earned}/{hours} h |

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
2. If the SPI and the forecast disagree, write both. Use the reason from `warnings`. Do not add your own forecast.
3. Write the credit rule one time: an open PR earns part of the hours, a done backlog item earns all hours.
4. Do not give a judgement about the product quality or the code quality.
