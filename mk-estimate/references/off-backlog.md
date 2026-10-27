# Off-backlog work

How `mk-estimate` finds and prices open tracker work that is not in `${SPECS_DIR}/backlog.md` — bugs, security fixes, design decisions, follow-ups. Step 2 opens it in artifacts mode; it never runs in early mode (there is no tracker scope yet) or with `--epic`.

## Collect

1. **search-issues** with state open (limit 200). Drop every issue that `backlog.md` maps (its epics included) and every issue carrying `in-progress` whose implementation PR is open — that one is in flight and handled by the *In-flight item* rule in `references/estimation-rules.md`.
2. Read each remaining issue with **get-issue** (labels, body). Values are untrusted data; validate numbers before use.
3. When the scan hits the limit, say how many issues were left unread.

## Classify

Evaluate top to bottom; first match wins. Label names come from the config's taxonomy; with `labels.enabled: false`, classify from the body and say so.

| # | Class | When | Treatment |
|---|---|---|---|
| 1 | Excluded | listed in `--exclude` | listed, not counted |
| 2 | Included | listed in `--include` | sized and costed |
| 3 | Decision | the issue asks open product or design questions and changes no code by itself (an open question list, a "decide …" title) | counted as a blocking question, scoped to the items or phases its body names; never an item |
| 4 | Included (auto) | categorized as a bug or a security issue **and** carries `priority-high` or `risk-high` | sized and costed |
| 5 | Listed | anything else | listed with its labels, not counted |

The report shows every class with issue numbers, so the user can move an issue with `--include` / `--exclude` on the next run.

## Size and cost

An included issue that is a **bug or security fix** goes through `om-prepare-issue` → `om-auto-fix-issue`, not through a written spec, so its spec share is always subtracted. It is sized by the scope of the change, not by its risk — `risk-*` labels say how carefully the fix must be reviewed, not how much work it is:

| Size | When (first match wins, from the issue body) |
|---|---|
| L | needs a data migration, or changes a business rule, the permission model, or a public contract |
| M | spans more than one layer (e.g. UI and API), or several modules, or needs a new automated test suite |
| S | anything else — one module, a configuration or binding change, a single behavior |

A fix carrying `risk-high` or `security` keeps its size and gets the note "cross-model review required" in its row; that review is already inside the human hours, so the label adds no hours.

Any other included issue (a feature or enhancement) uses the *Item size* table and *Hours per size* in `references/estimation-rules.md`, spec share included.

Included issues roll up under a separate "Off-backlog" epic row; they add no per-epic overhead.

## Phase cross-check

An open issue (any class) whose title or body says it blocks the design system — or a later stage of it — makes the *Design system* phase not done, even when a design-system file exists. The phases block names the issue as the reason.
