### A2A Client to Interact with Our A2A Server
%pip install a2a-sdk==0.3.8 azure-ai-projects==2.0.0b2 python-dotenv azure-identity uvicorn
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
### A2A Client Implementation
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

    final_agent_card_to_use: AgentCard | None = None

    try:
        # Attempting to fetch public agent card from custom path
        _public_card = (
                await resolver.get_agent_card()
            )  # Fetches from default public path

        final_agent_card_to_use = _public_card

    except Exception as e:
        print(f'Critical error fetching public agent card: {e}', exc_info=True)  
        raise RuntimeError(
                'Failed to fetch the public agent card. Cannot continue.'
            ) from e

    # initializing the A2A Client (ClientFactory Class) config
    config = ClientConfig(
        httpx_client = httpx_client,
        supported_transports=[
                    TransportProtocol.jsonrpc
        ],
        streaming=False
    )
    
    # Creating the A2A Client - Client Factory
    client = ClientFactory(config).create(final_agent_card_to_use)
    
    # Creating the message request
    request = create_text_message_object(content="How is Gotham City doing today?")

    # Send the request and get the streaming messages
    async for response in client.send_message(request):
                task, _ = response
                print(get_message_text(task.artifacts[-1]))
