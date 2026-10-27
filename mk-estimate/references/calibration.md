# Calibration (`--calibrate`)

The procedure `mk-estimate` runs in step 9: compare earlier estimates with work delivered in a window and propose corrected `hours` (and buffer) for `.ai/estimate.config.json`. It writes a calibration report and never the config.

## Procedure

1. **Load baselines.** Read every `${SPECS_DIR}/estimates/*.md` (filtered by `--target`) and parse its `mk-estimate-baseline` block (`references/report-templates.md`). Keep, per item id, the most recent baseline dated before the item's implementation PR was opened. Files without the block are listed as skipped.
2. **Resolve the window.** `--window` when given; else sprint *n* = `sprint.firstStart` + (n − 1) × 14 calendar days, taking the last sprint that has ended; else the last 14 calendar days, stated in the header.
3. **Collect finished items.** **list-prs** merged within the window; keep implementation PRs that close an item present in a baseline. Items closed as not planned are excluded. Items delivered in the window but absent from every baseline are *unplanned work* — count them, and their human hours when known.
4. **Measure agent hours per item** — first source that yields a value wins, recorded per item:
   1. `.ai/runs/` entries whose metadata names the issue or PR: sum of (end − start) over the item's `om-auto-*` runs;
   2. Cezar cockpit runs-index rows matched by `issueNumber` / `prNumber`, when a cockpit URL is configured for the run;
   3. fallback: first commit → last commit before the first review on the implementation PR (**get-pr**), marked `approx`.
5. **Measure human hours** with the *Human time* table below.
6. **Compute factors** with the *Calibration rules* below, per clock (human, agent), per size, and per target.
7. **Report and save** with the calibration template in `references/report-templates.md` to `${SPECS_DIR}/estimates/calibration-{YYYY-MM-DD}.md` (never overwrite). The proposed change is a JSON diff of `hours` (and `buffer` when the buffer check fires) only.
8. **Hand off.** Tell the user to apply the diff by hand and append a `calibration.history` entry; the next estimate picks the new values up. When a factor is outside the clamp, the next action is re-sizing with `om-backlog`, not new hours.

## Human time

Evaluate top to bottom; first match wins for each item.

| # | Source | When | Granularity |
|---|---|---|---|
| 1 | `human-hours: <number>` line in the implementation PR body or in a PR comment by its author (spec PR value added when present) | present | per item |
| 2 | Sprint capacity = `sprint.days` × `sprint.focusHoursPerDay` × devs × `calibration.capacityUsed` | the window covers whole sprints | per sprint |
| 3 | — | neither applies | item excluded from the human clock, counted as *no human evidence* |

Validate `human-hours` against `^[0-9]{1,3}(\.[0-9])?$`; anything else is ignored and reported. Sprint attribution compares capacity with the estimated human hours of everything finished in the sprint — items **plus** one-time phases and per-epic overhead whose artifacts first appeared in the window; items with a per-item value are subtracted from both sides first.

## Calibration rules

- **Ratio per item** = actual ÷ estimated hours from its baseline (`hoursUsed`, buffer excluded). An item that was `inFlight` in its baseline is compared on its finishing hours and counted toward `finishing.agentShare`, never toward a size factor. **Ratio per sprint** = capacity ÷ estimated hours of the sprint's finished work.
- **Factor per size** = median of the item ratios for that size and target, used only when the size has at least `calibration.minSamples` (5) items with evidence. Below that, all sizes of that clock share one **global factor**: the hours-weighted mean of every ratio, sprint ratios included. Below `calibration.minSamplesGlobal` (3) evidence points in total, propose nothing for that clock and say so.
- **Damping:** proposed = current × (1 + `calibration.damping` × (factor − 1)), default damping 0.5; round to 0.5 h.
- **Clamp:** a factor outside `calibration.clamp` (default [0.5, 2.0]) is not applied; report it as ⚠️ "sizing, not hours" with the items that drove it.
- **Spec share** scales with the human factor of its size.
- **`approx` agent hours** count with weight 0.5 in every mean and never alone satisfy `minSamples`.
- **Buffer check:** the share of items whose actual exceeded estimate × (1 + base buffer). Above 30% → propose +10 points on the base buffer; below 10% → propose −5 points. A separate line in the diff.
- **Unplanned work** — hours of items delivered in the window that were in no baseline (neither backlog item nor included off-backlog issue), as a share of all delivered hours in the window. Propose it as `unplanned.share` in the diff (damped like the hours, rounded to 0.05; needs at least `calibration.minSamplesGlobal` windows or 3 unplanned items, otherwise report it without proposing). Above 20% also add ⚠️ "scope grew outside the backlog — re-run the estimate with `--remaining`".

## Confidence

- `high` — per-size factors on both clocks from non-`approx` evidence.
- `medium` — a global factor on at least one clock.
- `low` — any clock with no proposal.
