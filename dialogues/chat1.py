from datetime import datetime
from uuid import uuid4
from uagents import Agent, Protocol, Context, Model
from time import sleep
import asyncio

#import the necessary components from the chat protocol
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    EndSessionContent,
    StartSessionContent,
    TextContent,
    chat_protocol_spec,
)

# Intialise agent1
agent1 = Agent(
    name="Chatproto1",
    port=8002,
    seed="vvrfrfeeojojojojojoofjoefefef",
    endpoint=["http://127.0.0.1:8002/submit"],
    )
    
# Store agent2's address (you'll need to replace this with actual address)
agent2_address = "agent1qff3al8a47xqgtejze6zumn6fwgkxz6n2pk6sd4cfr8d6l2rfgefugjz4jg"

# Initialize the chat protocol
chat_proto = Protocol(spec=chat_protocol_spec)

def create_text_chat(text: str, end_session: bool = True) -> ChatMessage:
    content = [TextContent(type="text", text=text)]
    if end_session:
        content.append(EndSessionContent(type="end-session"))
    return ChatMessage(
        timestamp=datetime.utcnow(),
        msg_id=uuid4(),
        content=content,
    )


#Startup Handler - Print agent details and send initial message
@agent1.on_event("startup")
async def startup_handler(ctx: Context):
    # Print agent details
    print(f"My name is {ctx.agent.name} and my address is {ctx.agent.address}")
        
    response = ChatMessage(
    timestamp=datetime.utcnow(),
    msg_id=uuid4(),
    content=[StartSessionContent(type="start-session")]
    )
    await ctx.send(agent2_address, response)
    
    # Send initial message to agent2
    initial_message = ChatMessage(
        timestamp=datetime.utcnow(),
        msg_id=uuid4(),
        content=[TextContent(type="text", text="Hello from Agent1!")]
    )
    
    
    await ctx.send(agent2_address, initial_message)

# Message Handler - Process received messages and send acknowledgements
@chat_proto.on_message(ChatMessage)
async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
    ctx.storage.set(str(ctx.session), sender)
    session_sender = ctx.storage.get(str(ctx.session))
    for item in msg.content:
        if isinstance(item, EndSessionContent):
            print(f"Got an end session message from {sender}")
            # Send acknowledgment
            ack = ChatAcknowledgement(
                timestamp=datetime.utcnow(),
                acknowledged_msg_id=msg.msg_id
            )
            await ctx.send(sender, ack)
        if isinstance(item, StartSessionContent):
            print(f"Got a start session message from {sender}")
            continue
        if isinstance(item, TextContent):
            # Log received message
            print(f"Received message from {sender}: {item.text}")
            
            # Send acknowledgment
            ack = ChatAcknowledgement(
                timestamp=datetime.utcnow(),
                acknowledged_msg_id=msg.msg_id
            )
            await ctx.send(sender, ack)
            
            #await ctx.send(session_sender, create_text_chat(str("Hello from Agent1")))


# Acknowledgement Handler - Process received acknowledgements
@chat_proto.on_message(ChatAcknowledgement)
async def handle_acknowledgement(ctx: Context, sender: str, msg: ChatAcknowledgement):
    print(f"Received acknowledgement from {sender} for message: {msg.acknowledged_msg_id}")



# Include the protocol in the agent to enable the chat functionality
# This allows the agent to send/receive messages and handle acknowledgements using the chat protocol
agent1.include(chat_proto, publish_manifest=True)

if __name__ == '__main__':
    agent1.run()
