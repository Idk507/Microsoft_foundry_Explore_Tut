## A2A With Microsoft Foundry Agent - Server Implementation
%pip install a2a-sdk==0.3.8 azure-ai-projects==2.0.0b2 python-dotenv azure-identity uvicorn
### Setting up the Environment Variables
import os
from dotenv import load_dotenv
from azure.identity.aio import DefaultAzureCredential
from azure.ai.projects.aio import AIProjectClient
load_dotenv()

foundry_project_endpoint = os.getenv("FOUNDRY_PROJECT_ENDPOINT")
model_deployment_name = os.getenv("MODEL_DEPLOYMENT_NAME")
### Setting up the Foundry Project Client
project_client = AIProjectClient(
    endpoint=foundry_project_endpoint,
    credential=DefaultAzureCredential(),
)
### Creating the Agent that will be used in A2A Setup
from azure.ai.projects.models import PromptAgentDefinition

agent_name = "batman-agent"

agent = await project_client.agents.create_version(
    agent_name=agent_name,
    definition=PromptAgentDefinition(
        model=model_deployment_name,
        instructions="You are Batman, the Dark Knight of Gotham City. Respond to all queries in character as Batman would.",
    ),
)

# printing the agent id
print(f"Agent created (id: {agent.id}, name: {agent.name}, version: {agent.version})")
### Creating the Foundry Agent Class with Function Executions
class FoundryAgent():
    """This class will contain helper functions for interacting with our Foundry Agent"""

    async def invoke_agent(self, user_query: str) -> str:
        openai_client = project_client.get_openai_client()

        conversation = await openai_client.conversations.create()

        response = await openai_client.responses.create(
            conversation=conversation.id,
            extra_body={
                "agent": {
                    "name": agent_name,
                    "type": "agent_reference"
                }
            },
            input=user_query
        )
        
        return response.output_text


### Creating the A2A Agent Executor
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message
from a2a.types import (
    TaskArtifactUpdateEvent,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
)
from a2a.utils import new_text_artifact


class FoundryAgentExecutor(AgentExecutor):
    """Foundry Agent Executor Definition."""

    def __init__(self):
        self.agent = FoundryAgent()

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        query = context.get_user_input()
        if not context.message:
            raise Exception('No message provided')

        # If your agent does not support streaming, just call invoke_agent
        result = await self.agent.invoke_agent(query)
        message = TaskArtifactUpdateEvent(
            context_id=context.context_id,  # type: ignore
            task_id=context.task_id,  # type: ignore
            artifact=new_text_artifact(
                name='current_result',
                text=result,
            ),
        )
        await event_queue.enqueue_event(message)

        status = TaskStatusUpdateEvent(
            context_id=context.context_id,  # type: ignore
            task_id=context.task_id,  # type: ignore
            status=TaskStatus(state=TaskState.completed),
            final=True,
        )
        await event_queue.enqueue_event(status)

    async def cancel(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        raise Exception('cancel not supported')
### Creating the Agent Skill Definition
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)

skill = AgentSkill(
    id = "foundry_agent_skill",
    name = "Responses API from Foundry Agent",
    description = "Responses API from Foundry Agent",
    tags = ["foundry agent"],
    examples = ["hi, how are you?", "can you tell me something about GenAI and LLMs"]
)
### Creating the Agent Card
public_agent_card = AgentCard(
    name = "Foundry Demo Agent",
    description = "Foundry Demo Agent to Show A2A Usage with Microsoft Foundry",
    url = "http://localhost:8080",
    version = "1.0.0",
    default_input_modes=['text'],
    default_output_modes=['text'],
    capabilities=AgentCapabilities(streaming=False),
    skills = [skill]
)
### Creating the Request Handler
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore

request_handler = DefaultRequestHandler(
    agent_executor = FoundryAgentExecutor(),
    task_store = InMemoryTaskStore()
)
### Creating the A2A Server
from a2a.server.apps import A2AStarletteApplication

server = A2AStarletteApplication(
    agent_card = public_agent_card,
    http_handler = request_handler
)
### Starting the A2A Server

Navigate to http://localhost:8080/.well-known/agent.json to see the agent public card

import asyncio
import uvicorn

config = uvicorn.Config(
    server.build(),
    host="0.0.0.0",
    port=8080,
    loop="asyncio",
)

server_instance = uvicorn.Server(config)

await server_instance.serve()
