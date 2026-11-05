# Convert a Report to PBIP (PBIR)

This file tells how to guide the user from a `.pbix` file or an old PBIP project to a PBIR project. Step 0 uses it.

## From a .pbix file

Give these instructions to the user. Then stop the skill.

1. Open the `.pbix` file in Power BI Desktop.
2. Select **File > Save as**.
3. In the file type list, select **Power BI project files (*.pbip)**.
4. If the list does not show this type, open **File > Options and settings > Options > Preview features**.
5. Turn on **Power BI Project (.pbip) save option**. Restart Power BI Desktop. Then do step 2 again.
6. Save the project in a new, empty folder. This folder is the report folder.
7. Tell the user to start the skill again with the path of the new `.pbip` file.

CAUTION: Keep the original `.pbix` file. It is a second copy of the report. The skill does not change it.

## Old format

The old format (PBIR-Legacy) keeps the full report in one file: `<report name>.Report/report.json`. The skill cannot edit this format.

Give these instructions to the user. Then stop the skill.

1. Open the `.pbip` file in Power BI Desktop.
2. Open **File > Options and settings > Options > Preview features**.
3. If the option **Store reports using enhanced metadata format (PBIR)** exists, turn it on. Restart Power BI Desktop.
4. Make one small change in the report. Example: move a visual and move it back.
5. Save the report. Power BI Desktop asks to upgrade the report. Accept the upgrade.
6. Make sure that the folder `<report name>.Report/definition/` now exists.
7. Tell the user to start the skill again.

## Result

The report folder has this structure after the conversion:

```
<report folder>/
├── <report name>.pbip
├── <report name>.Report/
│   ├── definition.pbir
│   └── definition/
└── <report name>.SemanticModel/
```
