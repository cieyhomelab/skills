# Early mode

This file gives the interview and the rules to make backlog items from the answers. Step 2 uses it when the mode is `early`.

## Interview

1. Ask all six questions in one message.
2. If step 6 also needs the price interview, add those questions to the same message.
3. Do not ask the questions one at a time.

## Backlog items from the answers

| Question | Backlog items for `mvp` | Backlog items for `poc` |
| --- | --- | --- |
| 1. Which user roles does the product have? | 1 S for each role (access and panel) | 1 S in total |
| 2. Which key user flows does the product have, from start to end? | 3 M for each flow | 3 M for each of the first 1–2 flows |
| 3. Which screens are not part of these flows? | 1 S for each screen | None |
| 4. Which external integrations does the product need? | 1 L for each integration | 1 S for each integration, with a mock |
| 5. Which risk areas does the product have? Examples: permissions, payments, scoring, audit. | 1 L for each area | 1 M for each area |
| 6. Which core data entities does the product have? | 1 S for each entity (CRUD) | 1 S for each 2 entities |

1. Give the ids `X01`, `X02`, and so on to the backlog items.
2. For each backlog item, write the question that made it.
3. The number of epics is the number of flows plus 1. The extra epic is the foundation.
4. Put all one-time phases in the input file. Nothing exists yet.
5. Set `"mode": "early"` in the input file. Then the script adds the early buffer and the range.
6. The confidence is `low`.
7. Give `om-discover` as the next action. Then give `om-backlog`.
8. The calibration skips the backlog items of an early estimate, because their ids are not tracker issues. Say this in the report.
