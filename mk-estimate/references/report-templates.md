# Report templates

The user-facing shapes `mk-estimate` renders in step 7 (estimate) and step 9 (calibration), plus the machine block calibration parses. Follow `references/rules.md`. Read-only on the tracker; no chaining fields. Lead with the answer.

## Estimate report

```markdown
📋 `mk-estimate` — {POC|MVP}, {devs} FTE: **{sprints} sprints (~{weeks} weeks)**, bound by {human|agent} time. Confidence: {high|medium|low}.
{Scope: mode, brief/backlog source, --epic, --remaining, read date; defaulted config values; assumed sizes; POC epic selection; early-mode range.}

| | Human FTE h | Agent h |
|---|---|---|
| One-time phases | {h} | {h} |
| Items ({n}: {s} S · {m} M · {l} L) | {h} | {h} |
| In flight ({n}, finishing only) | {h} | {h} |
| Off-backlog ({n} included) | {h} | {h} |
| Base buffer (+{pct}%) | {h} | {h} |
| Blocking questions ({n}: {id → blocked items}) | {h} | {h} |
| Unplanned allowance ({pct}%) | {h} | {h} |
| **Total** | **{h}** | **{h}** |

💰 API: ~{Mtok} M tokens → {cost or "not configured"} · Subscription: {devs} × {months} mo → {cost or "not configured"} (prices: {catalog as of {asOf} | interview} {, reason for interview})

⚠️ Split first: {XL item ids → `om-backlog … --epic E0x`}
⚠️ Blocking questions: {counted ids and what each blocks}; not counted: {ids and why}

<details><summary>Off-backlog ({n} open issues)</summary>

| Class | Issues | Treatment |
|---|---|---|
| Included | #{n} — {title} ({size}, {rule}; auto / --include) | sized and costed |
| Decision | #{n} — {title} | counted as a blocking question |
| Listed | #{n}, #{n}, … | not counted — add with `--include` |
| Excluded | #{n} | `--exclude` |

</details>

<details><summary>One-time phases</summary>

| Phase | Human h | Agent h | Status |
|---|---|---|---|
| {phase} | {h} | {h} | {done — evidence | not done — reason} |

</details>

<details><summary>Per epic</summary>

| Epic | Items | Human h | Agent h |
|---|---|---|---|

</details>

<details><summary>All items ({n})</summary>

| Item | Size | Why (rule) | Human h | Agent h |
|---|---|---|---|---|

</details>

🔁 Next: `{skill} {argument}`
```

When an earlier estimate for the same target exists from the same day, add one short paragraph under the scope line: which rule or tracker change moved which rows, from what to what. It is derived by comparing two independently computed results, never by patching the earlier one.

Omit the ⚠️ lines, the in-flight, off-backlog, and allowance rows, and the per-epic block when empty; keep the off-backlog block whenever the scan ran, even with nothing included, because it is how the user sees what the estimate leaves out; keep the one-time phases block whenever `--remaining` is set. In the item list, an in-flight row shows `{size} · in flight (PR #{n})` and its finishing hours. Show the dependency floor as one sentence under the table only when it set the calendar.

## Baseline block (end of every saved estimate file)

A fenced block with the info string `mk-estimate-baseline`, holding the `--format json` object below plus `"hoursUsed"` (per-size hours actually applied, buffer excluded) and `"configHash"` (sha256 of `.ai/estimate.config.json`, or `"defaults"`). An estimate file without it cannot be calibrated.

`--format json` object: `{"target", "devs", "mode", "confidence", "date", "sprints", "bindingClock", "human": {"phases", "items", "baseBuffer", "questionBuffer", "total"}, "agent": {"phases", "items", "baseBuffer", "questionBuffer", "total"}, "cost": {"apiTokens", "api", "subscription"}, "prices": {"source": "catalog|interview", "asOf", "currency", "models": {...}, "seat"}, "splitFirst": [...], "blocking": [...], "epics": [...], "items": [{"id", "issue", "epic", "size", "rule", "human", "agent", "assumed", "inFlight", "implPr", "offBacklog"}], "offBacklog": {"included": [...], "decision": [...], "listed": [...], "excluded": [...], "unread": n}, "unplanned": {"share", "human", "agent"}, "assumptions": [...]}`.

## Calibration report

```markdown
🎯 `mk-estimate --calibrate` — window {from}..{to}: human clock ×{factor} ({n} evidence points), agent clock ×{factor} ({n}). {Proposed change in one line, or "no change — not enough evidence".} Confidence: {high|medium|low}.
{Scope: baselines read/skipped, items finished, unplanned work, evidence sources per clock, approx items, capacityUsed.}

| Size | Clock | Items | Estimated h | Actual h | Factor | Current → proposed |
|---|---|---|---|---|---|---|
| {S} | {human} | {n} | {h} | {h} | {x} ({median|global}) | {h} → {h} |

📋 Buffer check: {pct}% of items exceeded estimate + buffer → {keep | raise to … | lower to …}.
⚠️ Sizing, not hours: {size → items}
⚠️ Unplanned work: {n} items, {pct}% of the window — re-estimate with `--remaining`

Proposed diff for `.ai/estimate.config.json` (apply by hand, then append a `calibration.history` entry):

~~~json
{ "hours": { "mvp": { "{size}": { "{clock}": {value} } } } }
~~~

<details><summary>Evidence per item ({n})</summary>

| Item | PR | Size | Est. human / agent | Actual human / agent | Source |
|---|---|---|---|---|---|

</details>

🔁 Next: apply the diff, then `mk-estimate --target {target} --remaining`
```

Omit the ⚠️ lines when they do not fire. A calibration states how the tables compare with delivery, never how well people performed.
