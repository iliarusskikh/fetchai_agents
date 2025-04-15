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
sender = Agent(
    name="SendQuery",
    seed="123123hel121212loage23222332323nt122231212coingekoooo",
)

# Initialize the chat protocol
chat_proto = Protocol(spec=chat_protocol_spec)



#Startup Handler - Print agent details and send initial message
@sender.on_event("startup")
async def startup_handler(ctx: Context):
    # Print agent details
    ctx.logger.info(f"My name is {ctx.agent.name} and my address is {ctx.agent.address}")
    
    # Send initial message to agent2
    initial_message = ChatMessage(timestamp=datetime.utcnow(),msg_id=uuid4(),content=[
            ResourceContent(
                type="resource",
                resource_id=uuid4(),
                resource=[
                    Resource(
                        uri="https://example.com/resource1",
                        metadata={"source": "test", "category": "sample"}
                    ),
                    Resource(
                        uri="https://example.com/resource2",
                        metadata={"source": "test", "category": "more"}
                    )
                ]
            )
        ]
    )

    """
    resource=[
        Resource(
            uri="file:///path/to/mri/brainstem_scan1.json",
            metadata={
                "source": "hospital_x",
                "category": "mri_brainstem",
                "scan_date": "2025-04-15",
                "patient_id": "anon_123"
            }
        ),
        Resource(
            uri="file:///path/to/mri/brainstem_scan2.json",
            metadata={
                "source": "hospital_x",
                "category": "mri_brainstem",
                "scan_date": "2025-04-16",
                "patient_id": "anon_124"
            }
        )
    ]
    """

    """
    initial_message = ChatMessage(
        timestamp=datetime.utcnow(),
        msg_id=uuid4(),
        content=[TextContent(type="text", text="base")]
    )
    """
    await ctx.send("agent1qdqan0pcttf6wyyyzz7wkvxrymyytxcmgfhdthjgsq9u03z6q6l6j3hgawl", initial_message)


# Message Handler - Process received messages and send acknowledgements
@chat_proto.on_message(ChatMessage)
async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
    for item in msg.content:
        if isinstance(item, TextContent):
            # Log received message
            ctx.logger.info(f"Received message from {sender}: {item.text}")
            
            # Send acknowledgment
            ack = ChatAcknowledgement(
                timestamp=datetime.utcnow(),
                acknowledged_msg_id=msg.msg_id
            )
            await ctx.send(sender, ack)


# Acknowledgement Handler - Process received acknowledgements
@chat_proto.on_message(ChatAcknowledgement)
async def handle_acknowledgement(ctx: Context, sender: str, msg: ChatAcknowledgement):
    ctx.logger.info(f"Received acknowledgement from {sender} for message: {msg.acknowledged_msg_id}")



sender.include(chat_proto, publish_manifest=True)

if __name__ == "__main__":
    sender.run()

