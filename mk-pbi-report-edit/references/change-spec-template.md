# Change Spec Template

This file gives the template of a change spec. Step 1 uses it when the request has more than 3 changes or more than 1 page.

## Procedure

1. Copy the template below to `<report folder>/pbi-edit-spec-<timestamp>.md`.
2. Fill the parts of the template that the request already gives.
3. Tell the user the path of the file.
4. Ask the user to fill the empty parts.
5. Tell the user to start the skill again with the path of the change spec as `{request}`.
6. Stop.

## Template

```markdown
# Change spec: <report name>

Make one section for each change. Delete the lines that you do not need.

## Change 1

- Type: new-page | new-visual | edit-visual | filter-slicer | layout-theme
- Page: <display name of the page; for a new page, the new name>
- Visual: <title of an existing visual, or "new">
- Visual type: <example: clusteredColumnChart, tableEx, cardVisual, slicer>
- Fields: <role = Table[Name]; example: Category = Product[Category]; Y = Sales[Total Sales]>
- Position: <auto | x, y, width, height | example: "right of the KPI cards">
- Title: <text, or "none">
- Format: <colors, data labels, sort order>
- Filter: <level (report | page | visual), field, values>
- Notes: <other information>

## Change 2

- Type:
```
