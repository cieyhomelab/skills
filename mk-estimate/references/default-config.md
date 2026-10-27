# Default estimate configuration

The defaults `mk-estimate` falls back to when `.ai/estimate.config.json` is absent or a key is missing (step 1). Every key is optional; the report lists each value taken from here.

```json
{
  "team": { "devs": 1 },
  "sprint": { "days": 10, "focusHoursPerDay": 6, "firstStart": null },
  "agents": { "parallelPerDev": 3, "hoursPerDay": 14 },
  "poc": { "humanFactor": 0.5, "agentFactor": 0.6 },
  "hours": {
    "mvp": {
      "S": { "human": 2, "agent": 1,   "spec": 0.5 },
      "M": { "human": 4, "agent": 2.5, "spec": 1 },
      "L": { "human": 8, "agent": 5,   "spec": 3 }
    }
  },
  "finishing": { "agentShare": 0.25 },
  "buffer": { "poc": 0.20, "mvp": 0.30, "perBlockingQuestion": 0.15 },
  "calibration": { "minSamples": 5, "minSamplesGlobal": 3, "damping": 0.5, "clamp": [0.5, 2.0], "capacityUsed": 1.0, "history": [] },
  "tokens": { "inputPerAgentHour": 4000000, "outputPerAgentHour": 200000, "cachedShare": 0.9, "reviewOverhead": 0.15 },
  "models": {
    "coding":   { "id": "claude-sonnet-5-5", "effort": "medium", "share": 0.8 },
    "advanced": { "id": "claude-opus-5-5",   "effort": "high",   "share": 0.2 }
  }
}
```

The config holds **which** models are used, never their prices. Prices come from `references/model-prices.md` or the price interview (`references/cost-model.md`).

## Key notes

- `sprint.firstStart` (`YYYY-MM-DD`) anchors sprint windows for calibration; sprints are 14 calendar days.
- `hours.poc` may be added with the same shape; without it POC hours are MVP × the `poc` factors.
- `calibration.capacityUsed` < 1 discounts sprints with known absences (e.g. 0.8 for a holiday week). `calibration.history` holds `{ "date", "window", "factors" }` entries the user appends when applying a diff; the skill only reads it to show the trend.
- Model defaults follow the course model tiers: coding at the standard tier, specs and architecture at the advanced tier. Swap `models.coding.id` for `gpt-6-1-sol` (`reasoning: medium`) to price an OpenAI coding tier; the id must match a key in `references/model-prices.md`, or the price interview runs.
