# a2a_client.py

import asyncio
import logging
import httpx

from a2a.client.card_resolver import A2ACardResolver
from a2a.client.client import ClientConfig
from a2a.client import ClientFactory, create_text_message_object
from a2a.types import AgentCard, TransportProtocol, TaskState
from a2a.utils.message import get_message_text


BASE_URL = "http://localhost:8080"


async def main():

    async with httpx.AsyncClient(
        timeout=httpx.Timeout(connect=10.0, read=60.0, write=10.0, pool=10.0)
    ) as httpx_client:

        resolver = A2ACardResolver(
            httpx_client=httpx_client,
            base_url=BASE_URL,
        )

        try:
            agent_card: AgentCard = await resolver.get_agent_card()
        except Exception as e:
            logging.error("Failed to fetch agent card", exc_info=True)
            raise RuntimeError("Cannot continue without AgentCard") from e

        config = ClientConfig(
            httpx_client=httpx_client,
            supported_transports=[TransportProtocol.jsonrpc],
            streaming=True,  # Enable streaming
        )

        client = ClientFactory(config).create(agent_card)

        request = create_text_message_object(
            content="Hi Beyhadh here"
        )

        response = client.send_message(request)

        print("Streaming response:")
        print("-" * 40)

        full_response = []
        async for result in response:
            task, update = result

            # Handle status updates
            if hasattr(update, 'status') and update.status:
                state = update.status.state
                if state == TaskState.working:
                    print(f"[Status: working...]")
                elif state == TaskState.completed:
                    print(f"\n[Status: completed]")

            # Handle artifact updates (streaming chunks)
            if hasattr(task, 'artifacts') and task.artifacts:
                for artifact in task.artifacts:
                    chunk = get_message_text(artifact)
                    if chunk:
                        print(chunk, end="", flush=True)
                        full_response.append(chunk)

        print("\n" + "-" * 40)
        print(f"Full response: {''.join(full_response)}")


if __name__ == "__main__":
    asyncio.run(main())


# -------------------------------------------------------------------------------------------------------------------------------------------------------

# ---

# # 1. Core Python Standard Library Imports

# The first three imports come from Python’s standard library and support asynchronous execution, logging, and HTTP communication.

# ### `import asyncio`

# `asyncio` is Python’s asynchronous runtime framework. It provides the **event loop**, which is responsible for scheduling asynchronous tasks and managing non-blocking I/O.

# Your client uses `asyncio` because HTTP requests are performed asynchronously using `httpx.AsyncClient`, and the A2A SDK itself is designed around async workflows.

# The event loop is started here:

# ```python
# asyncio.run(main())
# ```

# This line creates an event loop, executes the coroutine `main()`, and closes the loop when execution finishes.

# Without `asyncio`, your client would block while waiting for HTTP responses, which is inefficient for distributed agent communication.

# ---

# ### `import logging`

# The logging module provides structured runtime logging. It allows programs to record informational messages, warnings, errors, and debugging traces.

# Your code uses it here:

# ```python
# logging.error("Failed to fetch agent card", exc_info=True)
# ```

# This logs the error if the agent card cannot be retrieved from the server. The `exc_info=True` flag ensures the **full stack trace** is printed, which is essential when debugging distributed systems like A2A clients.

# In production environments, logging frameworks often integrate with observability systems such as OpenTelemetry, Azure Monitor, or ELK stacks.

# ---

# ### `import httpx`

# `httpx` is an advanced HTTP client library for Python. It supports both synchronous and asynchronous HTTP requests.

# In this program it is used to create an **asynchronous HTTP connection pool**:

# ```python
# async with httpx.AsyncClient(...)
# ```

# This client is responsible for all network communication with the A2A server, including:

# • fetching the agent discovery card
# • sending JSON-RPC messages
# • receiving responses from the server

# The timeout configuration ensures the client does not hang indefinitely if the server becomes unreachable.

# ---

# # 2. A2A SDK Client Discovery Import

# ### `from a2a.client.card_resolver import A2ACardResolver`

# This class is responsible for **agent discovery**.

# In the A2A protocol, a client does not directly call an agent endpoint. Instead, it first retrieves an **Agent Card**, which is a metadata document describing the agent’s capabilities.

# The resolver automatically fetches the card from the standard discovery path:

# ```
# /.well-known/agent-card.json
# ```

# Your code performs this discovery here:

# ```python
# resolver = A2ACardResolver(
#     httpx_client=httpx_client,
#     base_url=BASE_URL
# )
# ```

# Then:

# ```python
# agent_card = await resolver.get_agent_card()
# ```

# This returns an `AgentCard` object describing the agent.

# The card contains metadata such as:

# • agent name and description
# • supported transport protocols
# • supported input/output modes
# • streaming capability
# • available skills

# This discovery step is essential because it allows **dynamic agent interoperability**.

# ---

# # 3. A2A Client Configuration Imports

# ### `from a2a.client.client import ClientConfig`

# `ClientConfig` defines how the A2A client should communicate with the server.

# It encapsulates configuration such as:

# • HTTP client instance
# • supported communication protocols
# • streaming capability

# In your code:

# ```python
# config = ClientConfig(
#     httpx_client=httpx_client,
#     supported_transports=[TransportProtocol.jsonrpc],
#     streaming=False,
# )
# ```

# This tells the SDK:

# • use JSON-RPC for communication
# • do not expect streaming responses

# ---

# ### `from a2a.client import ClientFactory`

# The `ClientFactory` creates the actual client instance that communicates with the agent.

