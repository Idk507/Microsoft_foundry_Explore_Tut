## A2A and MCP Server Setup with Microsoft Foundry Agents - Streaming Example
%pip install a2a-sdk==0.3.8 azure-ai-projects==2.0.0b2 python-dotenv azure-identity uvicorn
### Setting Up the Environment Variables
import os
from dotenv import load_dotenv
from azure.identity.aio import DefaultAzureCredential
from azure.ai.projects.aio import AIProjectClient
load_dotenv()

foundry_project_endpoint = os.getenv("FOUNDRY_PROJECT_ENDPOINT")
model_deployment_name = os.getenv("MODEL_DEPLOYMENT_NAME")
mcp_server_name = os.getenv("MCP_SERVER_NAME")
### Setting up the Foundry Client
project_client = AIProjectClient(
    endpoint=foundry_project_endpoint,
    credential=DefaultAzureCredential(),
)
### Getting the MCP Server Connection ID
connection_id = ""

async for connection in project_client.connections.list():
    if connection.name == mcp_server_name:
        connection_id = connection.id
        break

print(f"The MCP Server Connection ID is: {connection_id}")
### Creating the MCP Tool Spec
from azure.ai.projects.models import MCPTool, Tool

tool = MCPTool(
    server_label = "microsoft_learn_server",
    server_url="https://learn.microsoft.com/api/mcp",
    require_approval="never",
    project_connection_id=connection_id
)
### Creating the Agent that will be used in A2A Setup
from azure.ai.projects.models import PromptAgentDefinition

agent_name = "A2A-MCP-Agent"

agent = await project_client.agents.create_version(
    agent_name=agent_name,
    definition=PromptAgentDefinition(
        model=model_deployment_name,
        instructions="You are an intelligent assistant that can interact with the Microsoft Learn MCP server to provide users with relevant learning resources and information about Microsoft technologies.",
        tools = [tool]
    ),
)

# printing the agent id
print(f"Agent created (id: {agent.id}, name: {agent.name}, version: {agent.version})")
### Creating the Foundry Agent Class with Function Executions
class FoundryAgent():
    """This class will contain helper functions for interacting with our Foundry Agent"""

    async def invoke_agent_stream(self, user_query: str):
        try: 
            openai_client = project_client.get_openai_client()

            conversation = await openai_client.conversations.create()

            response_stream_events = await openai_client.responses.create(
                conversation=conversation.id,
                extra_body = {
                    "agent": {
                        "name": agent.name,
                        "type": "agent_reference"
                    }
                },
                input = user_query,
                stream = True
            )
            async for event in response_stream_events:
                if event.type == "response.output_text.delta":
                        yield {'content': event.delta, 'done': False}
            yield {'content': '', 'done': True}

        except Exception as e:
            print(f'error：{e!s}')
            yield {
                'content': 'Sorry, an error occurred while processing your request.',
                'done': True,
            }
        
### Creating the A2A Agent Executor with Streaming Responses
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
        async for event in self.agent.invoke_agent_stream(query):
            message = TaskArtifactUpdateEvent(
                context_id=context.context_id,  # type: ignore
                task_id=context.task_id,  # type: ignore
                artifact=new_text_artifact(
                    name='current_result',
                    text=event['content'],
                ),
            )
            await event_queue.enqueue_event(message)
            if event['done']:
                break

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
    id = "mcp_a2a_foundry_agent_skill",
    name = "This skill interacts with Microsoft Foundry via MCP Server",
    description = "This skill allows the agent to interact with Microsoft Foundry using the MCP Server connection to provide users with relevant learning resources and information about Microsoft technologies.",
    tags = ["mcp a2a foundry agent"],
    examples = ["Give me code to interact with Microsoft Foundry using the Python SDK.", "How to provision an azure storage account using the Azure CLI?"]
)
### Creating the Agent Card
public_agent_card = AgentCard(
    name = "A2A MCP Foundry Demo Agent",
    description = "Foundry Demo Agent to Show A2A Usage with Microsoft Foundry and MCP Server",
    url = "http://localhost:8080",
    version = "1.0.0",
    default_input_modes=['text'],
    default_output_modes=['text'],
    capabilities=AgentCapabilities(streaming=True),
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
