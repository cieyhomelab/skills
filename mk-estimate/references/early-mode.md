# Early mode — interview and item derivation

The interview `mk-estimate` runs in step 2 when there is no backlog (`--mode early`, or no agentic config). Ask all six questions in one message, never one at a time; then derive items from the answers with the table below.

| Question | Items it adds (MVP) | POC |
|---|---|---|
| 1. User roles? | 1 S per role (access, panel) | 1 S total |
| 2. Key user flows (end-to-end)? | 3 M per flow | only the top 1–2 flows |
| 3. Screens outside those flows? | 1 S per screen | 0 |
| 4. External integrations? | 1 L per integration | 1 S per integration (mocked) |
| 5. Risk areas (permissions, payments, scoring, audit)? | 1 L per area | 1 M per area |
| 6. Core data entities? | 1 S per entity (CRUD) | 1 S per 2 entities |

- Epic count = number of flows + 1 (foundation).
- Derived items carry ids `X01`, `X02`, … and the question that produced them, so the report shows the derivation.
- Every one-time phase applies (nothing exists yet), and the early-mode buffer and ±40% range from `references/estimation-rules.md` apply.
- Confidence is always `low`; the next action is `om-discover` to turn the answers into a brief, then `om-backlog`.
- An early-mode estimate still writes its baseline block, but calibration skips its items (their ids never match tracker issues) and says so.