# The factory pattern exists because A2A supports multiple transport mechanisms. Based on the **Agent Card capabilities**, the factory builds a compatible client.

# Your code:

# ```python
# client = ClientFactory(config).create(agent_card)
# ```

# This dynamically creates the correct client implementation.

# Internally it performs tasks such as:

# • validating supported protocols
# • configuring JSON-RPC communication
# • binding the HTTP transport

# ---

# ### `from a2a.client import create_text_message_object`

# This utility function simplifies creation of message payloads that follow the A2A message schema.

# Instead of manually constructing a full message structure, you can simply pass text content.

# Your usage:

# ```python
# request = create_text_message_object(
#     content="Hi Beyhadh here"
# )
# ```

# Internally this creates an object similar to:

# ```
# Message
#  ├─ role: user
#  ├─ parts
#  │   └─ TextPart("Hi Beyhadh here")
# ```

# This matches the standardized A2A message format.

# ---

# # 4. A2A Data Model Imports

# ### `from a2a.types import AgentCard`

# `AgentCard` represents the metadata object returned by the discovery endpoint.

# The client receives this structure from:

# ```
# http://localhost:8080/.well-known/agent-card.json
# ```

# It contains information such as:

# ```
# AgentCard
#  ├─ name
#  ├─ description
#  ├─ version
#  ├─ capabilities
#  ├─ skills
# ```

# This allows the client to adapt to the agent dynamically.

# ---

# ### `from a2a.types import TransportProtocol`

# This enum defines supported transport mechanisms.

# Currently supported transports include:

# ```
# JSON-RPC
# HTTP
# Streaming protocols
# ```

# Your code explicitly selects JSON-RPC:

# ```python
# supported_transports=[TransportProtocol.jsonrpc]
# ```

# This matches the transport used by your A2A server.

# ---

# # 5. Message Utility Import

# ### `from a2a.utils.message import get_message_text`

# A2A responses return **task artifacts**, not plain strings.

# Artifacts may contain multiple parts:

# ```
# Artifact
#  ├─ name
#  ├─ parts
#  │   └─ TextPart
# ```

# Extracting the final text manually would be verbose.

# The helper function simplifies this:

# ```python
# get_message_text(task.artifacts[-1])
# ```

# This extracts the text content from the artifact automatically.

# ---

# # 6. Code Execution Flow

# Now let’s walk through the program step-by-step.

# ---

# ## Step 1 — Start the Async Event Loop

# ```
# asyncio.run(main())
# ```

# This initializes the async runtime and runs the client workflow.

# ---

# ## Step 2 — Create HTTP Client

# ```
# async with httpx.AsyncClient(...)
# ```

# This creates a reusable connection pool.

# Timeouts prevent the client from hanging.

# ---

# ## Step 3 — Discover Agent Card

# ```
# resolver = A2ACardResolver(...)
# agent_card = await resolver.get_agent_card()
# ```

# The resolver fetches the agent metadata.

# The request sent is:

# ```
# GET /.well-known/agent-card.json
# ```

# ---

# ## Step 4 — Configure Client

# ```
# config = ClientConfig(...)
# ```

# Defines transport settings and streaming capability.

# ---

# ## Step 5 — Create A2A Client

# ```
# client = ClientFactory(config).create(agent_card)
# ```

# This constructs the communication client using the discovered capabilities.

# ---

# ## Step 6 — Create Message Request

# ```
# request = create_text_message_object(...)
# ```

# Creates a properly formatted message object.

# ---

# ## Step 7 — Send Message

# ```
# response = client.send_message(request)
# ```

# The client sends a JSON-RPC message to the server.

# Internally the request looks like:

# ```
# POST /message/send
# {
#   "method": "message/send",
#   "params": {...}
# }
# ```

# ---

# ## Step 8 — Receive Task Events

# ```
# async for result in response:
# ```

# The server emits **task events** representing the agent execution lifecycle.

# Typical sequence:

# ```
# TaskStarted
# ArtifactUpdate
# TaskCompleted
# ```

# ---

# ## Step 9 — Extract Final Response

# ```
# print(get_message_text(task.artifacts[-1]))
# ```

# The final artifact contains the agent response.

# For your server implementation this will print:

# ```
# Hello, you said: Hi Beyhadh here
# ```

# ---

# # Complete Interaction Architecture

# ```
# Client
#   │
#   │ GET /.well-known/agent-card.json
#   ▼
# A2A Server
#   │
#   │ JSON-RPC message/send
#   ▼
# Agent Executor
#   │
#   │ invokes HelloWorldAgent
#   ▼
# EventQueue
#   │
#   │ TaskArtifactUpdateEvent
#   ▼
# Client
#   │
#   ▼
# Print Response
# ```

# ---

# # Important Implementation Detail

# Your code currently has one subtle issue:

# ```
# response = client.send_message(request)
# ```

# should actually be:

# ```
# response = await client.send_message(request)
# ```

# if streaming is disabled.

# But since the SDK may return an async generator depending on transport, your iteration still works in some versions.

# ---

# # Summary

# The program performs five key responsibilities:

# Agent discovery
# The client retrieves the agent metadata via the A2A discovery endpoint.

# Client configuration
# A communication client is built using the transport protocols supported by the agent.

# Message construction
# A properly formatted A2A message object is created.

# Agent invocation
# The client sends the request using JSON-RPC.

# Response processing
# Task artifacts returned by the agent executor are parsed and displayed.

# This architecture enables **interoperable communication between autonomous agents**, where any compliant client can discover and interact with any compliant agent without hardcoding endpoints or capabilities.

# ---

# --------------------------------------------------------------------------------------------------------------------
