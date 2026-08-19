---
name: a2a-agent-claude
description: Build an agent that speaks the A2A (Agent2Agent) protocol — the Linux Foundation open standard for agent-to-agent communication, governed by a Technical Steering Committee including AWS, Cisco, Google, IBM, Microsoft, Salesforce, SAP, and ServiceNow. Starts with a one-question-at-a-time Socratic session that first checks whether A2A is even the right protocol (versus MCP), then scopes the agent's skills, task lifecycle, transport binding, and protocol version before scaffolding the Agent Card, the executor, and the server or client wiring. Use whenever the user invokes /a2a-agent-claude, asks to "build an A2A agent", "expose my agent over A2A", "write an agent card", "make my agent talk to another agent", "call a remote A2A agent", "publish .well-known/agent-card.json", or wants two independent agents to collaborate rather than one agent calling a tool.
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - WebFetch
  - AskUserQuestion
---

# /a2a-agent-claude — Build an A2A-Compliant Agent

A2A (Agent2Agent) is an open protocol for **agents talking to other agents**: one agent delegates a unit of work to another over HTTP, without either side exposing its internal memory, tools, or reasoning. It was donated by Google to the Linux Foundation and is Apache-2.0 licensed. A remote agent publishes an **Agent Card** describing who it is and what it can do; clients discover that card, send **Messages**, and track the resulting stateful **Task** to a terminal state, collecting **Artifacts** along the way.

This skill has three phases. **Do not skip to phase 2.** Two mistakes dominate A2A work, and both are cheap to prevent in conversation and expensive to unwind in code:

1. **Reaching for A2A when the answer is MCP.** A2A is for partnering with an autonomous peer. MCP is for *using* a capability. If what's being built is a function with structured inputs and outputs, A2A is the wrong protocol and the whole plan should change.
2. **Writing v0.3 code against a v1.0 target.** A2A 1.0 (released March 2026; 1.0.1 May 2026) renamed nearly every JSON-RPC method, changed every enum to `SCREAMING_SNAKE_CASE`, restructured the Agent Card's transport declaration, and flattened `Part`. Most tutorials, blog posts, and model recall are still 0.3. **Never write A2A code from memory** — read `references/protocol.md` for the wire format and `references/implementation.md` for the SDK patterns and the full 0.3→1.0 delta.

## Phase 1 — Socratic session

Ask **one question at a time** and wait for the answer before asking the next. This is a dialogue meant to sharpen the user's own thinking, not a form to fill in — react to what they actually say, skip questions their answer already resolved, and push back when an answer reveals the design isn't right yet. Don't batch these into a checklist message.

Work through these in order, adapting as you go:

1. **The MCP gate.** "What is the thing on the other end — an autonomous agent that reasons, plans, and holds state across a conversation, or a capability with defined inputs and outputs?" This is the most important question in the session and you should be willing to end the session on it. Tools, database queries, API wrappers, calculators, retrieval endpoints — those are MCP, and saying so plainly is more useful than building an A2A server around a function call. A2A and MCP are complementary and frequently coexist: an A2A agent typically uses MCP *internally* for its own tools. If both are in play, name which is which before going further.
2. **Side of the wire.** "Are you exposing an agent for others to call (A2A server), consuming someone else's agent (A2A client), or both?" Server and client are genuinely different builds — the server needs an Agent Card, an executor, and a task store; the client needs card resolution and a send/stream loop. Don't scaffold both because the SDK supports both.
3. **Skills.** "What are the distinct things this agent can do? Name each one and describe it the way a *stranger's* agent would need to read it to decide whether to route work here." Every `AgentSkill` needs `id`, `name`, `description`, and `tags` — all four are required by the spec. Push on the descriptions: on the public internet the card is the entire basis for another agent's routing decision, so a vague description means no traffic. Two or three sharp skills beat eight vague ones.
4. **Task shape.** "For a typical request — does the agent answer immediately, or does it work for a while and produce output later?" This decides whether `SendMessage` returns a bare `Message` or creates a `Task`. Not everything needs a Task; a stateless Q&A agent returning a `Message` is legitimate and simpler. If work is long-running, ask what the intermediate states look like, and whether the agent ever needs to come back and ask the user something (`TASK_STATE_INPUT_REQUIRED`) or demand credentials (`TASK_STATE_AUTH_REQUIRED`).
5. **Update delivery.** "How does the caller find out the work is done — do they hold a connection open (streaming), poll, or should the agent call a webhook when it finishes (push notifications)?" Each maps to a `capabilities` flag that clients check *before* calling, so an over-declared capability is a broken promise. If the caller is a long-lived service and tasks run for minutes or hours, push notifications are worth the webhook plumbing; if tasks finish in seconds, streaming or plain polling is enough. Don't declare all three by default.
6. **Multi-turn.** "Will a caller come back with follow-ups that need earlier context?" If yes, explain `contextId` — the server-generated identifier that groups related Tasks — and decide now whether continuation reuses the same Task (`taskId`) or opens a new one in the same context. Getting this wrong later means reworking the task store.
7. **Transport binding.** "Which binding do the callers you care about actually speak?" `JSONRPC` is the common default and the safest single choice; `GRPC` suits internal high-throughput service meshes; `HTTP+JSON` suits REST-native infrastructure. An agent MAY expose several — they're an ordered list in `supportedInterfaces`, first entry preferred — but every binding you declare is one you must keep functionally equivalent, which the spec requires. Start with one unless there's a named caller that needs another.
8. **Protocol version.** "Are the agents on the other side on A2A 1.0, or still on 0.3?" Target `1.0` unless there's a concrete 0.3 peer. If there is, say so explicitly: an agent can expose multiple interfaces at different `protocolVersion`s, and the Python SDK ships a `compat/v0_3` layer. This answer changes literally every method name and enum value in the generated code, so pin it before writing a line.
9. **Discovery.** "How will callers find this agent — the well-known URI, a registry, or hardcoded configuration?" The well-known path is `/.well-known/agent-card.json` (IANA-registered). Registries and direct configuration are both legitimate; direct config is fine for tightly coupled internal systems and doesn't need the well-known route at all.
10. **Security.** "Who is allowed to call this, and how do they prove it?" A2A carries no bespoke auth — it declares standard schemes (`apiKey`, `http`, `oauth2`, `openIdConnect`, `mutualTLS`) in `securitySchemes` and requirements in `securityRequirements`, and authentication happens in normal HTTP headers outside the protocol body. If the agent is internal-only behind a mesh, say so and skip the scheme rather than inventing one. Ask separately whether some skills are more sensitive than the card should reveal publicly — that's what the authenticated extended card is for, and it's worth mentioning only if the answer is yes.
11. **Media types.** "What can callers send in, and what comes back out?" `defaultInputModes` and `defaultOutputModes` are required media-type lists on the card, overridable per skill. `text/plain` in and out is a fine answer; `application/json` matters if the agent takes structured input.
12. **Extensions.** "Is there anything the core protocol can't carry that the caller genuinely needs?" If the answer is no or "maybe later," **do not** add an `extensions` block. A declared extension is a URI other implementers are expected to understand; speculative ones are noise. Revisit only if a real cross-agent need surfaced in question 3 or 4.
13. **Language and SDK.** "What are you building in?" Official SDKs exist for Python, JavaScript/TypeScript, Java, .NET, Go, and Rust. Python and JS are the most mature — check `references/implementation.md` for what's verified before promising a version number.

