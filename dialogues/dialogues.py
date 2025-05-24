
from datetime import datetime
from uuid import uuid4
from uagents import Agent, Protocol, Context, Model


import os
import logging
from logging import Logger
import sys
import requests
import atexit

import asyncio
from dotenv import load_dotenv



from uagents.experimental.dialogues import Dialogue, Edge, Node

from dialogues.hardcoded_chitchat import (ChitChatDialogue,ChitChatDialogueMessage)


class ChitChatDialogueMessage(Model):
    text: str
 
# Defining dialogues class
class ChitChatDialogue(Dialogue):
    def __init__(self, version: str | None = None, agent_address: str | None = None) -> None:
        super().__init__(
            name="ChitChatDialogue",
            version=version,
            agent_address=agent_address,
            nodes=[ node1, node2, node3],
            edges=[ init_session, start_dialogue, cont_dialogue, end_session],
        )
 
    def on_continue_dialogue(self):
        return super()._on_state_transition(
            cont_dialogue.name,
            ChitChatDialogueMessage,
        )
        
        
 
# Instantiate the dialogues
chitchat_dialogue = ChitChatDialogue(
    version="0.1",
    agent_address=<agent's address>,
)
 
@chitchat_dialogue.on_continue_dialogue()
async def continue_chitchat(
    ctx: Context,
    sender: str,
    msg: ChitChatDialogueMessage,
):
    ctx.logger.info(f"Returning: {msg.text}")
    await ctx.send(sender, ChitChatDialogueMessage(text=msg.text))


if __name__ == '__main__':
    #load_dotenv()
    agent.run()


