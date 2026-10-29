# Script input

This file gives the exact shape of the input files for `scripts/estimate.py`. Step 7 uses the estimate shape. Step 10 uses the calibration shape. Use exactly these structures. The script stops with exit code 2 and a specific message if a value is not valid.

## Estimate input

```json
{
  "target": "mvp",
  "mode": "artifacts",
  "devs": 1,
  "epicScoped": false,
  "workItems": [
    { "id": "#29", "size": "L" },
    { "id": "#32", "size": "XL", "inFlight": true },
    { "id": "#40", "size": "M", "specMerged": true },
    { "id": "#10", "size": "S", "fix": true, "offBacklog": true }
  ],
  "phasesToDo": ["designSystem"],
  "openEpics": 2,
  "blockingQuestions": [
    { "id": "Q14", "blocks": ["#30"] },
    { "id": "#50", "blocks": ["phase:designSystem"] },
    { "id": "Q12", "blocks": [] }
  ],
  "chain": ["#32", "#33"],
  "prices": null
}
```

| Key | Value |
| --- | --- |
| `target` | `poc` or `mvp`. |
| `mode` | `artifacts` or `early`. |
| `devs` | The value of `--devs`. |
| `epicScoped` | `true` if `--epic` is set. Then the script does not add the unplanned allowance. |
| `workItems[].id` | The tracker issue number with `#`, or `X01` in early mode. |
| `workItems[].size` | `S`, `M`, `L`, or `XL`. |
| `workItems[].inFlight` | `true` for an in-flight work item. |
| `workItems[].specMerged` | `true` if the work item has a merged spec PR. |
| `workItems[].fix` | `true` for a bug fix or a security fix. |
| `workItems[].offBacklog` | `true` for an included off-backlog issue. |
| `phasesToDo` | The phases that are not done: `setup`, `discovery`, `backlog`, `designSystem`, `prototype`. |
| `openEpics` | The number of epics that have at least one work item that is not finished. |
| `blockingQuestions[].blocks` | The ids of the work items and the phases (`phase:<name>`) that the question blocks. An empty list means an unscoped question. |
| `chain` | The ids of the longest open `Depends on:` chain, in sequence. |
| `prices` | Omit it or set `null` for the price catalog. Set `"none"` if there are no prices. Else give the interview answers in the shape below. |

Shape of the interview prices:

```json
{
  "currency": "EUR",
  "models": {
    "claude-sonnet-5-5": { "input": 2.0, "cachedInput": 0.1, "output": 10.0 }
  },
  "seatPrice": 125,
  "seat": "team-premium-monthly"
}
```

## Calibration input

```json
{
  "target": "mvp",
  "items": [
    { "id": "#29", "size": "L", "humanEstimated": 8, "humanActual": 6, "agentEstimated": 5, "agentActual": 3.5, "questionHours": 0 },
    { "id": "#10", "size": "S", "humanEstimated": 1.5, "humanActual": null, "agentEstimated": 1, "agentActual": 0.6, "approx": true },
    { "id": "#32", "size": "L", "inFlight": true, "humanEstimated": 5, "humanActual": 4, "agentEstimated": 1.25, "agentActual": 2 }
  ],
  "sprints": [
    { "capacity": 60, "estimated": 52 }
  ],
  "unplanned": { "hours": 6, "deliveredHours": 40, "items": 2, "windows": 1 }
}
```

| Key | Value |
| --- | --- |
| `items[].size` | The costed size from the baseline block: `S`, `M`, or `L`. |
| `items[].*Estimated` | The hours of the work item in its baseline block, without the buffers. |
| `items[].*Actual` | The measured hours. Set `null` if there is no evidence. |
| `items[].approx` | `true` if the agent hours come from the commit-span fallback. |
| `items[].inFlight` | `true` if the work item was in flight in its baseline block. |
| `items[].questionHours` | The question buffer that the baseline block gave to this work item. |
| `sprints[]` | One entry for each whole sprint in the window. `capacity` already includes `capacityUsed`. `estimated` is the estimated human hours of the work that finished in the sprint. Remove the work items that have their own `human-hours` value from both numbers. |
| `unplanned` | The hours of delivered work that no baseline block contains, the total delivered hours, the number of these work items, and the number of windows. |