Once the MCP gate is cleared and skills, task shape, binding, and version are settled, summarize your understanding back in 2-3 sentences and confirm before scaffolding. If the user answers everything in one message up front, don't re-ask — confirm the summary and move to phase 2.

## Phase 2 — Scaffold

Read `references/protocol.md` and `references/implementation.md` now if you haven't. Do not reconstruct field names, method names, or enum values from memory — the 0.3 spelling is what surfaces from recall and it is wrong for 1.0.

Build in this order, because each step constrains the next:

1. **The Agent Card first.** It's the contract; writing it first forces the skills and capabilities to be concrete before any handler exists. Fill only the fields phase 1 established. Required: `name`, `description`, `supportedInterfaces`, `version`, `capabilities`, `defaultInputModes`, `defaultOutputModes`, `skills`. Set `capabilities` flags to what the agent will *actually* honor.
2. **The executor.** One class implementing the SDK's agent-executor interface: receive the request context, create or resume a Task, push status updates, attach Artifacts, reach a terminal state. Implement `cancel` honestly — raising "not supported" is a valid answer if the work isn't cancelable, and better than a stub that silently does nothing.
3. **Server wiring.** Request handler + task store + the routes for the chosen binding, mounted on an ASGI app (or the language equivalent). Serve the card at the well-known path only if phase 1 chose well-known discovery.
4. **Client**, only if phase 1 scoped one: resolve the card, build the client from it, send messages, consume the response stream.
5. Add push-notification config, an extended card, or additional interfaces **only** if phase 1 called for them. Each is real surface area with real failure modes.
6. Don't add a `README.md`, Dockerfile, or CI config unless asked.

## Phase 3 — Verify before calling it done

A card that parses but misdescribes the agent is worse than no card — it attracts work the agent will fail. Walk these before declaring completion:

- Every `capabilities` flag set to `true` is backed by an implementation; nothing declared aspirationally.
- Every skill's `description` and `tags` would let a stranger's agent route correctly without reading your source.
- Enum values are `SCREAMING_SNAKE_CASE` (`TASK_STATE_COMPLETED`, `ROLE_USER`) and JSON fields are `camelCase`. Any lowercase `"working"` or `"user"` in the output is 0.3 leakage — fix it.
- Every task path reaches a terminal state (`COMPLETED`, `FAILED`, `CANCELED`, `REJECTED`). A task that can hang in `WORKING` forever will hang the caller too.
- The declared `protocolVersion` in `supportedInterfaces` matches the code that was actually written.
- `securityRequirements` references only schemes defined in `securitySchemes`, and no static secret is embedded in the card.
- If it runs: fetch the card over HTTP and check it round-trips, then drive one real request end to end. `a2a-inspector` (https://github.com/a2aproject/a2a-inspector) is the official interactive validator — recommend it rather than hand-rolling a conformance checker.

Report what you verified and what you didn't. "The card serves and one request completed" and "the code compiles" are different claims.

## Going deeper

Point the user at https://a2a-protocol.org/latest/specification/ (normative spec), https://a2a-protocol.org/latest/topics/key-concepts/ (conceptual overview), https://a2a-protocol.org/latest/topics/a2a-and-mcp/ (the A2A/MCP boundary, if question 1 was contested), https://github.com/a2aproject/A2A (spec source and the `specification/a2a.proto` that is the authority on field names), and https://github.com/a2aproject/a2a-samples (working agents in several languages).
