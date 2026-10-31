# UX coverage

This file gives the procedure to measure the UX coverage. Step 4 uses it.

## Contents

- Browser
- Make the UX inventory
- Find the screens of the project application
- Match the inventory
- UX inventory format

## Browser

1. Read the browser descriptor `.ai/browsers/<provider>.md`. The provider is `browser.provider` in the config. The default is `agent-browser`.
2. Do each browser operation as the descriptor defines it: `ensure-installed`, **open**, **snapshot**, **interact**, **screenshot**, **close**.
3. If the descriptor is missing, do not use a browser. Write a line in `coverage`.
4. Use **interact** only to open links, tabs, and menus. Do not submit forms. Do not click buttons that save, delete, or send data.
5. If a page asks for a sign-in, stop on that page. Do not type credentials.
6. Tell the user which pages need a sign-in. The user can add these screens to the UX inventory by hand.
7. Do **close** at the end of this step.

## Make the UX inventory

Do this part only if `${BENCH}/ux-reference.md` is missing. If the file exists, use it and go to the next part.

1. Do **open** on the reference URL. Do **snapshot**.
2. Collect the links of the main navigation. Use only the links on the same host.
3. Open each link to a maximum depth of 2. Stop after 30 pages.
4. For each page, write one screen. Write its path, its main heading, and its main actions.
5. If two pages show the same screen with a different record, write one screen. Example: `/orders/12` and `/orders/13`.
6. Write the flows. A flow is a sequence of screens for one user goal. Example: "Sign in, open the list, open a record".
7. Write a maximum of 10 flows. Use the goals that the main navigation shows.
8. Do **screenshot** of each screen. Save the images in `${BENCH}/ux-reference/`.
9. Write the UX inventory in the format below.
10. Show the inventory to the user. Ask the user to remove, add, or change screens and flows.
11. Continue only after the user confirms the inventory.

## Find the screens of the project application

1. If `--ux-app` is set, do **open** on that URL. Collect the screens with the procedure of the part above.
2. If `--ux-app` is not set, or the application does not open, read the routes from the code.
3. To read the routes, find the route and page files. Examples: `app/**/page.tsx`, `pages/**`, `routes/**`, a router config.
4. For each route, read the main heading and the main actions from the code.
5. Write the method in the snapshot: `browser` or `code`.

## Match the inventory

For each screen and flow of the UX inventory, give one status:

| Status | When |
| --- | --- |
| `present` | The project application has a screen or flow with the same user goal and the same main actions. |
| `partial` | The project application has the screen or flow, but one or more main actions are missing. |
| `missing` | The project application has no screen or flow for this user goal. |

1. Compare the user goal and the main actions. Do not compare colors, fonts, or layout.
2. A screen with a different name can be `present`. The user goal decides.
3. A flow is `present` only if each of its screens is `present` or `partial` and the flow can complete.
4. For each status, write the evidence. Write the route or the file path of the project application.
5. If the evidence is not sufficient, write `partial` and give the reason. Do not write `present` without evidence.

## UX inventory format

Use exactly this structure.

```markdown
# UX inventory

- Reference: https://example.com
- Made: 2026-10-31

## Screens

| Id | Name | Path | Main actions |
|---|---|---|---|
| R01 | Sign in | /login | sign in, reset password |

## Flows

| Id | Name | Screens |
|---|---|---|
| F01 | Submit a request | R01, R03, R04 |
```
