# Cost model

How `mk-estimate` turns agent hours into model spend in step 6: first resolve the prices, then compute. This file never supplies a price itself.

## Price source

Resolve once per run; the source used is reported next to every cost line and saved in the baseline block.

| # | Source | When |
|---|---|---|
| 1 | **Interview** (below) | `--prices ask` |
| 2 | **Catalog** — `references/model-prices.md` | `--prices ref` (default), every model in `models` (estimate config) is listed there, and the catalog `asOf` is at most 90 days before the run date |
| 3 | **Interview**, catalog values offered as the suggested answers | `--prices ref`, but a model is missing from the catalog or the catalog is older than 90 days — say which condition sent you here |
| 4 | `not configured` on the cost lines | the interview was skipped or left unanswered (unattended run) — the hours estimate still completes |

## Price interview

Ask all questions in one message, with the catalog values as suggested defaults so the user can confirm with a single reply. When the early-mode interview also runs, append these questions to that same message instead of asking twice:

1. **Billing model** — API, subscription, or both?
2. **Models** — which coding-tier and which advanced-tier model, and what share of agent work each takes? (Default: `models` from the estimate config, 80% / 20%.)
3. **API prices** (API or both) — for each chosen model: input, cached input, and output price per 1M tokens, and the currency.
4. **Subscription** (subscription or both) — plan and price per developer per month.

Validate every price as a non-negative number (`^[0-9]+(\.[0-9]{1,4})?$`) and shares as fractions summing to 1; re-ask only the invalid answer. Answers apply to this run only: they are recorded in the report header and the baseline block (`"prices": {"source": "interview", ...}`), never written to the catalog or the config. To keep them, the user edits `references/model-prices.md` (or a repo-local override of it).

## API cost

1. Tokens per agent hour: `tokens.inputPerAgentHour` (default 4M) input and `tokens.outputPerAgentHour` (default 0.2M) output, then + `tokens.reviewOverhead` (default 15%) for cross-model review.
2. Of the input, `tokens.cachedShare` (default 0.9) is billed at the cached-input price, the rest at the base input price.
3. Split the total by the `share` of each tier in `models` (default 80% `coding`, 20% `advanced`), or by the shares from the interview.
4. Cost per tier = cached input × `cachedInput` + uncached input × `input` + output × `output`, all per 1M tokens.
5. A tier without a price → that line reads `not configured`; the total is reported only when every tier is priced.

## Subscription cost

Months = ceil(sprints × `sprint.days` / 20). Cost = devs × months × seat price (catalog `seats[defaultSeat]`, or the interview answer).

## Reference figures

With the catalog as shipped, one agent hour costs about $3.16 on the coding tier, $6.32 on the advanced tier, and **$4.36** for the 80/20 mix with review overhead. Use these only to sanity-check a computed total, never in place of the computation.
