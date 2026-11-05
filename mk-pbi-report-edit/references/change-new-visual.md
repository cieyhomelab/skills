# Branch: New Page and New Visual

This file tells how to add a page or a visual. Step 9 uses it for the change types `new-page` and `new-visual`.

## New page

1. Make a new page name. Use the command in `references/pbir-structure.md`, section 2.
2. Make the folder `definition/pages/<page name>/`.
3. Write `page.json`. Copy `$schema`, `displayOption`, `height`, and `width` from an existing page.
4. Set `displayName` to the page name from the plan.
5. Add the page name to the end of `pageOrder` in `pages.json`. If the plan gives a position, put it there.
6. Make the folder `visuals/` in the page folder.
7. Set the change status to `done` in the plan file.

## New visual

1. Find the page in the plan. If the plan has a new page, do the new page procedure first.
2. Make a new visual name.
3. Make the folder `definition/pages/<page name>/visuals/<visual name>/`.
4. Write `visual.json`. Apply the copy rule in `references/pbir-structure.md`, section 9.
5. Put each field in the query role from the plan. Use the field shapes from section 6.
6. Set `position` from the plan. If the plan says "auto", use the free space from step 3 of the workflow.
7. Set `z` and `tabOrder` to a value that is larger than all values on the page.
8. If the plan gives a title, set `visualContainerObjects.title`.
9. Set the change status to `done` in the plan file.

## Position rules

1. Keep each visual inside the page: `x + width` is not more than the page `width`, and `y + height` is not more than the page `height`.
2. Do not put a visual on top of a different visual, unless the plan says so.
3. Use a gap of 16 pixels between visuals, unless the page uses a different gap.
4. If the page has no free space for the visual, set the change status to `blocked`. Ask the user for a position.
