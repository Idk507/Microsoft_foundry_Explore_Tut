### Hosted MCP Tool with Microsoft Agent Framework
%pip install agent-framework==1.0.0b251209 python-dotenv azure-ai-projects==2.0.0b2
### Setting Up the Environment
import os
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential

load_dotenv()
project_endpoint = os.getenv("AI_FOUNDRY_PROJECT_ENDPOINT")
model = os.getenv("AI_FOUNDRY_DEPLOYMENT_NAME")

print("Project Endpoint: ", project_endpoint)
print("Model: ", model)
### Creating our MS Learn MCP Tool Object
from agent_framework import HostedMCPTool

ms_learn_mcp_tool = HostedMCPTool(
    name = "Microsoft Learn MCP Tool",
    url = "https://learn.microsoft.com/api/mcp"
)
### Creating our MCP Agent
from agent_framework.azure import AzureAIClient
from azure.identity.aio import AzureCliCredential
from azure.ai.projects.aio import AIProjectClient

async def create_mcp_tool_agent():
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
    
    # creating the Azure AI Client to interact with the Agent in Foundry
    agent_client = AzureAIClient(
        project_client = project_client,
        conversation_id = conversation_id,
        model_deployment_name=model
    )
    
    # creating an agent in Foundry
    agent = agent_client.create_agent(
        name="DocsAgent",
        instructions="You are a helpful assistant that can help with Microsoft documentation questions.",
        tools = [ms_learn_mcp_tool]
    )
    return agent, credential, agent_client

agent, credential, agent_client = await create_mcp_tool_agent()
### Creating an Async Function to Handle User Approvals
from agent_framework import ChatMessage

async def handle_approvals_with_thread(query: str, agent):
    result = await agent.run(query)
    while len(result.user_input_requests) > 0:
        new_input = []
        for user_input_needed in result.user_input_requests:
            print(
                f"\n⚙️ Function call requested: {user_input_needed.function_call.name}"
                f"\nArguments: {user_input_needed.function_call.arguments}"
            )
            user_approval = input("Approve function call? (y/n): ")
            new_input.append(
                ChatMessage(
                    role="user",
                    contents=[user_input_needed.create_response(user_approval.lower() == "y")],
                )
            )
        result = await agent.run(new_input)
    return result
query = "How to create an Azure storage account using az cli?"
response = await handle_approvals_with_thread(query, agent)

print("\n🧠 Assistant:\n", response)
