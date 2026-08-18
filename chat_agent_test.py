import os
import asyncio

from azure.ai.projects.aio import AIProjectClient
from azure.identity import InteractiveBrowserCredential  # or DefaultAzureCredential
from agent_framework_azure_ai import AzureAIAgentClient


PROJECT_ENDPOINT =AI_FOUNDRY_PROJECT_ENDPOINT
MODEL_DEPLOYMENT_NAME = "gpt-4.1"  # must match “Name” in Models + endpoints

async def main():
    credential = InteractiveBrowserCredential()

    async with AIProjectClient(
        endpoint=PROJECT_ENDPOINT,
        credential=credential,
    ) as project_client:

        # Create an Azure AI Agent client backed by your Foundry project
        agent_client = AzureAIAgentClient(
            project_client=project_client,
            model_deployment_name=MODEL_DEPLOYMENT_NAME,
        )

        # Define the agent once
        agent = agent_client.create_agent(
            name="Ben10",
            instructions=(
                "You are Ben10, the savior of the universe and the holder of the Omnitrix. "
                "You are brave, clever, and always ready to protect the innocent. "
                "You have access to a variety of alien forms that you can transform into using the Omnitrix. "
                "Your mission is to fight evil and save the day!"
            ),
        )

        # Run the agent
        query = "Who is Vilgax?"
        response = await agent.run(query)

        print("Agent Response:")
        print(response)

if __name__ == "__main__":
    asyncio.run(main())
