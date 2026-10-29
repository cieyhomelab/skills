# Estimation rules

This file gives the rules for steps 2, 4, and 5. The contents list below gives the topics. The hour values are not in this file. They are in the default config and the estimate config.

## Contents

1. Scope of each target
2. State of a work item
3. Size of a work item
4. One-time phases
5. Blocking questions
6. Confidence

## 1. Scope of each target

| Target | Scope | Pipeline for each work item | Not included |
| --- | --- | --- | --- |
| `poc` | The POC epics of the *Now* scope. Only the happy path. | `om-auto-write-spec` → `om-auto-implement-spec` → one review by a model of a different family → merge | QA gate, design system, all UI states, paths that are not the happy path |
| `mvp` | The full *Now* scope | Spec by size → merge the spec → `om-auto-implement-spec` → `om-auto-review-pr` and a review by a model of a different family → `om-auto-fix-pr` → `om-auto-qa-pr` and manual QA → merge | The parked *Later* epic |

1. For `poc`, keep the epics that the *Now* scope of the brief marks as POC.
2. If the brief marks no epic as POC, keep the first two epics in backlog order. Say this in the report.

## 2. State of a work item

1. A work item is finished if its tracker issue is closed as completed or closed as not planned.
2. A work item is in flight if it is not finished and it has an open implementation PR.
3. If you cannot read the state of a tracker issue, the work item is not finished. Say this in the report.
4. With `--remaining`, skip the finished work items.
5. Apply the in-flight rule with or without `--remaining`.

## 3. Size of a work item

Read the labels, the body, the acceptance criteria, and the linked spec. Use the first row that matches.

| Size | Condition |
| --- | --- |
| XL | It touches more than one role **and** the data model **and** an external integration. Or it has more than 5 acceptance criteria that define business rules. |
| L | It has the label `risk-high`. Or it touches permissions, authentication, audit, scoring, business rules, the data model, or payments. |
| M | It has business logic that is more than CRUD. Or it has 1–2 new screens, or one external integration, or 3–5 acceptance criteria. |
| S | It is CRUD, a list view, settings, or a change of text or configuration. Or it has the label `risk-low`. |

1. In each row of the report, give the condition that matched. Use the column "Why (rule)".
2. An in-flight work item keeps its size. If the size is XL, the script costs it as L. Say this in its row.
3. If `labels.enabled` is false, size from the issue body only. Say this in the report.

## 4. One-time phases

| Phase | Done when |
| --- | --- |
| `setup` | `VALIDATION_COUNT` is more than 0 and the last CI run on the base branch passed. |
| `discovery` | `${SPECS_DIR}/product-brief.md` exists. |
| `backlog` | `backlog.md` has a section for the brief. |
| `designSystem` | A design-system file exists in `${SPECS_DIR}` or in the design folder of the repository, **and** no open off-backlog issue says that it blocks the design system or a later stage of it. |
| `prototype` | `${PROTOTYPES_DIR}` has a prototype for each key flow of the brief. |

1. Without `--remaining`, put all phases in the input file.
2. With `--remaining`, put in the input file only the phases that are not done.
3. With `--epic`, put no phase in the input file. Count only the per-epic work.
4. Count the per-epic work only for the epics that have at least one work item that is not finished.
5. In the report, give the status of each phase and its evidence.
6. If the brief exists, an open blocking question does not make the `discovery` phase not done. The blocking question gets its cost from the question buffer.

## 5. Blocking questions

A blocking question comes from the *Open questions* of the brief, or from an off-backlog issue of the class "Decision".

1. Count a blocking question if it blocks at least one work item or phase in the estimate.
2. A question blocks a work item if the brief or the work item names it.
3. A question also blocks a work item if the spec PR of the work item waits for it.
4. For a counted question, list the ids of the work items and the phases that it blocks. Use the id `phase:<name>` for a phase.
5. If a question blocks only finished work items, do not count it.
6. If a question names no work item and no phase, count it only when the estimate covers the full scope. Then give it an empty list of blocked ids.
7. In the report, list the counted questions and the questions that you did not count. Give the reason for each.

## 6. Confidence

| Confidence | Condition |
| --- | --- |
| `high` | The mode is `artifacts`. There is no XL work item that is not in flight, no `assumed` size, and no blocking question. |
| `medium` | The mode is `artifacts`, and one of the `high` conditions is not true. |
| `low` | The mode is `early`, or an XL work item that is not in flight is in the split list. |
