# skills

A collection of portable Agent Skills, packaged as [agent-plugins.org](https://agent-plugins.org) v1.0.0 plugins so they can be loaded by any spec-compliant client (Claude Code, Cursor, and others), not just one.

## Plugins

| Plugin | Version | Description |
|---|---|---|
| [`agent-plugins/`](./agent-plugins) | 1.0.0 | Build a plugin conforming to the agent-plugins.org spec, via a Socratic session that scopes the plugin before scaffolding `plugin.json`, `skills/*/SKILL.md`, and `mcp.json`. |

More plugins will be added here as they're built. Each row's version tracks that plugin's own `plugin.json`.

## Structure

Each top-level directory is a self-contained plugin:

```
<plugin-name>/
├── plugin.json
├── skills/
│   └── <skill-name>/
│       └── SKILL.md
└── mcp.json          # optional
```
