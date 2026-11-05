# Branch: Edit a Visual

This file tells how to change an existing visual. Step 9 uses it for the change type `edit-visual`.

## Find the visual

1. Find the visual with the output of `scripts/inspect_report.py`. Use the page display name and the visual title.
2. If more than one visual matches, set the change status to `blocked`. Ask the user which visual to change.
3. Read the full `visual.json` before you change it.

## Change the fields

1. To add a field, add a projection to the query role. Use the field shapes in `references/pbir-structure.md`, section 6.
2. To remove a field, remove its projection.
3. To replace a field, change the `field`, `queryRef`, and `nativeQueryRef` of the projection.
4. If a filter or a sort of the visual uses a removed field, remove that filter or sort too. Record this in the plan file.

## Change the visual type

1. Change `visualType`.
2. Move each projection to the query role of the new type. Use the table in `references/pbir-structure.md`, section 8.
3. If a field has no role in the new type, set the change status to `blocked`. Ask the user.
4. Remove the `objects` entries that the new type does not use. If you do not know, keep them and add "check the format in Power BI Desktop" to the change description.

## Change the format

1. Change the value in `visual.objects` or `visualContainerObjects`.
2. If the property is not in the file, copy its shape from a different visual in the report.
3. If no visual in the report has it, set the change status to `blocked`. Ask the user to set it one time in Power BI Desktop.

## Remove a visual

WARNING: Remove a visual only if the plan has this removal and the user approved it. The backup is the only recovery path.

1. Remove the folder `visuals/<visual name>/`.
2. Write the removal as a `delete` line in the files list of the plan file.

After each change, set the change status to `done` in the plan file.
