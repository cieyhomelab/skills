# Default config

This file gives the default value of each key in the estimate config. Step 0 uses it for each key that the estimate config does not set. The script `scripts/estimate.py` reads the JSON block below. Do not keep a second copy of these numbers in a different file.

```json
{
  "team": { "devs": 1 },
  "sprint": { "days": 10, "focusHoursPerDay": 6, "firstStart": null },
  "agents": { "parallelPerDev": 3, "hoursPerDay": 14 },
  "hours": {
    "mvp": {
      "S": { "human": 2, "agent": 1,   "spec": 0.5 },
      "M": { "human": 4, "agent": 2.5, "spec": 1 },
      "L": { "human": 8, "agent": 5,   "spec": 3 }
    },
    "poc": null
  },
  "poc": { "humanFactor": 0.5, "agentFactor": 0.6 },
  "finishing": { "agentShare": 0.25 },
  "phases": {
    "setup":        { "poc": 4, "mvp": 8 },
    "discovery":    { "poc": 6, "mvp": 12 },
    "backlog":      { "poc": 2, "mvp": 4 },
    "designSystem": { "poc": 0, "mvp": 8 },
    "prototype":    { "poc": 4, "mvp": 8 },
    "perEpic":      { "poc": 1, "mvp": 3 },
    "agentShare":   { "setup": 0.25, "discovery": 0.25 }
  },
  "buffer": { "poc": 0.20, "mvp": 0.30, "earlyExtra": 0.15, "earlyRange": 0.40, "perBlockingQuestion": 0.50, "perUnscopedQuestion": 0.15 },
  "unplanned": { "share": null },
  "calibration": { "minSamples": 5, "minSamplesGlobal": 3, "damping": 0.5, "clamp": [0.5, 2.0], "capacityUsed": 1.0, "history": [] },
  "tokens": { "inputPerAgentHour": 4000000, "outputPerAgentHour": 200000, "cachedShare": 0.9, "reviewOverhead": 0.15 },
  "models": {
    "coding":   { "id": "claude-sonnet-5-5", "effort": "medium", "share": 0.8 },
    "advanced": { "id": "claude-opus-5-5",   "effort": "high",   "share": 0.2 }
  },
  "seat": "team-premium-monthly"
}
```

## Notes on the keys

1. `sprint.firstStart` is a date in the form `YYYY-MM-DD`. The calibration uses it to find the sprint windows. A sprint has 14 calendar days.
2. `hours.poc` is `null` by default. Then the POC hours are the MVP hours multiplied by the `poc` factors.
3. `unplanned.share` is `null` until a calibration measures it. The user copies the value from the calibration diff.
4. `calibration.capacityUsed` is less than 1 when the team was absent for part of a sprint. Example: use 0.8 for a sprint with holidays.
5. `calibration.history` contains one entry for each applied calibration diff: `{ "date", "window", "factors" }`. The user adds the entry. The skill only reads it.
6. `models` gives the models that the agents use, not their prices. Each `id` must be a key in the price catalog. If an `id` is not in the catalog, the skill asks for the price.
7. `seat` is a key in the `seats` table of the price catalog.
