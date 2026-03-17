# a2a_client.py

import asyncio
import logging
import httpx

from a2a.client.card_resolver import A2ACardResolver
from a2a.client.client import ClientConfig
from a2a.client import ClientFactory, create_text_message_object
from a2a.types import AgentCard, TransportProtocol, TaskState
from a2a.utils.message import get_message_text


BASE_URL = "http://localhost:8080"


async def main():

    async with httpx.AsyncClient(
        timeout=httpx.Timeout(connect=10.0, read=60.0, write=10.0, pool=10.0)
    ) as httpx_client:

        resolver = A2ACardResolver(
            httpx_client=httpx_client,
            base_url=BASE_URL,
        )

        try:
            agent_card: AgentCard = await resolver.get_agent_card()
        except Exception as e:
            logging.error("Failed to fetch agent card", exc_info=True)
            raise RuntimeError("Cannot continue without AgentCard") from e

        config = ClientConfig(
            httpx_client=httpx_client,
            supported_transports=[TransportProtocol.jsonrpc],
            streaming=True,  # Enable streaming
        )

        client = ClientFactory(config).create(agent_card)

        request = create_text_message_object(
            content="Hi Beyhadh here"
        )

        response = client.send_message(request)

        print("Streaming response:")
        print("-" * 40)

        full_response = []
        async for result in response:
            task, update = result

            # Handle status updates
            if hasattr(update, 'status') and update.status:
                state = update.status.state
                if state == TaskState.working:
                    print(f"[Status: working...]")
                elif state == TaskState.completed:
                    print(f"\n[Status: completed]")

            # Handle artifact updates (streaming chunks)
            if hasattr(task, 'artifacts') and task.artifacts:
                for artifact in task.artifacts:
                    chunk = get_message_text(artifact)
                    if chunk:
                        print(chunk, end="", flush=True)
                        full_response.append(chunk)

        print("\n" + "-" * 40)
        print(f"Full response: {''.join(full_response)}")


if __name__ == "__main__":
    asyncio.run(main())
