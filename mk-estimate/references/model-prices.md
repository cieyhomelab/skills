# Price catalog

This file contains the model prices and the seat prices. Step 6 uses it when `--prices ref` is set. The script `scripts/estimate.py` reads the JSON block below.

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
  }
}
```

## Notes

1. The Claude prices are standard API prices. The catalog does not contain the prices for fast mode or batch mode.
2. The `cachedInput` value of `gpt-6-1-sol` is an assumption. It is equal to the value of GPT-6 Sol.
3. The GPT-6 prices apply to prompts with a maximum of 272K input tokens.
4. A seat price is the price for one developer for one month.
5. To change a price, edit the JSON block and change `asOf` to the date of the change.
6. Before you give an estimate to a client, compare the prices with the official price pages of the vendors.
