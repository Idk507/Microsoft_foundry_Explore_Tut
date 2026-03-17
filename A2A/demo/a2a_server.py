# a2a_server.py

class HelloWorldAgent:
    async def invoke_agent(self, user_query: str) -> str:
        return f"Hello, you said: {user_query}"


from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.types import (
    TaskArtifactUpdateEvent,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
)
from a2a.utils import new_text_artifact


class HelloWorldAgentExecutor(AgentExecutor):

    def __init__(self):
        self.agent = HelloWorldAgent()

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        query = context.get_user_input()

        # Simulate streaming by sending incremental updates
        response_text = f"Hello, you said: {query}"

        # Send working status first
        working_status = TaskStatusUpdateEvent(
            context_id=context.context_id,
            task_id=context.task_id,
            status=TaskStatus(state=TaskState.working),
            final=False,
        )
        await event_queue.enqueue_event(working_status)

        # Stream the response character by character (or word by word)
        for i, chunk in enumerate(response_text.split()):
            partial_artifact = TaskArtifactUpdateEvent(
                context_id=context.context_id,
                task_id=context.task_id,
                artifact=new_text_artifact(
                    name="result",
                    text=chunk + " ",
                ),
            )
            await event_queue.enqueue_event(partial_artifact)

        # Send completed status
        status = TaskStatusUpdateEvent(
            context_id=context.context_id,
            task_id=context.task_id,
            status=TaskStatus(state=TaskState.completed),
            final=True,
        )

        await event_queue.enqueue_event(status)

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise Exception("cancel not supported")


from a2a.types import AgentCapabilities, AgentCard, AgentSkill

skill = AgentSkill(
    id="beyhadh_skill",
    name="Responses API from beyhadh agent",
    description=" beyhadh agent",
    tags=["hello"],
    examples=["hi", "hello"],
)

public_agent_card = AgentCard(
    name="Beyhadh Agent",
    description="Beyhadh A2A Agent",
    url="http://localhost:8080",
    version="1.0.0",
    default_input_modes=["text"],
    default_output_modes=["text"],
    capabilities=AgentCapabilities(streaming=True),
    skills=[skill],
)

from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore

request_handler = DefaultRequestHandler(
    agent_executor=HelloWorldAgentExecutor(),
    task_store=InMemoryTaskStore(),
)

from a2a.server.apps import A2AStarletteApplication

server = A2AStarletteApplication(
    agent_card=public_agent_card,
    http_handler=request_handler,
)


import asyncio
import uvicorn


async def main():
    config = uvicorn.Config(
        server.build(),
        host="0.0.0.0",
        port=8080,
        loop="asyncio",
    )

    server_instance = uvicorn.Server(config)
    await server_instance.serve()


if __name__ == "__main__":
    asyncio.run(main())

# http://localhost:8080/.well-known/agent-card.json







# ----------------------------------------------------------------------------------------------------------------------

# ---

# # 1. The Core Agent Implementation

# At the very top of the file you define the actual **business logic agent**.

# ```python
# class HelloWorldAgent:
#     async def invoke_agent(self, user_query: str) -> str:
#         return f"Hello, you said: {user_query}"
# ```

# This class represents the **domain logic of the agent**. In a real system this could be a wrapper around an LLM, a tool orchestrator, or a workflow engine. The method `invoke_agent` receives the user input and returns a generated response.

# The method is declared `async` because the A2A execution pipeline is asynchronous. In production systems this function typically performs operations such as calling an LLM API, querying databases, invoking external tools, or orchestrating multi-agent workflows.

# This layer is intentionally simple because the A2A protocol separates **agent logic** from **agent communication infrastructure**.

# ---

# # 2. A2A Execution Framework Imports

# ```python
# from a2a.server.agent_execution import AgentExecutor, RequestContext
# ```

# This module contains the **core execution abstraction used by A2A servers**.

# ### AgentExecutor

# `AgentExecutor` is the central class responsible for executing agent requests. Every A2A server must provide an implementation of this interface.

# The executor receives requests from the HTTP layer and processes them inside the agent runtime. It provides two main lifecycle methods:

# * `execute()` → processes a new request
# * `cancel()` → cancels an ongoing task

# In other words, the executor is the **bridge between the A2A protocol and your agent logic**.

# ### RequestContext

# `RequestContext` contains metadata about the incoming request. It provides structured access to the task and message information sent by the client.

# Important properties include:

