from datetime import datetime
from uuid import uuid4
from uagents import Agent, Protocol, Context, Model
from time import sleep
import asyncio
#proto:30a801ed3a83f9a0ff0a9f1e6fe958cb91da1fc2218b153df7b6cbf87bd33d62

#import the necessary components from the chat protocol
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    TextContent,
    chat_protocol_spec,
)

# Intialise agent1
agent1 = Agent(name="agent1",port=8000,seed="123123helloagent1231212",
 mailbox=True)

agent2_address = "agent1qthmuhfu5xlu4s8uwlq7z2ghxhpdqpj2r8smaushxu0qr3k3zcwuxu87t0t"
#some working examplr agent1q0h70caed8ax769shpemapzkyk65uscw4xwk6dc4t3emvp5jdcvqs9xs32y
#agent1qthmuhfu5xlu4s8uwlq7z2ghxhpdqpj2r8smaushxu0qr3k3zcwuxu87t0t coingecko
# Initialize the chat protocol
chat_proto = Protocol(spec=chat_protocol_spec)


#Startup Handler - Print agent details and send initial message
@agent1.on_event("startup")
async def startup_handler(ctx: Context):
    # Print agent details
    ctx.logger.info(f"My name is {ctx.agent.name} and my address is {ctx.agent.address}")
    
    # Send initial message to agent2
    initial_message = ChatMessage(
        timestamp=datetime.utcnow(),
        msg_id=uuid4(),
        content=[TextContent(type="text", text="base")]
    )
    await asyncio.sleep(25)
    await ctx.send(agent2_address, initial_message)

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



# Include the protocol in the agent to enable the chat functionality
# This allows the agent to send/receive messages and handle acknowledgements using the chat protocol
agent1.include(chat_proto, publish_manifest=True)

if __name__ == '__main__':
    agent1.run()
