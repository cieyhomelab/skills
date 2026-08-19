# A2A Protocol v1.0 — Reference

Working summary for A2A **v1.0** (spec releases v1.0.0 March 2026, v1.0.1 May 2026). Sources: <https://a2a-protocol.org/latest/specification/> (normative), <https://github.com/a2aproject/A2A/blob/main/specification/a2a.proto> (authoritative field names), <https://a2a-protocol.org/latest/topics/key-concepts/>. Consult those directly if a detail here seems ambiguous — this is a summary, not a replacement for the normative spec.

**Field names below are the proto names rendered in camelCase, which is what goes on the wire.** The spec is proto-first: `specification/a2a.proto` defines the model in `snake_case`, and all JSON serializations MUST use camelCase (§5.5). Where a published doc sample and the proto disagree, the proto wins — see [Known spec inconsistency](#known-spec-inconsistency).

---

## 1. Version landscape — read this first

A2A 1.0 is not a compatible evolution of 0.3. Nearly every identifier changed. Model recall, blog posts, and most tutorials are still 0.3.

| | v0.3 | v1.0 |
|---|---|---|
| JSON-RPC method style | slash-delimited, `message/send` | PascalCase, `SendMessage` |
| `TaskState` values | `submitted`, `working`, `input-required` | `TASK_STATE_SUBMITTED`, `TASK_STATE_WORKING`, `TASK_STATE_INPUT_REQUIRED` |
| `Role` values | `user`, `agent` | `ROLE_USER`, `ROLE_AGENT` |
| Card transport decl. | top-level `url` + `preferredTransport` + `additionalInterfaces` | ordered `supportedInterfaces[]` |
| Card security field | `security` | `securityRequirements` |
| `Part` | wrapper types `TextPart` / `FilePart` / `DataPart` discriminated by `kind` | one flat `Part` with a `text`/`raw`/`url`/`data` oneof |
| Extended-card flag | `supportsAuthenticatedExtendedCard` (top level) | `capabilities.extendedAgentCard` |
| Extended-card method | `agent/getAuthenticatedExtendedCard` | `GetExtendedAgentCard` |
| Serialization basis | Pydantic / hand-written JSON schema | ProtoJSON (ADR-001) |

The well-known discovery path is `/.well-known/agent-card.json` in **both** 0.3 and 1.0 — that one did not change.

**Version negotiation (§3.6).** Versions are identified by `Major.Minor` only (`1.0`); patch numbers MUST NOT appear in requests, responses, or Agent Cards, and MUST NOT be considered in negotiation. Clients MUST send the `A2A-Version` header on every request. An **absent or empty `A2A-Version` header MUST be interpreted by the agent as `0.3`** — so a 1.0 client that forgets the header gets silently downgraded. Agents MUST process requests using the semantics of the requested version and MUST return `VersionNotSupportedError` for versions they don't serve. An agent MAY expose multiple interfaces at different `protocolVersion`s, on the same or different URLs.

---

## 2. Core concepts

| Term | Meaning |
|---|---|
| **A2A Client** | Initiates requests to a remote agent on behalf of a user or another system. |
| **A2A Server (Remote Agent)** | Exposes an A2A-compliant HTTP endpoint; processes tasks, returns responses. Internals stay opaque to the client. |
| **Agent Card** | JSON manifest: identity, interfaces, capabilities, skills, security requirements. The basis for discovery and routing. |
| **Message** | One turn of communication. Has a `role` (`ROLE_USER` / `ROLE_AGENT`) and one or more `Part`s. |
| **Task** | The stateful unit of work. Unique `id`, defined lifecycle, holds `status`, `artifacts`, `history`. |
| **Part** | Smallest content unit — text, file (bytes or URL), or structured JSON. Used inside Messages and Artifacts. |
| **Artifact** | A tangible output produced by a task, composed of Parts. |
| **Context** (`contextId`) | Server-generated identifier grouping related Tasks and Messages across a series of interactions. |
| **Extension** | Agent-declared functionality beyond the core spec, identified by URI. |

**A2A vs MCP.** MCP covers primitives with well-defined structured inputs and outputs performing specific, often stateless functions. A2A covers autonomous systems that reason, plan, use multiple tools, hold state across longer interactions, and engage in multi-turn dialogue. "A2A is about agents *partnering* on tasks, while MCP is more about agents *using* capabilities." They compose: an agent typically speaks A2A outward and uses MCP internally.

---

## 3. Agent Card

### 3.1 `AgentCard` fields

| Field | Type | Required | Notes |
|---|---|---|---|
| `name` | string | **Yes** | Human-readable. e.g. `"Recipe Agent"` |
| `description` | string | **Yes** | What the agent is for. Read by other agents when routing. |
| `supportedInterfaces` | `AgentInterface[]` | **Yes** | Ordered; **the first entry is the preferred one**. At least one. |
| `provider` | `AgentProvider` | No | `{ organization, url }` — both required if present |
| `version` | string | **Yes** | The *agent's* version, not the protocol's. e.g. `"1.2.0"` |
| `documentationUrl` | string | No | |
| `capabilities` | `AgentCapabilities` | **Yes** | |
| `securitySchemes` | map<string, `SecurityScheme`> | No | Named scheme definitions |
| `securityRequirements` | `SecurityRequirement[]` | No | Which schemes/scopes are required |
| `defaultInputModes` | string[] | **Yes** | Media types accepted, agent-wide |
| `defaultOutputModes` | string[] | **Yes** | Media types produced, agent-wide |
| `skills` | `AgentSkill[]` | **Yes** | At least one |
| `signatures` | `AgentCardSignature[]` | No | JWS signatures over the card |
| `iconUrl` | string | No | |

Note there is **no top-level `protocolVersion`** in 1.0 — protocol version is declared per interface inside `supportedInterfaces`.

### 3.2 `AgentInterface`

| Field | Type | Required | Notes |
|---|---|---|---|
| `url` | string | **Yes** | Absolute; HTTPS in production |
| `protocolBinding` | string | **Yes** | Open string. Officially: `JSONRPC`, `GRPC`, `HTTP+JSON`. Custom bindings SHOULD use a URI (§5.8). |
| `protocolVersion` | string | **Yes** | `Major.Minor`, e.g. `"1.0"`, `"0.3"` |
| `tenant` | string | No | Opaque routing id when several agents sit behind one endpoint. If set, clients MUST echo it in the `tenant` field of every request. |

### 3.3 `AgentCapabilities`

| Field | Type | Notes |
|---|---|---|
| `streaming` | bool | Supports `SendStreamingMessage` / `SubscribeToTask` |
| `pushNotifications` | bool | Supports webhook delivery |
| `extendedAgentCard` | bool | Supports `GetExtendedAgentCard` |
| `extensions` | `AgentExtension[]` | Declared protocol extensions |

Clients check these **before** calling. Declaring a capability you don't implement is a broken contract, not a harmless hint — see `UnsupportedOperationError` / `PushNotificationNotSupportedError` in §7.

### 3.4 `AgentSkill`

| Field | Type | Required |
|---|---|---|
| `id` | string | **Yes** |
| `name` | string | **Yes** |
| `description` | string | **Yes** |
| `tags` | string[] | **Yes** — at least one |
| `examples` | string[] | No — example prompts or payloads |
| `inputModes` | string[] | No — overrides `defaultInputModes` |
| `outputModes` | string[] | No — overrides `defaultOutputModes` |
| `securityRequirements` | `SecurityRequirement[]` | No — per-skill auth |

### 3.5 `AgentExtension`

`uri` (the identifier), `description`, `required` (bool — if true the client must comply), `params` (object).

### 3.6 `AgentCardSignature`

RFC 7515 JWS in JSON format: `protected` (base64url header, required), `signature` (base64url, required), `header` (unprotected values, object). Canonicalization rules for signing are in spec §8.4.

### 3.7 Sample card

```json
{
  "name": "GeoSpatial Route Planner Agent",
  "description": "Provides route planning, traffic analysis, and custom map generation.",
  "supportedInterfaces": [
    { "url": "https://georoute.example.com/a2a/v1",   "protocolBinding": "JSONRPC",   "protocolVersion": "1.0" },
    { "url": "https://georoute.example.com/a2a/grpc", "protocolBinding": "GRPC",      "protocolVersion": "1.0" },
    { "url": "https://georoute.example.com/a2a/json", "protocolBinding": "HTTP+JSON", "protocolVersion": "1.0" }
  ],
  "provider": { "organization": "Example Geo Services Inc.", "url": "https://www.examplegeoservices.com" },
  "iconUrl": "https://georoute.example.com/icon.png",
  "version": "1.2.0",
  "documentationUrl": "https://docs.examplegeoservices.com/georoute/api",
  "capabilities": { "streaming": true, "pushNotifications": true, "extendedAgentCard": true },
  "securitySchemes": {
    "google": {
      "openIdConnectSecurityScheme": {
        "openIdConnectUrl": "https://accounts.google.com/.well-known/openid-configuration"
      }
    }
  },
  "securityRequirements": [{ "schemes": { "google": { "list": ["openid", "profile", "email"] } } }],
  "defaultInputModes": ["application/json", "text/plain"],
  "defaultOutputModes": ["application/json", "image/png"],
  "skills": [
    {
      "id": "route-optimizer-traffic",
      "name": "Traffic-Aware Route Optimizer",
      "description": "Calculates the optimal driving route between two or more locations, accounting for real-time traffic, closures, and preferences such as avoiding tolls.",
      "tags": ["maps", "routing", "navigation", "traffic"],
      "examples": ["Plan a route from Mountain View to SFO avoiding tolls."],
      "inputModes": ["application/json", "text/plain"],
      "outputModes": ["application/json", "application/vnd.geo+json"]
    }
  ]
}
```

### Known spec inconsistency

The v1.0.1 published sample card writes the security field as `"security": [{ "google": [...] }]` (the 0.3 OpenAPI-style spelling), while `specification/a2a.proto` at the same tag defines `security_requirements` as `repeated SecurityRequirement`, where `SecurityRequirement` is `{ "schemes": map<string, StringList> }`. The generated SDK type stubs use `security_requirements`, and the spec's `main` branch corrected the sample to match. **Follow the proto: `securityRequirements` with the `schemes` / `list` wrapper**, as in the sample above. If interoperating with a specific peer, check what it actually parses.

---

## 4. Data model

### 4.1 `Task`

| Field | Type | Required |
|---|---|---|
| `id` | string | **Yes** — server-generated, e.g. UUID |
| `contextId` | string | No — groups related tasks/messages |
| `status` | `TaskStatus` | **Yes** |
| `artifacts` | `Artifact[]` | No |
| `history` | `Message[]` | No |
| `metadata` | object | No |

### 4.2 `TaskStatus`

`state` (`TaskState`, required), `message` (`Message`), `timestamp` (ISO 8601 UTC).

### 4.3 `TaskState`

| Value | Kind |
|---|---|
| `TASK_STATE_UNSPECIFIED` | unknown / indeterminate |
| `TASK_STATE_SUBMITTED` | acknowledged, queued |
| `TASK_STATE_WORKING` | actively processing |
| `TASK_STATE_INPUT_REQUIRED` | **interrupted** — needs more user input |
| `TASK_STATE_AUTH_REQUIRED` | **interrupted** — needs authentication |
| `TASK_STATE_COMPLETED` | **terminal** — success |
| `TASK_STATE_FAILED` | **terminal** — error |
| `TASK_STATE_CANCELED` | **terminal** — canceled before completion |
| `TASK_STATE_REJECTED` | **terminal** — agent declined the work |

Terminal states close streams and reject further messages. Interrupted states do not.

### 4.4 `Message`

| Field | Type | Required |
|---|---|---|
| `messageId` | string | **Yes** — set by the creator |
| `role` | `Role` | **Yes** — `ROLE_USER` (client→server) or `ROLE_AGENT` (server→client) |
| `parts` | `Part[]` | **Yes** |
| `contextId` | string | No |
| `taskId` | string | No |
| `metadata` | object | No |
| `extensions` | string[] | No — extension URIs present in this message |
| `referenceTaskIds` | string[] | No — other tasks referenced for context |

For server messages `contextId` must be set (and `taskId` if a task exists). For client messages both are optional, but if both are given they must agree; given only `taskId`, the server infers `contextId`.

### 4.5 `Part`

A `oneof` over exactly one content field, plus shared metadata:

| Field | Type | Notes |
|---|---|---|
| `text` | string | *oneof* — text content |
| `raw` | bytes | *oneof* — file bytes; base64 in JSON serialization |
| `url` | string | *oneof* — pointer to file content |
| `data` | JSON value | *oneof* — arbitrary structured data |
| `mediaType` | string | MIME type; valid for **all** part kinds |
| `filename` | string | e.g. `"document.pdf"` |
| `metadata` | object | |

### 4.6 `Artifact`

`artifactId` (required, unique within the task), `name`, `description`, `parts` (required, ≥1), `metadata`, `extensions`.

### 4.7 Streaming events

**`TaskStatusUpdateEvent`** — `taskId` (req), `contextId` (req), `status` (req), `metadata`.

**`TaskArtifactUpdateEvent`** — `taskId` (req), `contextId` (req), `artifact` (req), `append` (bool — append to a previously sent artifact with the same id), `lastChunk` (bool), `metadata`.

**`StreamResponse`** wraps a oneof of `task` / `message` / `statusUpdate` / `artifactUpdate`.

Stream shape (§3.1.2): if the agent responds with a `Message`, the stream contains exactly that one object and closes. If it responds with a `Task`, the stream begins with the Task, then zero or more update events, and MUST close when the task reaches a terminal state.

### 4.8 Push notification objects

**`TaskPushNotificationConfig`** — `url` (required, the webhook), `id`, `taskId`, `token` (unique per task/session), `authentication` (`AuthenticationInfo`), `tenant`.

**`AuthenticationInfo`** — `scheme` (required, IANA HTTP auth scheme, e.g. `Bearer`), `credentials`.

The agent POSTs `StreamResponse` payloads to the webhook. Configs persist until task completion or explicit deletion. Security guidance is in spec §13.2 — webhook URL validation and replay protection matter here.

---

## 5. Operations and method mapping

| Operation | JSON-RPC method | gRPC method | REST endpoint |
|---|---|---|---|
| Send message | `SendMessage` | `SendMessage` | `POST /message:send` |
| Send streaming message | `SendStreamingMessage` | `SendStreamingMessage` | `POST /message:stream` |
| Get task | `GetTask` | `GetTask` | `GET /tasks/{id}` |
| List tasks | `ListTasks` | `ListTasks` | `GET /tasks` |
| Cancel task | `CancelTask` | `CancelTask` | `POST /tasks/{id}:cancel` |
| Subscribe to task | `SubscribeToTask` | `SubscribeToTask` | `POST /tasks/{id}:subscribe` |
| Create push config | `CreateTaskPushNotificationConfig` | same | `POST /tasks/{id}/pushNotificationConfigs` |
| Get push config | `GetTaskPushNotificationConfig` | same | `GET /tasks/{id}/pushNotificationConfigs/{configId}` |
| List push configs | `ListTaskPushNotificationConfigs` | same | `GET /tasks/{id}/pushNotificationConfigs` |
| Delete push config | `DeleteTaskPushNotificationConfig` | same | `DELETE /tasks/{id}/pushNotificationConfigs/{configId}` |
| Get extended card | `GetExtendedAgentCard` | same | `GET /extendedAgentCard` |

When an agent supports several bindings they MUST be functionally equivalent: same operations, semantically equivalent results, consistent error mapping, same auth schemes (§5.1).

### 5.1 `SendMessageRequest`

`message` (required), `configuration` (`SendMessageConfiguration`), `metadata`, `tenant`.

### 5.2 `SendMessageConfiguration`

| Field | Notes |
|---|---|
| `acceptedOutputModes` | Media types the client will accept back |
| `taskPushNotificationConfig` | Register a webhook inline; leave `taskId` empty here |
| `historyLength` | Max recent history messages to return. Unset = no client limit; `0` = none. Server MUST NOT exceed it but MAY return fewer. |
| `returnImmediately` | **Defaults to `false`, i.e. blocking.** `false` waits for a terminal or interrupted state before returning; `true` returns as soon as the task is created. No effect on direct `Message` responses or on streaming. |

### 5.3 `ListTasks`

Filters: `contextId`, `status` (a `TaskState`), `statusTimestampAfter`, `historyLength`, `includeArtifacts` (default `false` — when false the `artifacts` field MUST be omitted entirely, not sent as `[]` or `null`). Pagination is **cursor-based**: `pageSize` (default 50, min 1, max 100) and `pageToken`. Results MUST be sorted by status timestamp descending. `nextPageToken` MUST always be present, set to `""` on the last page. Response also carries `pageSize` and `totalSize`.

---

## 6. JSON-RPC binding (§9)

- JSON-RPC 2.0 over HTTP(S), `Content-Type: application/json`.
- Method names are PascalCase matching the gRPC names.
- Streaming is Server-Sent Events, `Content-Type: text/event-stream`.

```http
POST /rpc HTTP/1.1
Host: agent.example.com
Content-Type: application/json
Authorization: Bearer token
A2A-Version: 1.0
A2A-Extensions: https://example.com/extensions/geolocation/v1

{ "jsonrpc": "2.0", "id": 1, "method": "SendMessage", "params": { /* SendMessageRequest */ } }
```

Response `result` is a `SendMessageResponse` — a oneof of `task` or `message`. Streaming responses arrive as `data:` lines each carrying a full JSON-RPC envelope whose `result` is a `StreamResponse`.

### Service parameters (§3.2.6)

Transmitted as HTTP headers in HTTP-based bindings (gRPC metadata for gRPC). Names are case-insensitive; all spec-defined ones are prefixed `a2a-`.

| Header | Purpose |
|---|---|
| `A2A-Version` | Protocol version in use. Absent/empty ⇒ agent MUST assume `0.3`. |
| `A2A-Extensions` | Comma-separated extension URIs the client wants active for this request |

---

## 7. Errors

| A2A error | JSON-RPC | gRPC | HTTP |
|---|---|---|---|
| `TaskNotFoundError` | `-32001` | `NOT_FOUND` | 404 |
| `TaskNotCancelableError` | `-32002` | `FAILED_PRECONDITION` | 400 |
| `PushNotificationNotSupportedError` | `-32003` | `FAILED_PRECONDITION` | 400 |
| `UnsupportedOperationError` | `-32004` | `FAILED_PRECONDITION` | 400 |
| `ContentTypeNotSupportedError` | `-32005` | `INVALID_ARGUMENT` | 400 |
| `InvalidAgentResponseError` | `-32006` | `INTERNAL` | 500 |
| `ExtendedAgentCardNotConfiguredError` | `-32007` | `FAILED_PRECONDITION` | 400 |
| `ExtensionSupportRequiredError` | `-32008` | `FAILED_PRECONDITION` | 400 |
| `VersionNotSupportedError` | `-32009` | `FAILED_PRECONDITION` | 400 |

Standard JSON-RPC codes (`-32700` parse error, `-32600` invalid request, `-32601` method not found, `-32602` invalid params, `-32603` internal error) apply as usual.

---

## 8. Discovery (§8)

Three strategies, all legitimate:

1. **Well-known URI** — `GET https://{domain}/.well-known/agent-card.json`. IANA-registered URI suffix `agent-card.json`; the resource MUST return an `AgentCard`. Best for public or domain-controlled discovery.
2. **Curated registry** — an intermediary holding a searchable collection of cards, filterable by skill or tag. Adds governance and access control at the cost of running a registry.
3. **Direct configuration** — hardcoded URLs, config files, env vars. Fine for tightly coupled systems; inflexible for dynamic ones.

**Caching (§8.6).** Servers SHOULD send `Cache-Control: max-age=…` and an `ETag` derived from the card `version` or a content hash; MAY send `Last-Modified`. Clients SHOULD honour RFC 9111 semantics and use conditional requests (`If-None-Match` / `If-Modified-Since`) on revalidation.

**Card security.** Cards may leak internal URLs and skill detail. Protect sensitive detail behind the authenticated extended card (`capabilities.extendedAgentCard: true` + `GetExtendedAgentCard`), which MAY return different content per client identity. Use out-of-band dynamic credentials — **never embed static secrets in a card**.

---

## 9. Security schemes (§4.5)

`SecurityScheme` is a discriminated union modelled on the OpenAPI 3.2 Security Scheme Object. Keyed in the card's `securitySchemes` map by a name you choose; referenced from `securityRequirements`.

| Scheme key | Fields |
|---|---|
| `apiKeySecurityScheme` | `location` (`query` \| `header` \| `cookie`, req), `name` (req), `description` |
| `httpAuthSecurityScheme` | `scheme` (req, RFC 7235 e.g. `Bearer`), `bearerFormat`, `description` |
| `oauth2SecurityScheme` | `flows` (req), `oauth2MetadataUrl` (RFC 8414, TLS required), `description` |
| `openIdConnectSecurityScheme` | `openIdConnectUrl` (req), `description` |
| `mtlsSecurityScheme` | `description` |

`OAuthFlows` is a oneof: `authorizationCode` (`authorizationUrl`, `tokenUrl`, `refreshUrl`, `scopes`, `pkceRequired`), `clientCredentials` (`tokenUrl`, `refreshUrl`, `scopes`), `deviceCode` (`deviceAuthorizationUrl`, `tokenUrl`, `refreshUrl`, `scopes`), plus **deprecated** `implicit` and `password` — prefer authorization code + PKCE, or device code for input-constrained clients.

`SecurityRequirement` = `{ "schemes": { "<schemeName>": { "list": ["scope1", "scope2"] } } }`.

Authentication itself happens in transport headers, outside the A2A payload. The protocol declares requirements; it does not carry credentials in the body.

**In-task authorization (§7.6).** When an agent needs credentials mid-task for a downstream resource, it moves the task to `TASK_STATE_AUTH_REQUIRED` rather than failing, and the client supplies credentials out of band before continuing.

---

## 10. Extensions (§4.6)

Declared on the card under `capabilities.extensions` as `AgentExtension` objects (`uri`, `description`, `required`, `params`). Clients opt in per request via the `A2A-Extensions` service parameter (HTTP header / gRPC metadata). Extension data rides in the `extensions` array plus a `metadata` object keyed by the extension URI, on **Messages** and on **Artifacts**.

```json
{
  "role": "ROLE_USER",
  "parts": [{ "text": "Find restaurants near me" }],
  "extensions": ["https://example.com/extensions/geolocation/v1"],
  "metadata": {
    "https://example.com/extensions/geolocation/v1": {
      "latitude": 37.7749, "longitude": -122.4194, "accuracy": 10.0
    }
  }
}
```

An extension marked `required: true` means clients that don't understand it must not proceed; the agent returns `ExtensionSupportRequiredError` otherwise.

---

## 11. JSON conventions

- **Field names:** camelCase in JSON, always (`protocolVersion`, `contextId`, `defaultInputModes`, `pushNotificationConfig`) — never the proto's snake_case.
- **Enums:** ProtoJSON string names, i.e. SCREAMING_SNAKE_CASE (`"TASK_STATE_INPUT_REQUIRED"`, `"ROLE_USER"`).
- **Timestamps:** ISO 8601, UTC with `Z` suffix, millisecond precision where available — `YYYY-MM-DDTHH:mm:ss.sssZ`. No non-`Z` offsets.
- **Unknown fields:** implementations SHOULD ignore them, for forward compatibility.
- **Media type:** `application/a2a+json` is IANA-registered for A2A payloads.
