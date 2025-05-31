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
from cosmpy.aerial.faucet import FaucetApi
from cosmpy.crypto.address import Address
from cosmpy.aerial.wallet import LocalWallet

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


ONETESTFET=50000000000000000 #0.05 fet
CONVERT = 1000000000000000000 #1 FET

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
    mnemonic : str = Field(
        description="user's mnemonic phrase of ASI wallet",
    )
    amount : str = Field(
        description="amount of FET to be sent to recipient address",
    )
    recipient : str = Field(
        description="recipient wallet address",
    )

class BalanceResponse(Model):
    response : str = Field(
        description="transaction status",
    )


 
@farmer.on_event("startup")
async def introduce_agent(ctx: Context):
    ctx.logger.info(farmer.address)
    ctx.logger.info(farmer.wallet.address())
    ctx.logger.info(f"My name is {ctx.agent.name}")


def func_transaction(mn: str, am: str, re: str) -> str:
    try:
        ledger_client = LedgerClient(NetworkConfig.fetchai_mainnet())

        if not (mn and am and re):
            return "Error: Mnemonic (seed), amount, or recipient address is empty or invalid."

        wallet = LocalWallet.from_mnemonic(mn)
        farmer._logger.info(f"wallet: {wallet.address()}")

        balances = ledger_client.query_bank_balance(wallet.address(), denom='afet')
        balances = (int(balances)/CONVERT)
        farmer._logger.info(f"Balance is: {balances} FET")

        if balances < float(am):
            return f"Insufficient balance: {balances} FET < {am} FET!"

        destination_address = re
        tx = ledger_client.send_tokens(destination_address, int(amount), "afet", wallet)
        tx.wait_to_complete()

        farmer._logger.info(f"TX {tx.tx_hash} waiting to complete...done")

        balances = ledger_client.query_bank_balance(wallet.address(), denom='afet')
        balances = (int(balances)/CONVERT)
        
        farmer._logger.info(f"Transaction was made! Your remaining balance after transaction: {balances} FET")
        return f"Transaction was made: {tx.tx_hash}! Your remaining balance after transaction: {balances} FET"

    except Exception as err:
        farmer._logger.error(f"Transaction error: {err}")
        return f"Error: Transaction failed - {str(err)}"


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
        ctx.logger.error("Discarding message because no session sender found in storage")
        return

    if "<UNKNOWN>" in str(msg.output):
        await ctx.send(
            session_sender,
            create_text_chat(
                "Sorry, I couldn't process your request. Please include a valid mnemonic (seed), amount and recipient address."
            ),
        )
        return

    try:
        # Parse the structured output to get the address
        farmer_request = BalanceRequest.parse_obj(msg.output)
        mn = farmer_request.mnemonic
        am = farmer_request.amount
        re = farmer_request.recipient

        if not (mn and am and re):
            await ctx.send(
                session_sender,
                create_text_chat(
                    "Sorry, I couldn't identify valid information in your query. Please provide your mnemonic phrase (seed), recipient address, and amount of FET."
                ),
            )
            return

        ctx.logger.info(f"Mnemonic received: {mn}")
        ctx.logger.info(f"Amount received: {am}")
        ctx.logger.info(f"Recipient wallet: {re}")

        response_text = func_transaction(str(mn), str(am), str(re))
        ctx.logger.info(f"Transaction response: {response_text}")

        # Send response message
        await ctx.send(session_sender, create_text_chat(response_text))

    except Exception as err:
        ctx.logger.error(f"Error in handle_structured_output_response: {err}")
        await ctx.send(
            session_sender,
            create_text_chat(
                "Sorry, I couldn't make a transaction. Please try again later."
            ),
        )


@proto.on_message(model=BalanceRequest)
async def handle_acknowledgement(ctx: Context, sender: str, msg: BalanceRequest):
    ctx.logger.info(f"Mnemonic received: {msg.mnemonic}")
    ctx.logger.info(f"Amount received: {msg.amount}")
    ctx.logger.info(f"Recipient wallet: {msg.recipient}")

    try:
        # Convert inputs to strings to ensure compatibility
        response_text = func_transaction(str(msg.mnemonic), str(msg.amount), str(msg.recipient))
        ctx.logger.info(f"Transaction response: {response_text}")
    except Exception as err:
        ctx.logger.error(f"Error in handle_acknowledgement: {err}")
        response_text = f"Sorry, I couldn't make a transaction: {str(err)}"

    await ctx.send(sender, BalanceResponse(response=response_text))



# Include the protocol in the agent to enable the chat functionality
# This allows the agent to send/receive messages and handle acknowledgements using the chat protocol
farmer.include(chat_proto, publish_manifest=True)
farmer.include(struct_output_client_proto, publish_manifest=True)
farmer.include(proto, publish_manifest=True)


if __name__ == "__main__":
    farmer.run()
