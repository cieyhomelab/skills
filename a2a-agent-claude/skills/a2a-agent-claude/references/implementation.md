# Building an A2A Agent — SDK Patterns and Gotchas

Companion to `protocol.md`, which holds the wire format. This file covers how to actually build one. Everything here is A2A **v1.0**; see §4 for what changed from 0.3 and why it matters more than usual.

---

## 1. Official SDKs

Maintained under <https://github.com/a2aproject>. Versions verified August 2026 — check the repo before pinning, these move.

| Language | Repo | Package | Latest verified |
|---|---|---|---|
| Python | `a2aproject/a2a-python` | `a2a-sdk` (PyPI) | 1.1.3 |
| JS / TS | `a2aproject/a2a-js` | `@a2a-js/sdk` (npm) | 1.0.1 |
| Java | `a2aproject/a2a-java` | | 1.2.0.Final |
| Go | `a2aproject/a2a-go` | | 2.5.0 (module versioning differs from spec versioning) |
| .NET | `a2aproject/a2a-dotnet` | | see repo |
| Rust | `a2aproject/a2a-rust` | | see repo |

Python is the most complete: JSON-RPC, HTTP+JSON/REST, and gRPC on both client and server for spec 1.0, plus a 0.3 compatibility layer for all three.

Python extras: `a2a-sdk[http-server]` (Starlette), `[fastapi]`, `[grpc]`, `[telemetry]`, `[sql]` / `[postgresql]` / `[mysql]` / `[sqlite]` for a durable task store, `[all]`.

Samples in several languages: <https://github.com/a2aproject/a2a-samples>.

---

## 2. Server skeleton (Python, spec 1.0)

Four pieces, in the order worth writing them.

### 2.1 The Agent Card

Written first — it is the contract everything else has to satisfy.

```python
from a2a.types import AgentCapabilities, AgentCard, AgentInterface, AgentSkill

skill = AgentSkill(
    id='echo_bot',
    name='Echo Bot',
    description='Acknowledges a client request and responds with a Hello World message.',
    tags=['a2a', 'echo-example'],
    examples=['hi', 'how are you'],
    input_modes=['text/plain'],
    output_modes=['text/plain'],
)

agent_card = AgentCard(
    name='Hello World Agent',
    description='Just a hello world agent',
    version='0.0.1',
    default_input_modes=['text/plain'],
    default_output_modes=['text/plain'],
    capabilities=AgentCapabilities(streaming=True),
    supported_interfaces=[
        AgentInterface(
            protocol_binding='JSONRPC',
            url='http://127.0.0.1:9999',
            protocol_version='1.0',
        )
    ],
    skills=[skill],
)
```

The SDK types are protobuf messages, so Python-side attributes are `snake_case` (`default_input_modes`) while the JSON on the wire is camelCase (`defaultInputModes`). That translation is automatic — don't fight it, and don't assume the Python attribute name is the wire name when debugging a peer.

### 2.2 The executor

One class. Receive context, create or resume the Task, push status, attach artifacts, land in a terminal state.

```python
from a2a.helpers import (
    get_message_text, new_task_from_user_message, new_text_message, new_text_part,
)
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import TaskState


class HelloWorldAgentExecutor(AgentExecutor):
    def __init__(self) -> None:
        self.agent = HelloWorldAgent()

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        # 1. Resume an existing task, or create one and enqueue it.
        task = context.current_task
        if task is None:
            task = new_task_from_user_message(context.message)
            await event_queue.enqueue_event(task)

        updater = TaskUpdater(
            event_queue=event_queue, task_id=task.id, context_id=task.context_id
        )

        # 2. Signal work started.
        await updater.update_status(
            state=TaskState.TASK_STATE_WORKING,
            message=new_text_message('Processing request...'),
        )

        # 3. Do the actual work.
        query = get_message_text(context.message)
        result = await self.agent.invoke(query) if query else 'No text input provided.'

        # 4. Emit output as an artifact.
        await updater.add_artifact(parts=[new_text_part(text=result, media_type='text/plain')])

        # 5. Land in a terminal state. Non-negotiable — see §5.
        await updater.update_status(
            state=TaskState.TASK_STATE_COMPLETED,
            message=new_text_message('Request is completed!'),
        )

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise NotImplementedError('Cancel is not supported.')
```

