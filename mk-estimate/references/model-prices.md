# Model price catalog

The price list `mk-estimate` reads in step 6 when `--prices ref` (the default) is in effect. It ships with the skill; update it by editing this file and its `asOf` date — the skill never refreshes it from the web.

```json
{
  "currency": "USD",
  "asOf": "2026-10-27",
  "unit": "per 1M tokens",
  "models": {
    "claude-sonnet-5-5": { "input": 2.00, "cachedInput": 0.10, "cacheWrite5m": 2.50, "output": 10.00 },
    "claude-opus-5-5":   { "input": 4.00, "cachedInput": 0.20, "cacheWrite5m": 5.00, "output": 20.00 },
    "gpt-6-1-sol":       { "input": 2.00, "cachedInput": 0.20, "output": 10.00 },
    "gpt-6-luna":        { "input": 0.10, "cachedInput": 0.01, "output": 0.50 }
  },
  "seats": {
    "team-premium-monthly": 125,
    "team-premium-annual":  100,
    "max-5x":               100
  },
  "defaultSeat": "team-premium-monthly"
}
```

## Notes

- Claude prices are standard API rates (Opus 5.5 after the 2026-10-05 cut; Sonnet 5.5 at the Sonnet 5 rate). Fast mode and batch pricing are not listed.
- `gpt-6-1-sol.cachedInput` is assumed equal to GPT-6 Sol's; GPT-6 rates apply to prompts up to 272K input tokens.
- Seat prices are per developer per month. A solo developer running overnight loops may prefer a max-usage individual plan over a team seat.
- Verify against the vendors' official pricing pages before quoting an estimate to a client, then update `asOf`.
