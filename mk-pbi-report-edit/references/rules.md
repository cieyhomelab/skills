# Shared Rules

This file contains the rules for all skills in the `mk-` collection. The `## Rules` section of SKILL.md points to it. The rules apply in each run.

1. Write messages to the user in the language of the user.
2. Write the plan file text in the language of the user. Keep the template headings, the change types, and the status values in English. The scripts read them.
3. If a fact is not known, write "unknown". Do not invent names, values, or dates.
4. Give the evidence for each finding. Examples: a file path, a script output line, a tool result.
5. Do not report success if a check failed or did not run. Write which work has no verification.
6. Use the full name of each MCP tool. Example: `mcp__powerbi-dax__search_model`.
7. If a tool or a script gives an error, report the error text. Do not hide it.
8. Use forward slashes in the paths in instructions. The scripts also accept Windows paths.
9. Ask the user only when the skill has no default value and no stop condition.
