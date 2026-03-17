## MS Learn Path Builder with Microsoft Agent Framework (MAF) and A2A
# %pip install a2a-sdk==0.3.8 agent-framework==1.0.0b251209 azure-ai-projects==2.0.0b2 python-dotenv azure-identity uvicorn
### Setting Up the Environment
import os
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential

load_dotenv()
project_endpoint = os.getenv("FOUNDRY_PROJECT_ENDPOINT")
model = os.getenv("MODEL_DEPLOYMENT_NAME")

print("Project Endpoint: ", project_endpoint)
print("Model: ", model)
### Defining the Function to Create a Chat Agent
from agent_framework import ChatAgent
from agent_framework.azure import AzureAIClient
from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import AzureCliCredential

# Cell 2: Define async workflow
async def create_agent(agent_name: str,
                       agent_instructions: str) -> ChatAgent:
    
    # Create async Azure credential
    credential = AzureCliCredential()

    # creating the Foundry Project Client
    project_client = AIProjectClient(
        endpoint=project_endpoint,
        credential=credential
    )

    # creating a conversation using the OpenAI Client
    openai_client = project_client.get_openai_client()
    conversation = await openai_client.conversations.create()
    conversation_id = conversation.id
    print("Conversation ID: ", conversation_id)
    
    # Initialize the Azure AI Agent Client
    chat_client = AzureAIClient(project_client=project_client,
                                conversation_id=conversation_id,
                                model_deployment_name=model)

    try:
        agent = chat_client.create_agent(
            name=agent_name,
            instructions=agent_instructions,
        )

        print("{} Agent created successfully!".format(agent_name))
        return agent

    finally:
        # Clean up async clients
        await chat_client.close()
        await credential.close()
### Creating the Topic Generator Agent - Pure Foundry Based Agent
topic_generator_agent = await create_agent(
    agent_name = "Topic-Generator-Agent",
    agent_instructions = "You are a helpful assistant that generates a list of topics for Microsoft Learn learning paths based on user input."
                         "Your response should be a concise list of topics relevant to the user's interests in a structured format."
)     
### Creating the MS Learn Path Builder Agent - A2A Based Agent
from httpx import AsyncClient
from a2a.types import AgentCard, Message, Part, Role, Task, TextPart
from a2a.client import ClientFactory, Client
from a2a.client.card_resolver import A2ACardResolver
from a2a.client.client import ClientConfig
from a2a.types import TransportProtocol
from a2a.client import create_text_message_object
from a2a.utils.message import get_message_text
import httpx
from agent_framework.a2a import A2AAgent

base_url = "http://localhost:8080"

final_agent_card: AgentCard | None = None

# creating the httpx client with custom timeouts
async with httpx.AsyncClient(
    timeout=httpx.Timeout(
        connect=10.0,
        read=60.0,
        write=10.0,
        pool=10.0,
            )) as httpx_client:
    
    # creating the A2ACardResolver
    resolver = A2ACardResolver(
        httpx_client=httpx_client,
        base_url=base_url
    )

    try:
        # Attempting to fetch public agent card from custom path
        _public_card = (
                await resolver.get_agent_card()
            )  # Fetches from default public path

        final_agent_card = _public_card

        print('Successfully fetched public agent card:')
        print(f'Name: {_public_card.name}')

    except Exception as e:
        print(f'Critical error fetching public agent card: {e}', exc_info=True)  
        raise RuntimeError(
                'Failed to fetch the public agent card. Cannot continue.'
            ) from e
    
    # Creating the A2A Agent finally in Microsoft Agent Framework
    ms_learn_path_builder_agent = A2AAgent(
    name = final_agent_card.name,
    description = final_agent_card.description,
    agent_card = final_agent_card,
    url = "https://localhost:8080"
    )

### Creating the First Executor to run the Topic Generator Agent
from agent_framework import WorkflowBuilder, WorkflowContext, WorkflowOutputEvent, executor
from typing import Any
from agent_framework import ChatResponse

@executor(id = "run_topic_generator_agent")
async def run_topic_generator_agent(query: str,
                               ctx: WorkflowContext[str]) -> None:
    response = await topic_generator_agent.run(query)

    await ctx.send_message(str(response))
### Creating the Second Executor to run the MS Learn Path Builder Agent
@executor(id = "run_ms_learn_path_builder_agent")
async def run_ms_learn_path_builder_agent(research_data: str,
                          ctx: WorkflowContext[str]) -> None:
    response = await ms_learn_path_builder_agent.run(research_data)
    
    final_output = ""

    for message in response.messages:
        final_output += message.text + "\n"

    await ctx.yield_output(final_output)
### Creating the Sequential Workflow
from agent_framework import WorkflowBuilder, WorkflowViz

workflow = (
    WorkflowBuilder()
    .add_edge(run_topic_generator_agent, run_ms_learn_path_builder_agent)
    .set_start_executor(run_topic_generator_agent)
    .build()
)

viz = WorkflowViz(workflow)
### Running the Workflow and Streaming Events
# Run the workflow and stream events in notebook
async def main():
    async for event in workflow.run_stream("Help me Learn about Azure AI services."):
        print(f"Event: {event}")
        if isinstance(event, WorkflowOutputEvent):
            print(f"Workflow completed with result: {event.data}")

await main()
