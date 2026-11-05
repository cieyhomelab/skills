# Branch: Filters and Slicers

This file tells how to add or change filters and slicers. Step 9 uses it for the change type `filter-slicer`.

## Filter levels

| Level | File | Key |
| --- | --- | --- |
| Report | `definition/report.json` | `filterConfig.filters` |
| Page | `definition/pages/<page name>/page.json` | `filterConfig.filters` |
| Visual | `.../visuals/<visual name>/visual.json` | `filterConfig.filters` |

## Add a filter

1. Find the level of the filter in the plan.
2. If the file has no `filterConfig`, add `"filterConfig": {"filters": []}`.
3. If the report has a filter of the same type, copy its shape.
4. If the report has no filter of the same type, use the shape below.
5. Give the filter a new name. Use the command in `references/pbir-structure.md`, section 2.
6. Set the change status to `done` in the plan file.

Shape of a filter that keeps the listed values:

```json
{
  "name": "3c4d5e6f7a8b9c0d1e2f",
  "field": { "Column": { "Expression": { "SourceRef": { "Entity": "Geo" } }, "Property": "Region" } },
  "type": "Categorical",
  "filter": {
    "Version": 2,
    "From": [ { "Name": "g", "Entity": "Geo", "Type": 0 } ],
    "Where": [ { "Condition": { "In": {
      "Expressions": [ { "Column": { "Expression": { "SourceRef": { "Source": "g" } }, "Property": "Region" } } ],
      "Values": [ [ { "Literal": { "Value": "'North'" } } ], [ { "Literal": { "Value": "'South'" } } ] ]
    } } } ]
  }
}
```

1. Write the values as literals. Use `references/pbir-structure.md`, section 7.
2. For a filter without a value (all values), omit the `filter` key. Keep `name`, `field`, and `type`.
3. For a relative date filter or a Top N filter, copy the shape from the report. If the report has no such filter, set the change status to `blocked`. Ask the user to make one filter in Power BI Desktop.

## Add a slicer

1. Add a visual with `visualType` `slicer`. Use `references/change-new-visual.md`.
2. Put the field in the `Values` role.
3. If the plan gives a slicer style, copy `objects.data` from a slicer in the report with this style.
4. If no slicer in the report has this style, use the default style. Add "check the format in Power BI Desktop" to the change description.

## Interactions

Visual interactions are in the page file, in the `visualInteractions` list. Each entry has `source`, `target`, and `type`.

1. Copy the shape of an existing entry.
2. If the page has no entry, set the change status to `blocked`. Ask the user to set the interaction in Power BI Desktop.
