# Price source

This file tells how to select the source of the prices and how to ask the user for prices. Step 6 uses it.

## Select the source

Use the first row that matches. Give the source in the report.

| # | Source | Condition |
| --- | --- | --- |
| 1 | Interview | `--prices ask` is set. |
| 2 | Interview, with the catalog values as the proposed answers | One or more `models.*.id` values in the config are not in the price catalog. Or the `asOf` date of the catalog is more than 90 days before today. Give the reason in the report. |
| 3 | Price catalog | All other conditions. |
| 4 | None | The user did not answer the interview. Example: a run without a user. Set `"prices": "none"` in the input file. |

1. If the source is the price catalog, do not put `prices` in the input file. The script reads the catalog.
2. If the source is None, the cost lines show `not configured`. The hours and the sprints are still correct.
3. Do not get prices from the web during a run. A stable result is more important than a new price.

## Price interview

Ask all questions in one message. Give the catalog values as the proposed answers. Then the user can agree with one reply.

1. Which billing do you use: API, subscription, or both?
2. Which model does the coding work, and which model does the advanced work? What share of the agent work does each model do? The proposed answer is the `models` section of the config.
3. If you use the API: for each model, what are the input price, the cached input price, and the output price for 1M tokens? Which currency?
4. If you use a subscription: what is the plan, and what is its price for one developer for one month?

## Validate the answers

1. Each price must match `^[0-9]+(\.[0-9]{1,4})?$`.
2. The shares must add up to 1.
3. If an answer is not valid, ask only that question again.

## Use the answers

1. Put the answers in the input file as `prices`, in the shape that the script input file gives.
2. The answers apply only to this run.
3. Do not write the answers to the price catalog or to the estimate config.
4. To keep the answers for later runs, the user edits the price catalog.
