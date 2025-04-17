import json
import os
import logging
import requests
#from enum im copyport Enum
from enum import Enum

from typing import Any
from datetime import datetime
from uuid import uuid4
 
from uagents import Agent, Context, Model, Protocol, Field
from uagents.experimental.quota import QuotaProtocol, RateLimit
from uagents_core.models import ErrorMessage
 

agent = Agent()


#ASI-ONE SETUP
api_key = str("sk_20368c14ae744ee185663e00679c1d61ff3d9289512447e4bcd20ec478f83adc")
# ASI1-Mini LLM API endpoint
url = "https://api.asi1.ai/v1/chat/completions"
# Define headers for API requests, including authentication
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}"
}

# Import the necessary components of the chat protocol
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    EndSessionContent,
    StartSessionContent,
    TextContent,
    chat_protocol_spec,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#add chat protocol
 
class StructuredOutputPrompt(Model):
    prompt: str
    output_schema: dict[str, Any]
 
class StructuredOutputResponse(Model):
    output: dict[str, Any]

class ContextPrompt(Model):
    context: str
    text: str
 
 
class Response(Model):
    text: str
    

# Startup Handler - Print agent details
@agent.on_event("startup")
async def startup_handler(ctx: Context):
    ctx.logger.info(f"my address is {ctx.agent.address}")
    

chat_proto = Protocol(spec=chat_protocol_spec)
struct_output_client_proto = Protocol(
    name="StructuredOutputClientProtocol", version="0.1.0"
)
 

proto = QuotaProtocol(
    storage_reference=agent.storage,
    name="LLM-Context-Response",
    version="0.1.0",
    default_rate_limit=RateLimit(window_size_minutes=60, max_requests=6),
)
 
struct_proto = QuotaProtocol(
    storage_reference=agent.storage,
    name="LLM-Structured-Response",
    version="0.1.0",
    default_rate_limit=RateLimit(window_size_minutes=60, max_requests=6),
)



#receives enquiry about the wallet from user
@chat_proto.on_message(ChatMessage)
async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
    ctx.logger.info(f"Got a message from {sender}: {msg}")
    ctx.storage.set(str(ctx.session), sender)
    await ctx.send(
        sender,
        ChatAcknowledgement(timestamp=datetime.utcnow(), acknowledged_msg_id=msg.msg_id),
    )

    for item in msg.content:
        if isinstance(item, StartSessionContent):
            ctx.logger.info(f"Got a start session message from {sender}")
            continue
        elif isinstance(item, TextContent):
            ctx.logger.info(f"TextContent Got a message from {sender}: {item.text}")
            ctx.storage.set(str(ctx.session), sender)
                
            prompt = f'''prompt : {item.text}.'''
            
            response = query_llm(prompt)
            print(response, "response")
            print(sender, "sender")
            await ctx.send(sender, Response(text=f"{response}"))
            
            #await ctx.send(AI_AGENT_ADDRESS,StructuredOutputResponse(prompt=item.text, output_schema=SolanaRequest.schema()),)
        else:
            ctx.logger.info(f"Got unexpected content from {sender}")


@chat_proto.on_message(ChatAcknowledgement)
async def handle_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    ctx.logger.info(
        f"Got an acknowledgement from {sender} for {msg.acknowledged_msg_id}"
    )


@proto.on_message(ContextPrompt, replies={Response, ErrorMessage})
async def handle_request(ctx: Context, sender: str, msg: ContextPrompt):
    ctx.logger.info(f"Context Prompts Received message {msg.text}")
        
    prompt = f'''context : {msg.context}. prompt : {msg.text}.'''
    response = query_llm(prompt)
    print(response, "response")
    print(sender, "sender")
    await ctx.send(sender, Response(text=f"{response}"))



@struct_proto.on_message(StructuredOutputPrompt, replies={StructuredOutputResponse, ErrorMessage})
async def handle_structured_request(ctx: Context, sender: str, msg: StructuredOutputPrompt):
    ctx.logger.info(f"Received message: {msg.prompt}")
    
    prompt = f''' prompt : {msg.prompt}.response_schema : {msg.output_schema}; output: dict[str, Any]. if response_schema is not None: response_format = "type": "json_schema","json_schema":  "name": response_schema["title"], "strict": False, "schema": response_schema. ;     Follow the response schema to format the prompt and provide strict output to match the schema. Do not include "json" heading in the output. only brackets and json formated text.'''
    
    # Interpret the AI response and print SELL or HOLD decision
    #if "SELL" in response:
    #    print("SELL")
    #else:
    #    print("HOLD")
    
    response = query_llm(prompt)
    ctx.logger.info(f"Received response: {response}")
    #response = get_completion(context="", prompt=msg.prompt, response_schema=msg.output_schema)
    await ctx.send(sender, StructuredOutputResponse(output=json.loads(response)))
 
 
agent.include(proto, publish_manifest=True)
agent.include(struct_proto, publish_manifest=True)
agent.include(chat_proto, publish_manifest=True)
 
 
 
 

### Health check related code
def agent_is_healthy() -> bool:
    try:
        import asyncio
        #await asyncio.sleep(10)  # Wait 10 seconds
        pass
        #asyncio.run(get_balance_from_address("AtTjQKXo1CYTa2MuxPARtr382ZyhPU5YX4wMMpvaa1oy"))
        return True
    except Exception:
        return False
 

class HealthCheck(Model):
    pass
 
class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
 
class AgentHealth(Model):
    agent_name: str
    status: HealthStatus
 
health_protocol = QuotaProtocol(
    storage_reference=agent.storage, name="HealthProtocol", version="0.1.0"
)
 
@health_protocol.on_message(HealthCheck, replies={AgentHealth})
async def handle_health_check(ctx: Context, sender: str, msg: HealthCheck):
    status = HealthStatus.UNHEALTHY
    try:
        if agent_is_healthy():
            status = HealthStatus.HEALTHY
    except Exception as err:
        ctx.logger.error(err)
    finally:
        await ctx.send(sender, AgentHealth(agent_name=AGENT_NAME, status=status))
 
agent.include(health_protocol, publish_manifest=True)
 
 
 
"""
def get_completion(
    context: str,
    prompt: str,
    response_schema: dict[str, Any] | None = None,
    max_tokens: int = MAX_TOKENS,
) -> str:
    if response_schema is not None:
        response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": response_schema["title"],
                "strict": False,
                "schema": response_schema,
            },
        }
    else:
        response_format = None
 
    try:
        response = client.chat.completions.create(
            model=MODEL_ENGINE,
            messages=[
                {"role": "system", "content": context},
                {"role": "user", "content": prompt},
            ],
            response_format=response_format,
            max_tokens=max_tokens,
        )
    except OpenAIError as e:
        return f"An error occurred: {e}"
 
    return response.choices[0].message.content
"""







def query_llm(query):

    data = {
        "messages": [{"role": "user", "content": query}],  # User input for the chat model
        "conversationId": None,  # No conversation history tracking
        "model": "asi1-mini"  # Specifies the model version to use
    }

    try:
        # Send a POST request to the LLM API with the input query
        with requests.post(url, headers=headers, json=data) as response:
            output = response.json()  # Parse the JSON response

            # Extract and return the generated message content
            return output["choices"][0]["message"]["content"]
    
    except requests.exceptions.RequestException as e:
        # Handle and return any request-related exceptions (e.g., network errors)
        return str(e)


 
if __name__ == "__main__":
    agent.run()