# * `context_id` → unique conversation context identifier
# * `task_id` → identifier for the current task execution
# * `message` → the original message object
# * `get_user_input()` → helper method to extract the text content from the message

# In your code:

# ```python
# query = context.get_user_input()
# ```

# This extracts the text from the user's message payload.

# ---

# # 3. Event System

# ```python
# from a2a.server.events import EventQueue
# ```

# The **EventQueue** is the messaging channel used to communicate execution progress back to the client.

# Instead of returning a single response object, A2A agents emit **events** during execution. This allows:

# * streaming outputs
# * partial updates
# * progress reporting
# * cancellation handling

# The queue is asynchronous and supports real-time streaming.

# Each event pushed to the queue is delivered to the client through the transport layer.

# Example usage:

# ```python
# await event_queue.enqueue_event(event)
# ```

# This publishes an event to the client.

# ---

# # 4. Task Event Types

# ```python
# from a2a.types import (
#     TaskArtifactUpdateEvent,
#     TaskState,
#     TaskStatus,
#     TaskStatusUpdateEvent,
# )
# ```

# These types represent the **standardized event schema used in the A2A protocol**.

# ### TaskArtifactUpdateEvent

# This event represents a **new artifact produced by the agent**.

# Artifacts are structured outputs that may contain:

# * text
# * images
# * structured data
# * tool outputs

# In your code:

# ```python
# TaskArtifactUpdateEvent(...)
# ```

# Each event adds new output data to the task.

# ---

# ### TaskState

# `TaskState` defines the lifecycle state of a task.

# Typical states include:

# ```
# queued
# working
# completed
# failed
# cancelled
# ```

# Your server uses:

# ```
# TaskState.working
# TaskState.completed
# ```

# These states allow clients to monitor the progress of agent execution.

# ---

# ### TaskStatus

# `TaskStatus` wraps a `TaskState` and represents the **current execution status**.

# Example:

# ```python
# TaskStatus(state=TaskState.working)
# ```

# This tells the client that the task is currently processing.

# ---

# ### TaskStatusUpdateEvent

# This event communicates **task state transitions**.

# Example:

# ```
# TaskStatusUpdateEvent
#  ├─ context_id
#  ├─ task_id
#  ├─ status
#  └─ final flag
# ```

# The `final` flag indicates whether execution is finished.

# ---

# # 5. Artifact Utility

# ```python
# from a2a.utils import new_text_artifact
# ```

# Artifacts are the standard output container used by the A2A protocol.

# The utility function `new_text_artifact` creates a text artifact object.

# Example usage:

# ```python
# artifact = new_text_artifact(
#     name="result",
#     text="Hello world"
# )
# ```

# Artifacts can contain multiple parts and support multimodal outputs.

# This abstraction ensures the protocol can support:

# * text
# * images
# * structured outputs
# * tool results

# without changing the protocol schema.

# ---

# # 6. AgentExecutor Implementation

# You implement your own executor:

# ```python
# class HelloWorldAgentExecutor(AgentExecutor):
# ```

# This class connects the **A2A runtime** with the **HelloWorldAgent** logic.

# ---

# ## Constructor

# ```python
# def __init__(self):
#     self.agent = HelloWorldAgent()
# ```

# This initializes the internal agent instance.

# In real systems this might initialize:

# * an LLM client
# * vector databases
# * tool registries
# * orchestration engines

# ---

# ## execute()

# ```python
# async def execute(self, context: RequestContext, event_queue: EventQueue)
# ```

# This function processes the incoming request.

# Execution flow:

# 1. Extract user input
# 2. Generate response
# 3. Stream partial artifacts
# 4. Mark task completion

# ---

# ### Extract Query

# ```python
# query = context.get_user_input()
# ```

# This retrieves the user message.

# ---

# ### Response Construction

# ```
# response_text = f"Hello, you said: {query}"
# ```

# The agent generates the final response.

# ---

# ### Send Working Status

# ```python
# working_status = TaskStatusUpdateEvent(...)
# ```

# This informs the client that processing has started.

# ---

# ### Streaming Output

# ```python
# for chunk in response_text.split():
# ```

# Here you simulate streaming.

# Each chunk is sent as an artifact update event.

# This mimics how LLM token streaming works.

# ---

# ### Final Status

# ```python
# status = TaskStatusUpdateEvent(... final=True)
# ```

# This tells the client that the task execution is finished.

# ---

# ## cancel()

# ```python
# async def cancel(...)
# ```

# This method handles cancellation requests.

# Your implementation throws an exception because cancellation is unsupported.

