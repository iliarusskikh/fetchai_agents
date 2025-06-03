from uagents.setup import fund_agent_if_low
from uagents import Agent, Protocol, Context, Model
import random
import logging
from uagents import Field
from uagents.agent import AgentRepresentation #to use txn wallet
#from ai_engine import UAgentResponse, UAgentResponseType
import sys

from logging import Logger

import cosmpy
from cosmpy.crypto.keypairs import PrivateKey
from cosmpy.aerial.client import LedgerClient, NetworkConfig
from cosmpy.aerial.client import LedgerClient
from cosmpy.aerial.faucet import FaucetApi
from cosmpy.crypto.address import Address

from uagents.config import TESTNET_REGISTRATION_FEE
from uagents.network import get_faucet, wait_for_tx_to_complete
from uagents.utils import get_logger
from uagents.experimental.quota import QuotaProtocol, RateLimit

import argparse
import time

from cosmpy.aerial.wallet import LocalWallet

from datetime import datetime
from uuid import uuid4
import os
import requests
import atexit



# Import the necessary components of the chat protocol
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    EndSessionContent,
    StartSessionContent,
    TextContent,
    chat_protocol_spec,
)


farmer = Agent()


TOTALSTAKEDCOINS = ""
# AI Agent Address for structured output processing
AI_AGENT_ADDRESS = 'agent1q2gmk0r2vwk6lcr0pvxp8glvtrdzdej890cuxgegrrg86ue9cahk5nfaf3c'
if not AI_AGENT_ADDRESS:
    raise ValueError("AI_AGENT_ADDRESS not set")

def create_text_chat(text: str, end_session: bool = True) -> ChatMessage:
    content = [TextContent(type="text", text=text)]
    if end_session:
        content.append(EndSessionContent(type="end-session"))
    return ChatMessage(
        timestamp=datetime.utcnow(),
        msg_id=uuid4(),
        content=content,
    )
# Initialize the chat protocol
chat_proto = Protocol(spec=chat_protocol_spec)
struct_output_client_proto = Protocol(
    name="StructuredOutputClientProtocol", version="0.1.0"
)
proto = QuotaProtocol(
    storage_reference=farmer.storage,
    name="FetchFund-FarmerWill-Protocol",
    version="0.1.0",
    default_rate_limit=RateLimit(window_size_minutes=60, max_requests=15),
)


class StructuredOutputPrompt(Model):
    prompt: str
    output_schema: dict[str, Any]

class StructuredOutputResponse(Model):
    output: dict[str, Any]


class FarmerRequest(Model):
    response : str = Field(
        description="ASI1 response to user query to maintain the conversation",
    )
 
class BalanceRequest(Model):
    wallet : str = Field(
        description="user's FET wallet address",
    )

class BalanceResponse(Model):
    amount : str = Field(
        description="user's total staked FET amount",
    )


 
@farmer.on_event("startup")
async def introduce_agent(ctx: Context):
    ctx.logger.info(farmer.address)
    ctx.logger.info(farmer.wallet.address())
    ctx.logger.info(f"My name is {ctx.agent.name}")

    #ctx.logger.info(f"My name is {farmer.name}")



# Message Handler - Process received messages and send acknowledgements
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
            ctx.logger.info(f"Got a message from {sender}: {item.text}")
            asiprompt = f"Match the output schema given user input: {item.text}."
            await ctx.send(
                AI_AGENT_ADDRESS,
                StructuredOutputPrompt(
                    prompt=asiprompt, output_schema=BalanceRequest.schema()
                ),
            )
        else:
            ctx.logger.info(f"Got unexpected content from {sender}")



# Acknowledgement Handler - Process received acknowledgements
@chat_proto.on_message(ChatAcknowledgement)
async def handle_acknowledgement(ctx: Context, sender: str, msg: ChatAcknowledgement):
    ctx.logger.info(f"Received acknowledgement from {sender} for message: {msg.acknowledged_msg_id}")


@struct_output_client_proto.on_message(StructuredOutputResponse)
async def handle_structured_output_response(
    ctx: Context, sender: str, msg: StructuredOutputResponse
):
    session_sender = ctx.storage.get(str(ctx.session))
    if session_sender is None:
        ctx.logger.error(
            "Discarding message because no session sender found in storage"
        )
        return

    if "<UNKNOWN>" in str(msg.output):
        await ctx.send(
            session_sender,
            create_text_chat(
                "Sorry, I couldn't process your request. Please include a valid wallet address to check your balance in FET."
            ),
        )
        return

    try:
        # Parse the structured output to get the address
        farmer_request = BalanceRequest.parse_obj(msg.output)
        inforesponse = farmer_request.wallet

        if not inforesponse:
            await ctx.send(session_sender,create_text_chat("Sorry, I couldn't find a valid wallet address in your query. Please, provide your wallet address to check your balance."),)
            return

        ctx.logger.info(f"Received wallet {inforesponse}")

        ledger_client = LedgerClient(NetworkConfig.fetchai_mainnet())
        try:
            balances = ledger_client.query_bank_balance(inforesponse, denom='afet')
            totalbalance = (int(balances)/1000000000000000000)
            ctx.logger.info(f"Total balance: {balances}")
            response_text= f"{totalbalance} FET"
        except Exception as err:
            ctx.logger.error(err)
            await ctx.send(
                session_sender,
                create_text_chat(
                    "Sorry, I couldn't check your FET wallet on native blockchain. Please provide a valid wallet address."
                ),
            )
            return
        # Send response message

        await ctx.send(session_sender, create_text_chat(response_text))
        
    except Exception as err:
        ctx.logger.error(err)
        await ctx.send(
            session_sender,
            create_text_chat(
                "Sorry, I couldn't check your wallet. Please try again later."
            ),
        )
        return
 


@proto.on_message(model=BalanceRequest)
async def handle_acknowledgement(ctx: Context, sender: str, msg: BalanceRequest):
    ctx.logger.info(f"Received wallet {msg.wallet}")

    ledger_client = LedgerClient(NetworkConfig.fetchai_mainnet())
    balances = ledger_client.query_bank_balance(inforesponse, denom='afet')
    totalbalance = (int(balances)/1000000000000000000)
    ctx.logger.info(f"Total balance: {balances}")

    response_text= f"{totalbalance} FET"

    await ctx.send(sender, BalanceResponse(amount=response_text))




# Include the protocol in the agent to enable the chat functionality
# This allows the agent to send/receive messages and handle acknowledgements using the chat protocol
farmer.include(chat_proto, publish_manifest=True)
farmer.include(struct_output_client_proto, publish_manifest=True)
farmer.include(proto, publish_manifest=True)


if __name__ == "__main__":
    farmer.run()
