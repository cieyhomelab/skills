# a2a-agent

Version: 1.0.0

An [agent-plugins.org](https://agent-plugins.org) v1.0.0 plugin that packages the `a2a-agent` Skill: a guided, Socratic workflow for building agents that speak the [A2A (Agent2Agent) protocol](https://a2a-protocol.org) — the Linux Foundation open standard for agent-to-agent communication.

The session opens by checking whether A2A is even the right protocol (versus MCP), then scopes the agent's skills, task lifecycle, transport binding, and protocol version before scaffolding the Agent Card, executor, and server or client wiring. When the user wants to learn A2A rather than have it built for them, the skill switches to mentor mode and guides them through writing each piece themselves.

## Contents

```
a2a-agent/
├── plugin.json
└── skills/
    └── a2a-agent/
        ├── SKILL.md
        └── references/
            ├── protocol.md          # A2A v1.0 wire format: card, data model, methods, errors
            └── implementation.md    # SDK patterns, v0.3→v1.0 migration, failure modes
```

## Usage

Load this plugin in any agent-plugins.org–compliant client. The bundled skill triggers when you ask to build an A2A agent, write an Agent Card, expose an agent over A2A, call a remote A2A agent, learn the A2A protocol, or get two independent agents collaborating.

## Protocol coverage

Targets **A2A v1.0** (spec v1.0.0 March 2026, v1.0.1 May 2026). A2A 1.0 renamed every JSON-RPC method, changed every enum to `SCREAMING_SNAKE_CASE`, restructured the Agent Card's transport declaration, and flattened `Part` — most material in circulation is still v0.3, so the references carry the full delta and the skill treats "which version are the peers on" as a blocking question.
