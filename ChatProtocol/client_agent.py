from typing import Any, Literal
from datetime import datetime
from pydantic.v1 import UUID4
from uagents import Agent, Protocol, Model, Context
from time import sleep
from uuid import uuid4
#from chat_proto import AgentContent, ChatAcknowledgement
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    TextContent,
    chat_protocol_spec,
)
 


class ContextPrompt(Model):
    context: str
    text: str
 
 
class Response(Model):
    text: str
 
 
class StructuredOutputPrompt(Model):
    prompt: str
    output_schema: dict[str, Any]
 
 
class StructuredOutputResponse(Model):
    output: dict[str, Any]
 
class TextContent(Model):
    type: Literal["text"]
 
    # The text of the content. The format of this field is UTF-8 encoded strings. Additionally,
    # markdown based formatting can be used and will be supported by most clients
    text: str
 
class ChatMessage(Model):
 
    # the timestamp for the message, should be in UTC
    timestamp: datetime
 
    # a unique message id that is generated from the message instigator
    msg_id: UUID4
 
    # the list of content elements in the chat
    content: list[TextContent]
 
agent = Agent(name="agent-2", port=8001, seed="agent-2123123123123123agent" , endpoint="http://localhost:8001/submit")

chat_proto = Protocol(spec=chat_protocol_spec)
 
AI_AGENT_ADDRESS = "agent1q09xe6rk6lqcnchdrkcn92ma4wlmjyty3v2yzxlxdx4jylq2fcfa2rv458x"
 
code = """
    def do_something():
        for i in range(10)
            pass
    """
 
 
class Location(Model):
    city: str
    country: str
    temperature: float
 
 
prompts = [
    ContextPrompt(
        context="Find and fix the bug in the provided code snippet",
        text=code,
    ),
    StructuredOutputPrompt(
        prompt="How is the weather in London today?",
        output_schema=Location.schema(),
    ),
    ChatMessage(
        timestamp=datetime.now(),
        msg_id=uuid4(),
        content=[TextContent(type="text", text="who is president of US")],
    )
    
]
 
 
@agent.on_interval(period=10.0)
async def send_message(ctx: Context):
    for prompt in prompts:
        await ctx.send(AI_AGENT_ADDRESS, prompt)
 
 
@agent.on_message(Response)
async def handle_response_ai(ctx: Context, sender: str, msg: Response):
    ctx.logger.info(f"Received response from {sender}: {msg.text}")
 
 
@chat_proto.on_message(StructuredOutputResponse)
async def handle_structured_output_response(ctx: Context, sender: str, msg: StructuredOutputResponse):
    ctx.logger.info(f"[Received response from ...{sender[-8:]}]:")
    response = Location.parse_obj(msg.output)
    ctx.logger.info(response)
 
@chat_proto.on_message(ChatAcknowledgement)
async def handle_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    ctx.logger.info(f"Got an acknowledgement from {sender} for {msg.acknowledged_msg_id}")
 
@chat_proto.on_message(ChatMessage)
async def handle_ack(ctx: Context, sender: str, msg: ChatMessage):
    ctx.logger.info(f"Received request from {sender} for {msg.content[0].text}")
 
 
 
# Include the protocol in the agent to enable the chat functionality
# This allows the agent to send/receive messages and handle acknowledgements using the chat protocol
agent.include(chat_proto, publish_manifest=True)
 

if __name__ == "__main__":
    agent.run()




