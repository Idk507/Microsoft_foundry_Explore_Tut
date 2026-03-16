%pip install agent-framework==1.0.0b251209 
### Setting Up the Environment
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("AZURE_OPENAI_API_KEY")
endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

print("API Key:", api_key)
print("Endpoint:", endpoint)
print("Deployment Name:", deployment_name)
### Creating our Client and Agent
import asyncio
from agent_framework.openai import OpenAIChatClient

# Creating the AzureOpenAIChatClient
client = OpenAIChatClient(
    base_url = endpoint,
    model_id = deployment_name,
    api_key = api_key
)



# Creating our agent
agent = client.create_agent(
    instructions = "You are Batman, the Dark Knight of Gotham City.",
    name = "Batman-Agent"
)
### Running a Chat Loop with the Agent
# Running a chat loop with the agent
async def chat_with_agent():
    print("Chatting with the agent. Type 'exit' to quit.")
    while True:
        user_input = input("You: ")
        if user_input.lower() == 'exit':
            break
        response = await agent.run(user_input)
        print(f"Agent: {response.text}")

await chat_with_agent()
### Streaming Responses from the Agent
# Running the agent with streaming responses
async def streaming_chat():
    async for update in agent.run_stream("Tell me something interesting about Gotham City in 10 points"):
        if update.text:
            print(update.text, end="", flush=True)
    print()  # New line after streaming is complete

await streaming_chat()
### Giving our Agent an Image to Analyze
![joker_interrogation_scene](./Assets/joker_interrogation_scene.png)
from agent_framework import ChatMessage, TextContent, DataContent, Role

# Load image from local file
with open("./Assets/joker_interrogation_scene.png", "rb") as image_file:
    image_bytes = image_file.read()

# Create a message with text and image data
message = ChatMessage(
    role = Role.USER,
    contents = [
        TextContent(text = "Tell me about the incident in this image."),
        DataContent(
            data = image_bytes,
            media_type = "image/png"
        )
    ]
)

# Creating an async function for the entire image analysis run
async def analyze_image():
    response = await agent.run(message)
    print(f"Agent: {response.text}")

# invoke the async function
await analyze_image()
