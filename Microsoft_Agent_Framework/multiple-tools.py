## Multi-Tool Calling with MAF and Microsoft Foundry
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
### Loading the Code Interpreter Tool
from agent_framework import AgentRunResponse, ChatResponseUpdate, HostedCodeInterpreterTool

code_interpreter_tool = HostedCodeInterpreterTool()
### Loading the Hosted MCP Tool
from agent_framework import HostedMCPTool

ms_learn_mcp_tool = HostedMCPTool(
    name = "Microsoft Learn MCP Tool",
    url = "https://learn.microsoft.com/api/mcp"
)
### Creating our Mutli-Tooled Agent
from agent_framework.azure import AzureAIClient
from azure.identity.aio import AzureCliCredential
from azure.ai.projects.aio import AIProjectClient

async def create_multi_tool_agent():
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
        name="multi-tool-agent",
        instructions="You are a helpful multi-tool agent",
        tools = [code_interpreter_tool, ms_learn_mcp_tool]
    )
    return agent, credential, agent_client

agent, credential, agent_client = await create_multi_tool_agent()
### Creating an Async Function to Handle User Approvals
from agent_framework import ChatMessage

async def handle_approvals_with_thread(query: str, agent):
    result = await agent.run(query)
    while len(result.user_input_requests) > 0:
        new_input = []
        for user_input_needed in result.user_input_requests:
            new_input.append(
                ChatMessage(
                    role="user",
                    contents=[user_input_needed.create_response(True)],
                )
            )
        result = await agent.run(new_input)
    return result
### Running Different Queries on the Agent
query = "Can you write a Python function to calculate the factorial of a number using recursion and give me the output for number 100"
response = await handle_approvals_with_thread(query, agent)

print("\n🧠 Assistant:\n", response)
thread = agent.get_new_thread()
query = "How to create an Azure storage account using az cli?"
response = await handle_approvals_with_thread(query, agent)

print("\n🧠 Assistant:\n", response)
