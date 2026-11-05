# Branch: Layout and Theme

This file tells how to change positions, sizes, and the report theme. Step 9 uses it for the change type `layout-theme`.

## Layout

1. Change only `position` in each `visual.json`. Do not change the other parts of the visual.
2. Apply the position rules in `references/change-new-visual.md`.
3. To align visuals, give them the same `x` or the same `y`.
4. To give visuals the same size, give them the same `width` and `height`.
5. To change the page size, change `width` and `height` in `page.json`. Then make sure that all visuals are inside the new size.
6. After the change, run `python scripts/inspect_report.py -- <report definition>`. Read the layout warnings.
7. Set the change status to `done` in the plan file.

## Theme

The report theme is in `report.json`, in `themeCollection`. A custom theme is a JSON file in `StaticResources/RegisteredResources/`.

1. Read `themeCollection.customTheme.name` in `report.json`.
2. If the report has no custom theme, set the change status to `blocked`. Ask the user to make one in Power BI Desktop: **View > Themes > Customize current theme**. Then the skill can edit it.
3. Find the theme file path in the `resourcePackages` list of `report.json`. Use the item that has the name from step 1.
4. Change only the keys that the plan gives. Examples: `dataColors`, `background`, `foreground`, `tableAccent`.
5. Write colors as `#RRGGBB`.
6. Do not change `themeCollection.baseTheme`.
7. Set the change status to `done` in the plan file.

CAUTION: A theme change affects all pages. Name all pages in the plan as "affected".
