### Structured Output Streaming with Microsoft Agent Framework
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
### Creating the Foundry Client and Agent
from agent_framework.azure import AzureAIClient
from azure.identity.aio import AzureCliCredential
from azure.ai.projects.aio import AIProjectClient

async def create_agent():
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
        name="JobCandidateExtractor",
        instructions="You are an HR assistant that extracts structured information about a job candidate from text."
    )
    return agent, credential, agent_client

agent, credential, agent_client = await create_agent()
### Creating a Structured Output Schema using Pydantic
from pydantic import BaseModel, ConfigDict

class CandidateProfile(BaseModel):
    """Structured job candidate profile"""
    name: str
    experience_years: int
    skills: list[str]
    current_role: str
    model_config = ConfigDict(extra="forbid")
### Run the Agent with Structured Output Streaming
text_input = """
    Hi, I’m Alice Johnson. I've been a software engineer for 6 years,
    mainly working with Python, Azure, and React. Currently a senior developer at Contoso Ltd.
    """

response = await agent.run(text_input, response_format=CandidateProfile)

print(response)
if response.value:
    print("name:", response.value.name)
    print("experience_years:", response.value.experience_years)
    print("skills:", response.value.skills)
    print("current_role:", response.value.current_role)
else:
    print("Failed to parse response")
