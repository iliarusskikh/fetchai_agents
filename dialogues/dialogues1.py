# Import required libraries
from uagents import Agent, Protocol, Context, Model
import json
from time import sleep
from asyncio import sleep

from uagents.experimental.dialogues import Dialogue, Edge, Node
from dialogues.hardcoded_chitchat import (ChitChatDialogue,ChitChatDialogueMessage)

from dialogues.hardcoded_chitchat import (
    ChitChatDialogue,
    ChitChatDialogueMessage,
    ConcludeChitChatDialogue,
)

CHAT_AGENT_ADDRESS = ""

agent = Agent(
    name="chit_agent1",
    seed="ikjkenjbndbjwdnwlncleohnwpjd",
    port=8001,
    endpoint="http://127.0.0.1:8001/submit",
)

# Instantiate the dialogues
chitchat_dialogue = ChitChatDialogue(
    version="0.1",
)

# Get an overview of the dialogue structure
print("Dialogue overview:")
print(json.dumps(chitchat_dialogue.get_overview(), indent=4))
print("---")


# This is the only decorator that is needed to add to your agent with the
# hardcoded dialogue example. If you omit this decorator, the dialogue will
# emit a warning.
@chitchat_dialogue.on_continue_dialogue()
async def continue_chitchat(
    ctx: Context,
    sender: str,
    msg: ChitChatDialogueMessage,
):
    # Do something when the dialogue continues
    ctx.logger.info(f"Received message: {msg.text}")
    try:
        my_msg = input("Please enter your message:\n> ")
        await ctx.send(sender, ChitChatDialogueMessage(text=my_msg))
    except EOFError:
        await ctx.send(sender, ConcludeChitChatDialogue())


agent.include(chitchat_dialogue)  # Including dialogue in agent

if __name__ == "__main__":
    print(f"My name is {agent.name} and my address is {agent.address}")
    agent.run()  # Running agent