# In production systems this function stops long-running operations.

# ---

# # 7. Agent Metadata

# ```python
# from a2a.types import AgentCapabilities, AgentCard, AgentSkill
# ```

# These classes describe the agent for discovery.

# ---

# ### AgentSkill

# ```python
# skill = AgentSkill(...)
# ```

# Skills describe what the agent can do.

# Fields include:

# * skill id
# * name
# * description
# * tags
# * example prompts

# Clients can inspect skills before invoking the agent.

# ---

# ### AgentCapabilities

# ```python
# AgentCapabilities(streaming=True)
# ```

# Capabilities describe supported features.

# Examples:

# ```
# streaming
# multimodal input
# tool invocation
# ```

# Your agent supports streaming.

# ---

# ### AgentCard

# The AgentCard is the **identity document of the agent**.

# It is served through the discovery endpoint:

# ```
# /.well-known/agent-card.json
# ```

# Fields include:

# ```
# name
# description
# url
# version
# capabilities
# skills
# ```

# Clients fetch this card before interacting with the agent.

# ---

# # 8. Request Handling Layer

# ```python
# from a2a.server.request_handlers import DefaultRequestHandler
# ```

# The request handler processes incoming HTTP requests.

# Responsibilities:

# * validate request schema
# * create task objects
# * invoke AgentExecutor
# * manage event streaming

# It acts as the **controller layer of the A2A server**.

# ---

# # 9. Task Storage

# ```python
# from a2a.server.tasks import InMemoryTaskStore
# ```

# The task store maintains state for running tasks.

# Your implementation uses an **in-memory store**, meaning tasks exist only while the server is running.

# In production deployments this would typically be replaced with:

# * Redis
# * PostgreSQL
# * distributed state stores

# This enables persistence and fault tolerance.

# ---

# # 10. A2A HTTP Server

# ```python
# from a2a.server.apps import A2AStarletteApplication
# ```

# This class builds the **HTTP server interface for the A2A protocol**.

# It integrates:

# * Starlette web framework
# * request handler
# * agent card endpoint
# * message endpoints

# Endpoints automatically exposed include:

# ```
# GET /.well-known/agent-card.json
# POST /message/send
# POST /message/send-streaming
# POST /tasks/cancel
# ```

# ---

# # 11. Server Initialization

# ```python
# server = A2AStarletteApplication(
#     agent_card=public_agent_card,
#     http_handler=request_handler,
# )
# ```

# This binds the agent metadata and request handler to the server runtime.

# ---

# # 12. Uvicorn Server

# ```python
# import uvicorn
# ```

# Uvicorn is an ASGI web server used to run asynchronous Python applications.

# It executes the Starlette application created earlier.

# ---

# ### Configuration

# ```python
# config = uvicorn.Config(
#     server.build(),
#     host="0.0.0.0",
#     port=8080,
# )
# ```

# `server.build()` returns the ASGI application.

# ---

# ### Start Server

# ```python
# await server_instance.serve()
# ```

# This starts the HTTP server and begins accepting requests.

# ---

# # 13. Async Entry Point

# ```python
# asyncio.run(main())
# ```

# This launches the async event loop and runs the server.

# ---

# # Complete A2A Execution Pipeline

# The full lifecycle of a request looks like this:

# ```
# Client
#    │
#    │ GET /.well-known/agent-card.json
#    ▼
# AgentCard Discovery
#    │
#    │ POST /message/send
#    ▼
# DefaultRequestHandler
#    │
#    ▼
# AgentExecutor.execute()
#    │
#    ▼
# HelloWorldAgent.invoke_agent()
#    │
#    ▼
# EventQueue
#    │
#    ├─ TaskStatusUpdateEvent (working)
#    ├─ TaskArtifactUpdateEvent (chunks)
#    └─ TaskStatusUpdateEvent (completed)
#    ▼
# Client receives streaming response
# ```

# ---

# # Summary

# Your server contains five architectural layers.

# Agent Logic
# The `HelloWorldAgent` implements the domain behavior.

# Execution Engine
# `AgentExecutor` orchestrates request processing.

# Event System
# `EventQueue` streams progress and outputs.

# Protocol Layer
# `DefaultRequestHandler` handles A2A messages.

# Transport Layer
# `A2AStarletteApplication` exposes HTTP endpoints.

# Together these components implement the **full A2A protocol stack**, enabling agents to communicate with external systems and other agents using a standardized interface.

# ---

# --------------------------------------------------------------------------------------------------------------------------------------------------

