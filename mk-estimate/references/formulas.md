# Formulas

This file gives the formulas of `scripts/estimate.py estimate`. Step 7 uses this file only when `python3` cannot run. If this file and the script do not agree, the script is correct. All values come from the estimate config and the default config.

## Hours of a work item

1. Get the hours for the size from `hours.<target>.<size>`.
2. If `hours.poc` is `null`, the POC hours are: human = MVP human × `poc.humanFactor`, agent = MVP agent × `poc.agentFactor`, spec = MVP spec × `poc.humanFactor`.
3. An XL work item that is in flight uses the L hours.
4. In-flight work item: human = human − spec. Agent = `finishing.agentShare` × agent.
5. Fix, or a work item with a merged spec PR: human = human − spec. Agent = agent.
6. All other work items: human = human. Agent = agent.

## Hours of a phase

1. Phase human hours = `phases.<name>.<target>`.
2. Phase agent hours = phase human hours × `phases.agentShare.<name>`. If the key is missing, the agent hours are 0.
3. Per-epic human hours = `phases.perEpic.<target>` × the number of open epics. Per-epic agent hours are 0.

## Buffers and allowance

Calculate each line for the human hours and for the agent hours separately.

1. Subtotal = the sum of the work items + the sum of the phases.
2. Base buffer = (`buffer.<target>` + `buffer.earlyExtra` in early mode) × subtotal.
3. Scoped question = `buffer.perBlockingQuestion` × the sum of the hours of the ids that it blocks.
4. Unscoped question = `buffer.perUnscopedQuestion` × subtotal.
5. After buffer = subtotal + base buffer + the sum of all questions.
6. Unplanned allowance = `unplanned.share` × after buffer. If the share is `null` or `--epic` is set, the allowance is 0.
7. Total = after buffer + unplanned allowance.
8. In early mode, the range is total × (1 − `buffer.earlyRange`) to total × (1 + `buffer.earlyRange`).

## Calendar

1. Human capacity = `sprint.days` × `sprint.focusHoursPerDay` × devs.
2. Agent capacity = `agents.parallelPerDev` × `agents.hoursPerDay` × `sprint.days` × devs.
3. Sprints = the next integer above the larger of human total ÷ human capacity and agent total ÷ agent capacity. The minimum is 1.
4. The binding clock is the clock with the larger ratio.
5. Dependency floor in days = the sum of the agent hours of the chain ÷ `agents.hoursPerDay`.
6. If the floor needs more sprints than step 3 gives, use the floor. Then the binding clock is "dependency".

## Cost

1. Input tokens = agent total × `tokens.inputPerAgentHour` × (1 + `tokens.reviewOverhead`).
2. Output tokens = agent total × `tokens.outputPerAgentHour` × (1 + `tokens.reviewOverhead`).
3. For each tier in `models`, use its `share` of the tokens.
4. Cached input = the input tokens of the tier × `tokens.cachedShare`. Uncached input = the remaining input tokens.
5. Tier cost = (cached × `cachedInput` + uncached × `input` + output × `output`) ÷ 1,000,000.
6. API cost = the sum of the tier costs. If a tier has no price, the API cost is `not configured`.
7. Months = the next integer above sprints × `sprint.days` ÷ 20.
8. Subscription cost = devs × months × seat price.