Raising `NotImplementedError` from `cancel` is an honest answer when the work genuinely can't be interrupted — better than a stub that returns success and cancels nothing. If cancellation *is* supported, drive the task to `TASK_STATE_CANCELED`.

### 2.3 Server wiring

```python
import uvicorn
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import create_agent_card_routes, create_jsonrpc_routes
from a2a.server.tasks import InMemoryTaskStore
from starlette.applications import Starlette

request_handler = DefaultRequestHandler(
    agent_executor=HelloWorldAgentExecutor(),
    task_store=InMemoryTaskStore(),
    agent_card=agent_card,
    # extended_agent_card=extended_card,   # only if capabilities.extended_agent_card
)

routes = []
routes.extend(create_agent_card_routes(agent_card))          # serves /.well-known/agent-card.json
routes.extend(create_jsonrpc_routes(request_handler, '/'))   # or create_rest_routes / gRPC

app = Starlette(routes=routes)
uvicorn.run(app, host='127.0.0.1', port=9999)
```

Route factories rather than a monolithic app class — that's the 1.0 shape, and it means A2A routes can mount into an existing Starlette or FastAPI app alongside your own middleware. `InMemoryTaskStore` is for development; use a SQL-backed store for anything that must survive a restart, which is most things once push notifications or long tasks are in play.

The `url` in `supported_interfaces` is what clients will actually dial. Behind a proxy or in a container it must be the externally reachable URL, not `127.0.0.1` — a card advertising localhost is the single most common reason a working agent is unreachable.

### 2.4 Client

```python
import httpx
from a2a.client import A2ACardResolver, ClientConfig, create_client
from a2a.helpers import new_text_message
from a2a.types import Role, SendMessageRequest

async with httpx.AsyncClient() as httpx_client:
    resolver = A2ACardResolver(
        httpx_client=httpx_client,
        base_url='http://127.0.0.1:9999',
        # agent_card_path='...'   # only if the agent doesn't use the well-known path
    )
    card = await resolver.get_agent_card()

client = await create_client(agent=card, client_config=ClientConfig(streaming=False))
request = SendMessageRequest(message=new_text_message('Hi there', role=Role.ROLE_USER))

async for chunk in client.send_message(request):
    print(chunk)

await client.close()
```

The client is constructed *from the card*, which is how it picks the interface and binding — another reason the card has to be right before anything else works. `ClientConfig(streaming=True)` switches to `SendStreamingMessage`; the consumption loop is the same `async for`.

`a2a.helpers.display_agent_card(card)` prints a readable summary — useful for eyeballing a peer's card during integration.

### 2.5 Other languages

The concepts map across all SDKs — card, executor, request handler, task store, routes — but the APIs differ. Don't transliterate the Python above into JS or Go from memory; read that SDK's README and its sample under `a2a-samples/samples/<lang>/`. Getting a method name wrong there produces a confusing runtime failure rather than a clean type error.

---

## 3. Choosing the pieces

**Binding.** `JSONRPC` is the default worth starting from — simplest to debug, widest support, plain HTTP + SSE. `GRPC` for internal service meshes where you already have the tooling. `HTTP+JSON` when the consumers are REST-native. Multiple bindings are allowed but the spec requires functional equivalence across all of them, so each one is ongoing work, not a free checkbox.

**Task vs Message.** `SendMessage` may return a bare `Message` instead of creating a `Task`. For a stateless Q&A agent that answers in one shot, that's the right answer and skips the whole task store. Create a Task when work is long-running, resumable, cancelable, or multi-turn.

**Blocking vs immediate.** `SendMessageConfiguration.returnImmediately` defaults to `false` — blocking until terminal or interrupted. If tasks run long and the caller shouldn't hold a connection, the client sets `returnImmediately: true` and then polls `GetTask`, subscribes via `SubscribeToTask`, or receives push notifications.

**Update delivery.** Streaming (SSE) for interactive callers wanting incremental output. Polling `GetTask` for simplicity. Push notifications for genuinely long or disconnected work — real webhook plumbing, and the security requirements in spec §13.2 (URL validation, replay protection, authenticating the notification) are not optional if the webhook is internet-facing.

**Task store.** In-memory is fine for a demo and wrong for anything else. Once a task can outlive a request, restart, or process, it needs to be persisted.

---

## 4. The v0.3 → v1.0 migration

This is where most A2A bugs come from. Model recall, tutorials, and existing code are largely 0.3. `protocol.md` §1 has the full wire-level table; this is the code-level view for the Python SDK.

