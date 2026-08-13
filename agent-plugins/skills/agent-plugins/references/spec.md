# Agent Plugins Specification v1.0.0 — Reference

Source: https://agent-plugins.org/specification (normative), https://agent-plugins.org/schemas, https://agent-plugins.org/plugin-authors. Consult these directly if a detail below seems ambiguous or the user needs something not covered here — this file is a working summary, not a replacement for the normative spec.

## Plugin directory shape

```
my-plugin/
├── plugin.json              # Required manifest
├── skills/                  # Optional Agent Skills
│   └── summarize/
│       ├── SKILL.md
│       ├── scripts/
│       └── references/
├── mcp.json                 # Optional MCP server definitions
└── com.example.client/      # Client-specific extensions (reverse-domain namespace)
    └── hooks/
```

- **Skills** are discovered as subdirectories of `skills/` that contain a `SKILL.md` file.
- **MCP servers** are discovered via `mcp.json` at the plugin root.
- A missing `skills/` or `mcp.json` is not an error — components are simply optional.
- If `skills` exists but isn't a directory (or similar filesystem-kind mismatches), only that component type is invalidated — it doesn't fail the whole plugin.
- Reverse-domain client namespaces (e.g. `com.example.client/`) let a specific client stash extra files/behavior without touching the portable core. Unknown namespaces are ignored by other clients without validation.

## `plugin.json` schema

### Required
| Field | Type | Constraint |
|---|---|---|
| `$schema` | string | `"https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"` |
| `name` | string | 1–64 chars; lowercase alphanumeric, hyphens, periods only; must start and end alphanumeric; no consecutive `--` or `..` |

### Optional
| Field | Type | Purpose |
|---|---|---|
| `version` | string | SemVer recommended; used for update checks |
| `description` | string | Brief plugin purpose |
| `author` | object | `{ name?, email?, url? }`, all strings |
| `homepage` | string | Docs/homepage URL |
| `repository` | string | Source repo URL |
| `license` | string | SPDX identifier recommended |
| `keywords` | string[] | Search/discovery tags |
| `extensions` | object | Client-specific data, keyed by reverse-domain namespace. MUST be an object whose member values are also objects. Unknown namespaces ignored. |

### Minimal example
```json
{
  "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
  "name": "minimal-plugin"
}
```

### Full example
```json
{
  "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
  "name": "plugin-name",
  "version": "1.2.0",
  "description": "Brief plugin description",
  "author": {
    "name": "Author Name",
    "email": "author@example.com",
    "url": "https://example.com"
  },
  "homepage": "https://docs.example.com/plugin",
  "repository": "https://github.com/example/plugin",
  "license": "MIT",
  "keywords": ["keyword1", "keyword2"],
  "extensions": {
    "com.example.client": {
      "setting": true
    }
  }
}
```

## SKILL.md frontmatter (inside `skills/<name>/`)

```markdown
---
name: greet
description: Greet the user and offer help.
---
```

`name` + `description` are the minimum. The description is the discovery mechanism — write it so a client can tell *when* to use the skill, not just what it does.

## `mcp.json` schema

### Top level
| Field | Type | Required |
|---|---|---|
| `$schema` | string | Yes — `"https://agent-plugins.org/schemas/1.0.0/mcp.schema.json"`, matching the plugin's spec version |
| `mcpServers` | object | Yes — keys are server IDs, values are server configs below |

### `stdio` server
| Field | Type | Required | Notes |
|---|---|---|---|
| `type` | `"stdio"` | Yes | |
| `command` | string | Yes | Bare executable name, or `./`-prefixed plugin-relative path; single token |
| `args` | string[] | No | Supports `${PLUGIN_ROOT}` / `${PLUGIN_DATA}` expansion |
| `env` | object<string,string> | No | Supports placeholder expansion in values (not keys) |
| `cwd` | string | No | Plugin-relative `./…`, `${PLUGIN_ROOT}`, or `${PLUGIN_DATA}`; defaults to plugin root |

### `streamable-http` server
| Field | Type | Required | Notes |
|---|---|---|---|
| `type` | `"streamable-http"` | Yes | |
| `url` | string | Yes | Absolute HTTP/HTTPS; no userinfo or fragment; HTTPS required except `localhost` |
| `headers` | object<string,string> | No | No placeholder expansion |

### `sse` server (legacy, MCP 2024-11-05)
Same fields as `streamable-http` (`url`, `headers`), `type: "sse"`. Deprecated — only use for compatibility with an old server, not as a default.

### Example
```json
{
  "$schema": "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json",
  "mcpServers": {
    "local-validator": {
      "type": "stdio",
      "command": "./bin/validator",
      "args": ["--data", "${PLUGIN_DATA}/validator"],
      "env": { "CONFIG": "${PLUGIN_ROOT}/config.json" },
      "cwd": "${PLUGIN_ROOT}"
    },
    "deployment-api": {
      "type": "streamable-http",
      "url": "https://deploy.example.com/mcp",
      "headers": { "X-Tenant": "public-tenant" }
    },
    "legacy-events": {
      "type": "sse",
      "url": "https://legacy.example.com/sse"
    }
  }
}
```

## Environment variables for `stdio` subprocesses

Clients launching a `stdio` server MUST inject, into the subprocess environment (not configurable via the server's own `env` object):
- `PLUGIN_ROOT` — absolute path to the plugin root
- `PLUGIN_DATA` — absolute path to a persistent, client-managed directory for that plugin instance

### Placeholder expansion rules
- Applies to: `args` elements, `env` values, `cwd`
- Recognized placeholders: `${PLUGIN_ROOT}`, `${PLUGIN_DATA}` only
- Single, non-recursive textual substitution; unrecognized placeholders are left literal
- Does **not** apply to: `env` keys, `command`, or the fixed component locations (`skills/`, `mcp.json`)

## Path safety

- Any package-supplied path that would resolve outside the plugin root must be rejected by a conformant client.
- Plugin-relative paths must begin with `./`.
- `cwd` is restricted to plugin-relative form, `${PLUGIN_ROOT}`, or `${PLUGIN_DATA}`.
- Symlinks may only resolve to targets within the plugin root.

## Validation outcomes

| Condition | Outcome |
|---|---|
| Unknown top-level field in `plugin.json` | Reported, ignored — non-fatal |
| `extensions` present but not an object | Reported, ignored — non-fatal |
| Any other schema violation | Fatal — plugin rejected, no components loaded |
| Fixed location missing (`skills/`, `mcp.json`) | No error — component type just absent |
| Invalid entry within a component (e.g. one bad skill folder) | That entry skipped, others still load |
| MCP server connection failure | That server skipped, others still load |
| Unsupported MCP transport | That server skipped, others still load |

## Minimum client conformance (for context — not what you're building, but useful when the user asks "will client X load this")

A minimally conformant client MUST:
1. Load plugins from a directory path
2. Parse and validate `plugin.json` against the declared schema
3. Discover components at the fixed locations
4. If it supports MCP at all: implement at least `stdio` or `streamable-http`
5. If it launches subprocesses: provide and expand `PLUGIN_ROOT` / `PLUGIN_DATA`
6. Support at least one component type
7. Ignore component types and extension namespaces it doesn't understand, rather than failing

## Governance note

Spec is openly licensed, developed in public; Technical Steering Committee includes Amazon, Cursor, Microsoft, OpenAI, Vercel. New proposals start as GitHub Discussions and need a concrete portability need plus implementer support — worth mentioning if the user asks about proposing a spec change rather than just authoring a plugin.
