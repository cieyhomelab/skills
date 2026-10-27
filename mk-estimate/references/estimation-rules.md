# Estimation rules

The deterministic tables `mk-estimate` applies in steps 2–6: scope per target, item size, hours per size, one-time phases, buffer, and calendar. First match wins in every table. Values in `.ai/estimate.config.json` override the defaults named here; the report lists every default that was used.

## Targets

| Target | Scope | Pipeline per item | Excluded |
|---|---|---|---|
| `poc` | POC epics of the *Now* scope; happy path only | `om-auto-write-spec` → `om-auto-implement-spec` → one cross-model review → merge | QA gate, design system, full UI states, non-happy paths |
| `mvp` | the whole *Now* scope | spec by size → merge spec → `om-auto-implement-spec` → `om-auto-review-pr` + cross-model review → `om-auto-fix-pr` → `om-auto-qa-pr` + manual QA → merge | the parked *Later* epic |

**POC scope selection (artifacts mode).** Keep the epics the brief's *Now* scope marks as POC. When the brief marks none, keep the first two epics in backlog order and say so in the header.

**Finished item (`--remaining`).** An item is finished when its issue is closed as completed (with or without a merged implementation PR) or closed as not planned. Read the state with **get-issue**; an unreadable state counts as unfinished and is reported.

**In-flight item.** An unfinished item whose implementation PR is open (found with **search-prs**) is in flight. It is not re-sized and never listed under *Split first* — the split decision was already taken by building it. It is costed with the *Finishing* rule under *Hours per size* and marked `in flight` in the report. This applies with or without `--remaining`.

## Item size

Evaluate top to bottom; first match wins. Inputs: issue labels, body, acceptance criteria, linked spec. In-flight items keep the size this table gives them only to look up their finishing hours; an in-flight XL is costed as L and the row says so.

| Size | When |
|---|---|
| XL | touches more than one role **and** the data model **and** an external integration, or has more than 5 acceptance criteria that define business rules |
| L | carries `risk-high`, or touches permissions/auth, audit, scoring or business rules, the data model, or payments |
| M | business logic beyond CRUD, or 1–2 new screens, or one external integration, or 3–5 acceptance criteria |
| S | CRUD, list view, settings, copy/config change, or carries `risk-low` |

Each item row in the report names the rule that matched ("Why (rule)").

## Hours per size

Human hours = spec review + cross-model review + fixes + manual QA + merge. Agent hours = autonomous wall clock. Config keys: `hours.{mvp|poc}.{S|M|L}.{human|agent|spec}`.

| Size | Spec route | MVP human h | MVP agent h | Spec share of human h |
|---|---|---|---|---|
| L | `om-spec-writing` (interactive) + grill-me | 8 | 5 | 3 |
| M | `om-auto-write-spec` + human review | 4 | 2.5 | 1 |
| S | `om-auto-write-spec` | 2 | 1 | 0.5 |

POC without its own `hours.poc` keys: MVP human × `poc.humanFactor` (0.5), MVP agent × `poc.agentFactor` (0.6). A merged spec PR subtracts the spec share from human hours.

**Finishing (in-flight items).** Human = size human − spec share (review, fixes, QA, merge remain); agent = `finishing.agentShare` (default 0.25) × size agent (fix and re-review loops). Example: an in-flight L costs 5 h human and 1.25 h agent.

## One-time phases

| Phase | Human h POC | Human h MVP | Already done when (`--remaining`) |
|---|---|---|---|
| Setup + CI safety net | 4 | 8 | `VALIDATION_COUNT` > 0 and the latest CI run on the base branch passed |
| Discovery + product brief | 6 | 12 | `product-brief.md` exists |
| Backlog | 2 | 4 | `backlog.md` has a section for the brief |
| Design system | 0 | 8 | a design-system file exists under `${SPECS_DIR}` or the repo's design path **and** no open issue says it blocks the design system (`references/off-backlog.md`, *Phase cross-check*) |
| Prototype | 4 | 8 | `${PROTOTYPES_DIR}` has a prototype for every key flow |
| Per epic (status, decisions, new-screen prototype) | 1 × epics | 3 × epics | counted only for epics with at least one unfinished item |

Setup and discovery also consume agent time: add 25% of their human hours to the agent clock. With `--epic`, every one-time phase except the per-epic row is excluded.

Open blocking questions never re-open the discovery phase once the brief exists: their cost is carried by the buffer alone (next section), so a question is never paid for twice.

## Buffer

The buffer has two parts, reported as two rows.

**Base buffer** — on the whole subtotal (phases + items + in flight + off-backlog), human and agent separately:

| Target | Base buffer (`buffer.poc` / `buffer.mvp`) |
|---|---|
| `poc` | +20% |
| `mvp` | +30% |

**Blocking-question buffer** — scoped to what each counted question blocks, never to the whole estimate:

- A question that names what it blocks adds `buffer.perBlockingQuestion` (default 50%) × the human and agent hours of exactly those items or phases. Example: a question blocking one L item adds 4 h human and 2.5 h agent; a question blocking the 8 h design-system phase adds 4 h human.
- Two questions blocking the same item each add their share.
- A counted question that names nothing (whole-scope estimates only, see below) adds `buffer.perUnscopedQuestion` (default 15%) × the subtotal, and the report flags it as unscoped.
- Decision issues found outside the backlog (`references/off-backlog.md`, class 3) count as blocking questions here, once each, scoped to the items or phases their body names.

In `early` mode, add a further +15% to the base buffer and report a range of ±40% around the result.

**Unplanned-work allowance.** When `unplanned.share` is set in the estimate config (it comes from a calibration diff, never from a default), add it as its own row after the buffer: allowance = share × (human and agent totals after buffer, separately). With `--epic` the allowance is skipped. Without a measured share the row is omitted and the header says "no unplanned-work allowance yet — run `--calibrate` after a sprint".

**Which blocking questions count.** A blocking open question in the brief counts when it blocks at least one item being estimated — the brief or the item names it, or the item's spec PR is held on it. A question that blocks only finished items, or names no item, counts only when the estimate covers the whole scope (no `--remaining`, no `--epic`). The report lists counted and uncounted questions with the reason for each.

## Calendar

- Human capacity per sprint = `sprint.days` × `sprint.focusHoursPerDay` × devs (default 10 × 6 = 60 h per FTE; Agile ceremonies already excluded).
- Agent capacity per sprint = `agents.parallelPerDev` × `agents.hoursPerDay` × `sprint.days` × devs (default 3 × 14 × 10 = 420 h per FTE — three worktrees by day plus overnight runs).
- Sprints = ceil(max(human h / human capacity, agent h / agent capacity)); the larger ratio is the binding clock and is named in the report.
- **Dependency floor:** the longest `Depends on:` chain × the average agent hours of its items, in days, is a lower bound on calendar time. When it exceeds the sprint figure, report the floor instead and say why.

## Confidence

- `high` — artifacts mode, no XL, no `assumed` sizes, no blocking questions.
- `medium` — artifacts mode with any of those.
- `low` — early mode, or any XL left unsplit (an in-flight XL does not count).
