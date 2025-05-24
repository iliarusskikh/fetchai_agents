from datetime import datetime
from uuid import uuid4
from uagents import Agent, Protocol, Context

#import the necessary components from the chat protocol
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    EndSessionContent,
    StartSessionContent,
    TextContent,
    chat_protocol_spec,
)
# Initialise agent2
agent2 = Agent(
    name="Chatproto2",
    port=8001,
    seed="eeeeeefgrgrojojoojojkoooioioio",
    endpoint=["http://127.0.0.1:8001/submit"],
    )

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


# Startup Handler - Print agent details
@agent2.on_event("startup")
async def startup_handler(ctx: Context):
    # Print agent details
    print(f"My name is {ctx.agent.name} and my address is {ctx.agent.address}")

# Message Handler - Process received messages and send acknowledgements
@chat_proto.on_message(ChatMessage)
async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
    ctx.logger.info(f"Got a message from {sender}: {msg}")
    ctx.storage.set(str(ctx.session), sender)
    session_sender = ctx.storage.get(str(ctx.session))
    await ctx.send(
        sender,
        ChatAcknowledgement(timestamp=datetime.utcnow(), acknowledged_msg_id=msg.msg_id),
    )

    for item in msg.content:
        if isinstance(item, EndSessionContent):
            print(f"Got an end session message from {sender}")
            ack = ChatAcknowledgement(
                timestamp=datetime.utcnow(),
                acknowledged_msg_id=msg.msg_id
            )
            await ctx.send(sender, ack)
            
        if isinstance(item, StartSessionContent):
            print(f"Got a start session message from {sender}")
            continue
            
        elif isinstance(item, TextContent):
            ctx.logger.info(f"Got a message from {sender}: {item.text}")
            ctx.storage.set(str(ctx.session), sender)
            await ctx.send(session_sender, create_text_chat(str("Hello from Agent2")))
            
            response = ChatMessage(
            timestamp=datetime.utcnow(),
            msg_id=uuid4(),
            content=[EndSessionContent(type="end-session")]
            )
            await ctx.send(session_sender, response)

            await ctx.send(session_sender, create_text_chat(str("Hello from Agent2 again"), False))

        else:
             print(f"Got unexpected content from {sender}")


# Acknowledgement Handler - Process received acknowledgements
@chat_proto.on_message(ChatAcknowledgement)
async def handle_acknowledgement(ctx: Context, sender: str, msg: ChatAcknowledgement):
    print(f"Received acknowledgement from {sender} for message: {msg.acknowledged_msg_id}")

# Include the protocol in the agent to enable the chat functionality
# This allows the agent to send/receive messages and handle acknowledgements using the chat protocol
agent2.include(chat_proto, publish_manifest=True)

if __name__ == '__main__':
    agent2.run()