**Enums.** Every one changed to SCREAMING_SNAKE_CASE.

| | v0.3 | v1.0 |
|---|---|---|
| `TaskState` | `TaskState.working` | `TaskState.TASK_STATE_WORKING` |
| `TaskState` | `TaskState.input_required` | `TaskState.TASK_STATE_INPUT_REQUIRED` |
| `Role` | `Role.user` | `Role.ROLE_USER` |

**Part construction.** The wrapper types are gone; content fields sit directly on `Part`.

| Kind | v0.3 | v1.0 |
|---|---|---|
| Text | `Part(TextPart(text=...))` | `Part(text=...)` |
| File (bytes) | `Part(FilePart(file=FileWithBytes(bytes=<base64>, ...)))` | `Part(raw=<bytes>, media_type=..., filename=...)` |
| File (URI) | `Part(FilePart(file=FileWithUri(uri=..., ...)))` | `Part(url=..., media_type=...)` |
| Structured | `Part(DataPart(data={...}))` | `Part(data=<protobuf Value>)` |

Two consequences: file bytes no longer need manual base64 (protobuf handles it), and `Part.data` is a `google.protobuf.Value`, so a Python dict must go through `ParseDict` rather than being assigned directly.

**Types layer.** Pydantic models → protobuf-generated classes, with ProtoJSON as the canonical serialization. Protobuf semantics come along: `HasField` for presence checks on message fields, and unset scalars read as zero values rather than `None`.

**Server setup.** Monolithic application classes → Starlette route factories (`create_agent_card_routes`, `create_jsonrpc_routes`, …), mountable into an existing app.

**Serving 0.3 clients.** The Python SDK ships `a2a.compat.v0_3` with adapters, converters, and handlers for all three bindings. An agent can expose a 0.3 interface and a 1.0 interface side by side — declare both in `supported_interfaces` with the right `protocol_version`. Full guide: `docs/migrations/v1_0/README.md` in `a2aproject/a2a-python`.

**The silent trap.** An agent MUST treat a missing or empty `A2A-Version` header as `0.3`. A 1.0 client that omits the header gets 0.3 semantics with no error raised — it just behaves subtly wrong. Send the header.

---

## 5. Failure modes worth checking for

- **A capability declared but not implemented.** `capabilities.streaming: true` with no streaming path, or `pushNotifications: true` with no sender. Clients read these before calling and will fail on the promise, not on your code.
- **A task that never terminates.** Every path through `execute`, including exceptions, must land in `COMPLETED`, `FAILED`, `CANCELED`, or `REJECTED`. A task stuck in `WORKING` hangs a blocking caller and leaves a stream open forever. Wrap the body and drive to `FAILED` on error.
- **A card advertising an unreachable URL.** `127.0.0.1` or a container-internal hostname in `supported_interfaces[].url`.
- **0.3 spellings leaking into 1.0 output.** Lowercase `"working"`, `"user"`, a `"kind"` discriminator on parts, `preferredTransport` on the card, `message/send` as a method name. Any of these means something was written from memory.
- **Static secrets in the Agent Card.** The card is usually public. Use out-of-band credentials; put sensitive skill detail behind the authenticated extended card.
- **Vague skill descriptions.** Not a spec violation, but the card is the entire basis on which a stranger's agent decides to route work here. `"Handles requests"` gets no traffic and deserves none.
- **Overreach on artifacts.** Intermediate progress belongs in status messages; `Artifact`s are the task's actual outputs.

---

## 6. Verification

**Fetch and eyeball the card.**

```bash
curl -s http://127.0.0.1:9999/.well-known/agent-card.json | python -m json.tool
```

Check: enums SCREAMING_SNAKE, fields camelCase, `supportedInterfaces[].url` externally reachable, `protocolVersion` matching what you built, no secrets, `securityRequirements` referencing only defined `securitySchemes`.

**Drive one real request end to end.** A card that serves is not an agent that works. Send a message, watch it reach a terminal state, confirm the artifact comes back.

**a2a-inspector** — <https://github.com/a2aproject/a2a-inspector> — is the official interactive tool for validating an agent and inspecting its card and traffic. Prefer it to a hand-rolled conformance checker.

**Interoperability.** If a specific peer matters, test against that peer. The spec has room for implementations to diverge (see the `securityRequirements` inconsistency in `protocol.md` §3), and only a real exchange settles it.
