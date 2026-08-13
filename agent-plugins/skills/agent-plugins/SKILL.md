---
name: agent-plugins
description: Build a plugin conforming to the agent-plugins.org open specification (v1.0.0) — the vendor-neutral, portable packaging format for Agent Skills and MCP servers that spec-compliant clients (Claude Code, Cursor, and others) can discover and load consistently. Starts with a one-question-at-a-time Socratic session to pressure-test what the plugin is actually for and which components it needs, before scaffolding plugin.json, skills/*/SKILL.md, and mcp.json. Use whenever the user invokes /agent-plugins, asks to "build an agent plugin", "make a plugin.json", "package this skill/MCP server for agent-plugins.org", "write an mcp.json", or wants a Skill/MCP server to be portable across multiple agent clients instead of tied to one.
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - AskUserQuestion
---

# /agent-plugins — Build an Agent Plugins–Compliant Plugin

Agent Plugins (agent-plugins.org, spec v1.0.0) is an open, vendor-neutral standard — governed by a steering committee including Amazon, Cursor, Microsoft, OpenAI, and Vercel — for packaging Agent Skills and MCP servers into one portable directory that any compliant client can load. It exists because clients had each invented incompatible plugin formats; the spec defines the small interoperability floor, not a maximal framework.

This skill has two phases. **Do not skip to phase 2.** A plugin manifest is easy to write; the mistake is writing one for the wrong thing — bundling an MCP server that should just be a hosted skill, or building portability nobody asked for. The exact schema, field tables, and validation/path-safety rules live in `references/spec.md` — read it before generating any file, and re-check against it before declaring the plugin done.

## Phase 1 — Socratic session

Ask **one question at a time** and wait for the answer before asking the next. This is a dialogue meant to sharpen the user's own thinking, not a form to fill in — react to what they actually say, skip questions their answer already resolved, and push back if an answer reveals the plugin isn't the right shape yet. Don't batch these into a checklist message.

Work through these in order, adapting as you go:

1. **Purpose.** "In one sentence, what capability does this give an agent, and what problem does it solve that the agent can't already do?" If the answer is vague, stay here — everything downstream (naming, description, components) derives from this.
2. **Necessity check.** "Does this already exist as a Skill you use, an MCP server you run, or is it new?" If it's an existing single-client Skill, ask directly: *is portability across clients actually needed right now, or would wrapping it in a plugin just add ceremony?* The spec is a floor for sharing across clients — if there's only ever going to be one client, a bare Skill may be enough, and it's worth saying so.
3. **Audience.** "Which agent clients does this need to run in — just the one you're using today, or others too?" This determines whether `extensions` / client-specific reverse-domain directories matter at all.
4. **Components.** "Does the agent need extra instructions or a workflow (→ a Skill), a live tool or data connection (→ an MCP server), or both?" A plugin can carry either, neither meaningfully (don't build an empty one), or both — don't assume both are needed just because the format supports it.
5. **If a Skill is involved:** "What should the skill be named, and can you describe its purpose in one sentence that tells the agent *when* to reach for it?" Push on the description the same way SKILL.md authoring always should — a vague description means the agent won't trigger it reliably.
6. **If an MCP server is involved:** "How does it run — a local process you control (`stdio`), or something already hosted over HTTP (`streamable-http`)?" Only mention the legacy `sse` transport if they specifically need compatibility with an old MCP 2024-11-05 server — don't offer it as a default choice.
7. **Naming.** "What should the plugin itself be called?" Check it against the constraint before moving on: 1–64 chars, lowercase alphanumeric/hyphen/period only, must start and end alphanumeric, no `--` or `..`. If their proposed name fails, say exactly which rule it breaks and suggest a fix rather than silently changing it.
8. **Versioning.** "Starting fresh at `0.1.0`/`1.0.0`, or does this already have a version from somewhere else it's being ported from?"
9. **Metadata depth.** "Want author/license/homepage/repository filled in now, or ship the minimal manifest and add these later?" Default to minimal if they hesitate — every optional field left out is one less thing to get wrong.
10. **Client-specific extensions.** "Does any specific client need special behavior beyond the portable core — custom hooks, settings?" If the answer is no or "maybe later," **do not** add an `extensions` block or `com.example.client/` directory. Speculative extension namespaces are exactly the kind of unrequested flexibility to avoid.

Once purpose, components, and name are settled, summarize your understanding back in 2-3 sentences and confirm before scaffolding. If the user answers everything in one message up front, don't re-ask — just confirm the summary and move to phase 2.

## Phase 2 — Scaffold

Read `references/spec.md` now if you haven't, for the exact field tables, JSON Schema URLs, and validation rules — don't reconstruct them from memory.

1. Create the plugin root directory (named after the plugin's `name`).
2. Write `plugin.json` — minimal (just `$schema` + `name`) unless phase 1 established a need for more fields. Use the exact `$schema` value for v1.0.0, not a guessed URL.
3. If a Skill was scoped: create `skills/<skill-name>/SKILL.md` with `name` + `description` frontmatter, following normal SKILL.md authoring practice (the description is the trigger mechanism — make it specific about when to use it). Add `scripts/`/`references/` under that skill folder only if the skill's own content needs them.
4. If an MCP server was scoped: write `mcp.json` with the matching `$schema` version and one entry per server under `mcpServers`, using the transport fields from `references/spec.md`. For `stdio` servers, remember `${PLUGIN_ROOT}` and `${PLUGIN_DATA}` are the only valid placeholders, and `command`/`cwd` must stay plugin-relative (`./`-prefixed) — nothing that resolves outside the plugin root.
5. Only if phase 1 confirmed a real need: add the client's reverse-domain directory (e.g. `com.example.client/`) and/or the `extensions` object in `plugin.json`, keyed by that same namespace.
6. Don't add a `README.md`, license file, or CI config unless the user asks — the spec doesn't require them and it's not what was asked for.

## Before calling it done

Walk the manifest(s) against the validation rules in `references/spec.md`: naming constraints, `extensions` must be an object, all paths resolve inside the plugin root, `stdio` `command` is a single token, HTTP transports use HTTPS (except localhost) with no userinfo/fragment in the URL. Point out anything that would make a conformant client reject the plugin outright versus something that's merely ignored (unknown top-level fields are non-fatal; most other violations are fatal).

If the user wants deeper grounding beyond `references/spec.md`, point them at https://agent-plugins.org/specification (normative spec), https://agent-plugins.org/schemas (JSON Schemas), https://agent-plugins.org/plugin-authors (authoring guide), and the worked example at https://github.com/agentplugins/agent-plugins-example.
