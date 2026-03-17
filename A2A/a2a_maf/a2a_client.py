### A2A Client Integration with Microsoft Agent Framework 
%pip install a2a-sdk==0.3.8 agent-framework==1.0.0b251209 azure-ai-projects==2.0.0b2 python-dotenv azure-identity uvicorn
### Importing Libraries and Utilities
import logging

from typing import Any
from uuid import uuid4

import httpx

from a2a.client import A2ACardResolver, A2AClient
from a2a.types import (
    AgentCard,
    MessageSendParams,
    SendMessageRequest,
    SendStreamingMessageRequest,
)
### Initializing the A2A Card Resolver and Fetching the Public Agent Card
import uuid
from httpx import AsyncClient
from a2a.types import AgentCard, Message, Part, Role, Task, TextPart
from a2a.client import ClientFactory, Client
from a2a.client.card_resolver import A2ACardResolver
from a2a.client.client import ClientConfig
from a2a.types import TransportProtocol
from a2a.client import create_text_message_object
from a2a.utils.message import get_message_text

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

    except Exception as e:
        print(f'Critical error fetching public agent card: {e}', exc_info=True)  
        raise RuntimeError(
                'Failed to fetch the public agent card. Cannot continue.'
            ) from e
### Creating a MAF Agent using the Fetched Agent Card
from agent_framework.a2a import A2AAgent

a2a_agent = A2AAgent(
    name = final_agent_card.name,
    description = final_agent_card.description,
    agent_card = final_agent_card,
    url = "https://localhost:8080/"
)
### Invoking our Agent
# invoke the agent
response = await a2a_agent.run("Can you help me with provisioning a VM in Azure using the Azure CLI?")

# print the agent response
print("\n Agent Response:")
for message in response.messages:
    print(message.text, end='', flush=True)
