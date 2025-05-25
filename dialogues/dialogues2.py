"""Chit chat dialogue example"""
from uagents import Agent, Protocol, Context, Model
from asyncio import sleep

from uagents.experimental.dialogues import Dialogue, Edge, Node
from dialogues.hardcoded_chitchat import (ChitChatDialogue,ChitChatDialogueMessage)

from dialogues.hardcoded_chitchat import (
    ChitChatDialogue,
    ChitChatDialogueMessage,
    InitiateChitChatDialogue,
)

CHIT_AGENT_ADDRESS = ""

agent = Agent(
    name="chat_agent2",
    seed="ojojojnjejennenebiedeaaaawaw",
    port=8002,
    endpoint="http://127.0.0.1:8002/submit",
)

# Instantiate the dialogues
chitchat_dialogue = ChitChatDialogue(
    version="0.1",
)


@chitchat_dialogue.on_continue_dialogue()
async def continue_chitchat(
    ctx: Context,
    sender: str,
    msg: ChitChatDialogueMessage,
):
    ctx.logger.info(f"Returning: {msg.text}")
    await ctx.send(sender, ChitChatDialogueMessage(text=msg.text))


# Initiate dialogue after 5 seconds
@agent.on_event("startup")
async def start_cycle(ctx: Context):
    await sleep(5)
    await chitchat_dialogue.start_dialogue(
        ctx, CHIT_AGENT_ADDRESS, InitiateChitChatDialogue()
    )


agent.include(chitchat_dialogue)

if __name__ == "__main__":
    print(f"My name is {agent.name} and my address is {agent.address}")
    agent.run()
