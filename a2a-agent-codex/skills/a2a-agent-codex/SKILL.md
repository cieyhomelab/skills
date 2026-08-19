---
name: a2a-agent-codex
description: Build, adapt, or review agents that speak the A2A (Agent2Agent) protocol in Codex-oriented coding workflows. Use when the user asks to create an A2A agent, expose an existing agent over A2A, write an Agent Card, implement an A2A server or client, publish /.well-known/agent-card.json, connect independent agents, or decide whether A2A or MCP is the right protocol. Always begin with a one-question-at-a-time Socratic session before scaffolding protocol artifacts.
---

# A2A Agent Codex

## Overview

A2A is for interoperable agent-to-agent collaboration: one autonomous agent delegates work to another without exposing internal memory, tools, or reasoning. Use this skill to help Codex shape the protocol boundary, write the Agent Card contract, scaffold server/client wiring, and verify that the implementation matches the current A2A specification.

This skill is packaged using the Agent Plugins layout: a plugin root with `plugin.json`, discoverable skills under `skills/<skill-name>/SKILL.md`, and optional `references/` loaded only when protocol detail is needed.

## Required References

Read these before writing A2A wire formats, SDK code, or Agent Cards:

- `references/protocol.md`: current A2A protocol model, Agent Card fields, task/message/artifact objects, method names, enum casing, versioning, and verification traps.
- `references/implementation.md`: SDK and implementation patterns for common server/client scaffolds.

Also check the live docs when current accuracy matters: https://a2a-protocol.org/latest/specification/ and https://github.com/a2aproject/A2A.

## Phase 1 - Socratic Session

Ask one question at a time and wait for the answer before asking the next. React to the user's answer, skip questions already resolved, and push back when the design points to MCP, a plain API, or a local tool instead of A2A.

Work through these decisions in order:

1. **A2A-vs-MCP gate.** Ask: "Is the other side an autonomous agent that reasons and manages state, or a capability with defined inputs and outputs?" If it is a tool, retrieval endpoint, database query, calculator, or API wrapper, recommend MCP instead. If both are involved, distinguish the external A2A peer from internal MCP tools.
2. **Side of the wire.** Ask whether Codex should expose an A2A server, consume a remote A2A agent as a client, or build both.
3. **Agent skills.** Ask for the distinct capabilities this agent advertises to other agents. Each `AgentSkill` needs `id`, `name`, `description`, and `tags`; sharpen vague descriptions until another agent could route work from the card alone.
4. **Task shape.** Ask whether a typical request returns immediately or creates long-running work. Decide whether to return a `Message`, create a `Task`, or support both. If long-running, identify possible intermediate states and whether `TASK_STATE_INPUT_REQUIRED` or `TASK_STATE_AUTH_REQUIRED` can occur.
5. **Update delivery.** Ask whether callers use streaming, polling, or push notifications. Declare only the matching `capabilities` flags.
6. **Multi-turn context.** Ask whether follow-ups need previous context. If yes, decide how `contextId` and `taskId` are created and reused.
7. **Transport binding.** Ask which binding callers speak: `JSONRPC`, `GRPC`, or `HTTP+JSON`. Prefer one implemented binding unless a named caller requires more.
8. **Protocol version.** Ask whether peers use A2A 1.0 or legacy 0.3. Default to 1.0 only when no concrete legacy peer exists.
9. **Discovery.** Ask whether callers discover the agent through `/.well-known/agent-card.json`, a registry, or direct configuration.
10. **Security.** Ask who can call the agent and how they authenticate. Use standard HTTP security schemes in the Agent Card; never embed static secrets.
11. **Media types.** Ask what callers send and receive. Fill `defaultInputModes` and `defaultOutputModes`; override per skill only when needed.
12. **Extensions.** Ask whether the core protocol cannot carry something the caller needs. Do not add speculative extensions.
13. **Language and runtime.** Ask what stack Codex is modifying or creating. Prefer the repo's existing framework and SDK conventions.

Once the MCP gate is cleared and the agent's skills, lifecycle, binding, version, discovery, and security are known, summarize the design in 2-3 sentences and get confirmation before editing files. If the user supplied all answers up front, summarize and proceed.

## Phase 2 - Scaffold

Read `references/protocol.md` and `references/implementation.md` before writing files. Build the contract before handlers:

1. **Agent Card.** Write the card first. Required fields include `name`, `description`, `supportedInterfaces`, `version`, `capabilities`, `defaultInputModes`, `defaultOutputModes`, and `skills`. Fill only fields supported by the Socratic session and implementation plan.
2. **Executor.** Implement the SDK or framework executor interface. It should receive request context, create or resume task state, emit status/artifact updates, and reach a terminal state. Implement cancellation honestly, even if the honest answer is "not supported".
3. **Server wiring.** Add request handling, task store, selected binding routes, and well-known card discovery only if chosen.
4. **Client wiring.** Add card resolution, protocol selection, message send/stream handling, and task polling/subscription only if a client was scoped.
5. **Optional surfaces.** Add push notification config, extended card handling, extra bindings, signatures, or extensions only when Phase 1 required them.

Do not add a README, Dockerfile, CI config, registry integration, or plugin wrapper unless the user asks or the surrounding repo already requires it.

## Phase 3 - Verify

Before reporting completion, verify the implementation at the strongest level practical for the repo:

- Fetch or load the Agent Card and check it parses.
- Confirm every declared capability has implemented behavior.
- Confirm each advertised skill is specific enough for routing.
- Check A2A 1.0 casing: JSON fields use `camelCase`; enum values use `SCREAMING_SNAKE_CASE`.
- Confirm method names and binding routes match the selected protocol version.
- Drive at least one real send-message path end to end when the app can run locally.
- Confirm every task path reaches a terminal state: `TASK_STATE_COMPLETED`, `TASK_STATE_FAILED`, `TASK_STATE_CANCELED`, or `TASK_STATE_REJECTED`.
- Confirm `securityRequirements` references only defined `securitySchemes`, and no secret is embedded in source or card output.

Recommend `a2a-inspector` for interactive conformance checks when the user wants protocol-level QA.

## Agent Plugins Structure

When packaging this skill or an output as an Agent Plugin, follow the agent-plugins.org structure:

```text
<plugin-name>/
├── plugin.json
└── skills/
    └── <skill-name>/
        ├── SKILL.md
        ├── references/
        ├── scripts/
        └── assets/
```

Keep `plugin.json` minimal unless portability metadata is actually needed. Use the canonical schema URL for Agent Plugins v1.0.0 and keep plugin-relative paths inside the plugin root.

## Reporting

Report exactly what was built and verified. Distinguish "card parses", "server starts", "one request completed", "tests passed", and "not run". Include links to the normative A2A docs when decisions relied on live protocol details.
