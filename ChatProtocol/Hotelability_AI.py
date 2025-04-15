from datetime import datetime
from uuid import uuid4

from uagents import Agent, Protocol, Context, Model
import os
import logging
import sys
import requests
import atexit
from typing import Literal, Union, List
from pydantic import Field

# Import the necessary components from the chat protocol
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    TextContent,
    chat_protocol_spec,
    ResourceContent,
    Resource
)

# Initialize agent2
agent2 = Agent(
    name="ChatProtocolTester",
    seed="123123hel121212loage232323nt1231212coingek123123123123ooo778778o",
)

# Initialize the chat protocol
chat_proto = Protocol(spec=chat_protocol_spec)

# Startup Handler - Print agent details
@agent2.on_event("startup")
async def startup_handler(ctx: Context):
    ctx.logger.info(f"My name is {ctx.agent.name} and my address is {ctx.agent.address}")

# Message Handler - Process received ChatMessages
@chat_proto.on_message(ChatMessage)
async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
    for item in msg.content:
        # Handle TextContent (existing functionality)
        if isinstance(item, TextContent):
            pass
        # Handle ResourceContent (new functionality)
        elif isinstance(item, ResourceContent):
            ctx.logger.info(f"Received ResourceContent from {sender}:")
            ctx.logger.info(f"Resource ID: {item.resource_id}")
            
            # Process resource(s)
            resources = item.resource if isinstance(item.resource, list) else [item.resource]
            for res in resources:
                ctx.logger.info(f"Resource: {res.uri}, Data: {res.metadata}")

            # Send acknowledgment
            ack = ChatAcknowledgement(
                timestamp=datetime.utcnow(),
                acknowledged_msg_id=msg.msg_id
            )
            await ctx.send(sender, ack)

            # Send TextContent response
            response_text = f"Processed {len(resources)} resource(s) with ID {item.resource_id}"
            response = ChatMessage(
                timestamp=datetime.utcnow(),
                msg_id=uuid4(),
                content=[TextContent(type="text", text=response_text)]
            )
            await ctx.send(sender, response)

# Acknowledgement Handler - Process received acknowledgements
@chat_proto.on_message(ChatAcknowledgement)
async def handle_acknowledgement(ctx: Context, sender: str, msg: ChatAcknowledgement):
    ctx.logger.info(f"Received acknowledgement from {sender} for message: {msg.acknowledged_msg_id}")

# Include the protocol in the agent
agent2.include(chat_proto, publish_manifest=True)

if __name__ == "__main__":
    agent2.run()
