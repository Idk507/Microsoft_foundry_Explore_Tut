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
