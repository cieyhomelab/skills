# PBIR Structure

This file gives the folder layout and the JSON shapes of a PBIR report. Step 0 loads it. All branch files use its terms.

## Contents

1. Folder layout
2. Names
3. The $schema field
4. Page files
5. Visual files
6. Field references
7. Literal values
8. Query roles
9. Copy rule

## 1. Folder layout

```
<report name>.Report/
├── definition.pbir
├── definition/
│   ├── version.json
│   ├── report.json                 report settings, theme, report filters
│   ├── reportExtensions.json       optional
│   ├── pages/
│   │   ├── pages.json              page order and active page
│   │   └── <page name>/
│   │       ├── page.json           page settings and page filters
│   │       └── visuals/
│   │           └── <visual name>/
│   │               └── visual.json
│   └── bookmarks/                  optional
└── StaticResources/
    ├── SharedResources/BaseThemes/
    └── RegisteredResources/        custom theme and images
```

1. Do not edit `version.json` or `definition.pbir`.
2. Do not edit files in a `.pbi` folder. Power BI Desktop writes them.

## 2. Names

- Each page and each visual has a `name` field. The folder name is equal to the `name` field.
- The `displayName` field of a page is the name that the user sees.
- Power BI Desktop makes names with 20 lowercase hexadecimal characters.

1. Make a new name with this command: `python -c "import secrets; print(secrets.token_hex(10))"`.
2. Make sure that the new name is unique in the report.

## 3. The $schema field

Each `page.json`, `visual.json`, `pages.json`, and `report.json` file has a `$schema` field with a URL. The URL contains the schema version.

1. Copy the `$schema` value from a file of the same kind in the same report.
2. Do not change the `$schema` value of an existing file.

## 4. Page files

`pages.json`:

```json
{
  "$schema": "<copy from the existing file>",
  "pageOrder": ["a1b2c3d4e5f6a7b8c9d0", "0f9e8d7c6b5a4f3e2d1c"],
  "activePageName": "a1b2c3d4e5f6a7b8c9d0"
}
```

`page.json`:

```json
{
  "$schema": "<copy from an existing page.json>",
  "name": "0f9e8d7c6b5a4f3e2d1c",
  "displayName": "Sales by Region",
  "displayOption": "FitToPage",
  "height": 720,
  "width": 1280
}
```

1. When you add a page, add its name to `pageOrder` in `pages.json`.
2. Do not change `activePageName` unless the user asks.

## 5. Visual files

`visual.json` for a column chart:

```json
{
  "$schema": "<copy from an existing visual.json>",
  "name": "1a2b3c4d5e6f7a8b9c0d",
  "position": { "x": 40, "y": 40, "z": 1000, "width": 600, "height": 360, "tabOrder": 1000 },
  "visual": {
    "visualType": "clusteredColumnChart",
    "query": {
      "queryState": {
        "Category": { "projections": [ {
          "field": { "Column": { "Expression": { "SourceRef": { "Entity": "Product" } }, "Property": "Category" } },
          "queryRef": "Product.Category", "nativeQueryRef": "Category", "active": true
        } ] },
        "Y": { "projections": [ {
          "field": { "Measure": { "Expression": { "SourceRef": { "Entity": "Sales" } }, "Property": "Total Sales" } },
          "queryRef": "Sales.Total Sales", "nativeQueryRef": "Total Sales"
        } ] }
      }
    },
    "visualContainerObjects": {
      "title": [ { "properties": {
        "show": { "expr": { "Literal": { "Value": "true" } } },
        "text": { "expr": { "Literal": { "Value": "'Sales by Category'" } } }
      } } ]
    }
  }
}
```

- `position` uses pixels. The point 0,0 is the top-left corner of the page.
- `z` sets the layer. A visual with a larger `z` is in front.
- `visual.objects` contains the format of the visual. `visualContainerObjects` contains the title, the border, and the background.
- `filterConfig` contains the visual filters. See `references/change-filters-slicers.md`.

## 6. Field references

| Field kind | JSON shape | `queryRef` |
| --- | --- | --- |
| Column | `{"Column": {"Expression": {"SourceRef": {"Entity": "<table>"}}, "Property": "<column>"}}` | `<table>.<column>` |
| Measure | `{"Measure": {"Expression": {"SourceRef": {"Entity": "<table>"}}, "Property": "<measure>"}}` | `<table>.<measure>` |
| Column with aggregation | `{"Aggregation": {"Expression": {"Column": {...}}, "Function": <number>}}` | Copy from the report |

1. Use the table that owns the measure in the model snapshot as `Entity`.
2. Use a measure for each value. Use an aggregation of a column only if the user asks for it.
3. If you need an aggregation, copy the shape from a visual in the report that uses the same aggregation. If no visual has it, set the change status to `blocked` and ask the user.
4. In filters, `SourceRef` can use `Source` (an alias) in place of `Entity`. The `From` list of the same filter defines the alias.

## 7. Literal values

| Value type | Example of `Value` |
| --- | --- |
| Text | `"'North'"` (single quotes inside the string) |
| Whole number | `"10L"` |
| Decimal number | `"10.5D"` |
| True or false | `"true"`, `"false"` |
| Date and time | `"datetime'2026-01-01T00:00:00'"` |
| Color | `"'#1F6FB2'"` |

## 8. Query roles

The query roles are the keys in `queryState`. Each visual type has its own roles.

| Visual | `visualType` | Roles |
| --- | --- | --- |
| Card (new) | `cardVisual` | `Data` |
| Card (old) | `card` | `Values` |
| Table | `tableEx` | `Values` |
| Matrix | `pivotTable` | `Rows`, `Columns`, `Values` |
| Clustered column chart | `clusteredColumnChart` | `Category`, `Y`, `Series` |
| Clustered bar chart | `clusteredBarChart` | `Category`, `Y`, `Series` |
| Line chart | `lineChart` | `Category`, `Y`, `Series` |
| Pie chart | `pieChart` | `Category`, `Y` |
| Donut chart | `donutChart` | `Category`, `Y` |
| Slicer | `slicer` | `Values` |

## 9. Copy rule

1. If the report has a visual of the same type, copy its structure. Change only the name, the position, the fields, and the title.
2. If the report has no visual of the same type, use the shapes in this file.
3. If you use the shapes in this file, add "check the format in Power BI Desktop" to the change description.
