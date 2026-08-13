# agent-plugins

Version: 1.0.0

An [agent-plugins.org](https://agent-plugins.org) v1.0.0 plugin that packages the `agent-plugins` Skill: a guided, Socratic workflow for building other agent-plugins.org–compliant plugins. It scopes what a plugin actually needs (Skill, MCP server, or both) before scaffolding `plugin.json`, `skills/*/SKILL.md`, and `mcp.json`.

## Contents

```
agent-plugins/
├── plugin.json
└── skills/
    └── agent-plugins/
        ├── SKILL.md
        └── references/
            └── spec.md
```

## Usage

Load this plugin in any agent-plugins.org–compliant client. The bundled skill triggers when you ask to build an agent plugin, write a `plugin.json`/`mcp.json`, or package a Skill/MCP server for portability across clients.
