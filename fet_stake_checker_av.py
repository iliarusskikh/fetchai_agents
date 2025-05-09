from uagents.setup import fund_agent_if_low
from uagents import Agent, Context, Protocol, Model
import random
import logging
from uagents import Field
from uagents.agent import AgentRepresentation #to use txn wallet
#from ai_engine import UAgentResponse, UAgentResponseType
import sys

from logging import Logger

from cosmpy.aerial.client import LedgerClient
from cosmpy.aerial.faucet import FaucetApi
from cosmpy.crypto.address import Address

from uagents.config import TESTNET_REGISTRATION_FEE
from uagents.network import get_faucet, get_ledger
from uagents.utils import get_logger
from uagents.experimental.quota import QuotaProtocol, RateLimit

import argparse
import time

from cosmpy.aerial.config import NetworkConfig
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


farmer = Agent(
    name="Farmer agent faucet collector",
)


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
 
class StakeRequest(Model):
    wallet : str = Field(
        description="user's FET wallet address",
    )

class StakeResponse(Model):
    amount : str = Field(
        description="user's total staked FET amount",
    )



fund_agent_if_low(farmer.wallet.address())
 
@farmer.on_event("startup")
async def introduce_agent(ctx: Context):
    ctx.logger.info(farmer.address)
    ctx.logger.info(farmer.wallet.address())
    ctx.logger.info(f"My name is {ctx.agent.name}")

    #ctx.logger.info(f"My name is {farmer.name}")



 
 #need to add some pause before starting
@farmer.on_interval(43200)
async def get_faucet_farmer(ctx: Context):
    ledger: LedgerClient = get_ledger()
    faucet: FaucetApi = get_faucet()
    agent_balance = ledger.query_bank_balance(Address(farmer.wallet.address()))
    converted_balance = agent_balance/1000000000000000000
    faucet.get_wealth(farmer.wallet.address())
    #ctx.logger.info({agent_balance})
    
    #staking letsgooo
    ledger_client = LedgerClient(NetworkConfig.fetchai_stable_testnet())
    faucet_api = FaucetApi(NetworkConfig.fetchai_stable_testnet())
    validators = ledger_client.query_validators()
    # choose any validator
    validator = validators[2]

    # delegate some tokens to this validator
    tx = ledger_client.delegate_tokens(validator.address, agent_balance, farmer.wallet)
    tx.wait_to_complete()
    #then call function to stake
    #my_wallet = LocalWallet.from_unsafe_seed("registration test wallet")
    ctx.logger.info("Delegation completed.")
    summary = ledger_client.query_staking_summary(farmer.wallet.address())
    totalstaked = summary.total_staked/1000000000000000000
    ctx.logger.info(f"Staked:{totalstaked}")
    global TOTALSTAKEDCOINS
    TOTALSTAKEDCOINS = str(totalstaked)



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
            #ctx.storage.set(str(ctx.session), sender)

            #ledger: LedgerClient = get_ledger()
            #ledger_client = LedgerClient(NetworkConfig.fetchai_stable_testnet())

            #summary = ledger.query_staking_summary(farmer.wallet.address())
            #totalstaked = summary.total_staked/1000000000000000000
            #ctx.logger.info(f"Total stake: {totalstaked}")
            #global TOTALSTAKEDCOINS
            #TOTALSTAKEDCOINS = str(totalstaked)

            #response_text = f"Sorry bro I am busy farming.. My total stake is {TOTALSTAKEDCOINS} FET! Back to work now.."
            #session_sender = ctx.storage.get(str(ctx.session))
            #await ctx.send(session_sender, create_text_chat(response_text))
            #asiprompt = f"You are the fetch ai farmer who farms FET and stakes it onto blockchain. You already have {TOTALSTAKEDCOINS}, and super proud of it. You are an expert in staking (which is farming), and knows everything about blockchain and fetch AI. Now, answer the user query - {item.text}"
            asiprompt = f"Match the output schema given user input: {item.text}."
            await ctx.send(
                AI_AGENT_ADDRESS,
                StructuredOutputPrompt(
                    prompt=asiprompt, output_schema=StakeRequest.schema()
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
                "Sorry, I couldn't process your request. Please include a valid wallet address to check your stake in FET."
            ),
        )
        return

    try:
        # Parse the structured output to get the address
        farmer_request = StakeRequest.parse_obj(msg.output)
        inforesponse = farmer_request.wallet

        if not inforesponse:
            await ctx.send(session_sender,create_text_chat("Sorry, I couldn't find a valid wallet address in your query. Please, provide your wallet address to find your about your stake in FET."),)
            return

        ctx.logger.info(f"Received wallet {inforesponse}")


        ledger: LedgerClient = get_ledger("mainnet")

        summary = ledger.query_staking_summary(inforesponse)
        totalstaked = round((summary.total_staked/1000000000000000000),2)
        ctx.logger.info(f"Total stake: {totalstaked}")


        response_text= f"{totalstaked} FET"
        # Send response message

        await ctx.send(session_sender, create_text_chat(response_text))
        #response = ChatMessage(timestamp=datetime.utcnow(),msg_id=uuid4(),content=[TextContent(type="text", text=coinres)])
        #await ctx.send(session_sender, create_text_chat(response))


        # Send the response back to the user
       # await ctx.send(session_sender, create_text_chat(response_text))
        
    except Exception as err:
        ctx.logger.error(err)
        await ctx.send(
            session_sender,
            create_text_chat(
                "Sorry, I couldn't check your wallet. Please try again later."
            ),
        )
        return
 


@proto.on_message(model=StakeRequest)
async def handle_acknowledgement(ctx: Context, sender: str, msg: StakeRequest):
    ctx.logger.info(f"Received wallet {msg.wallet}")
    
    summary=0
    
    ledger: LedgerClient = get_ledger("mainnet")
    try:
        summary = ledger.query_staking_summary(msg.wallet)
    except Exception as err:
        ctx.logger.error(err)

    totalstaked = round((summary.total_staked/1000000000000000000),2)
    ctx.logger.info(f"Total stake: {totalstaked}")


    response_text= f"{totalstaked} FET"
    # Send response message

    await ctx.send(sender, StakeResponse(amount=response_text))




# Include the protocol in the agent to enable the chat functionality
# This allows the agent to send/receive messages and handle acknowledgements using the chat protocol
farmer.include(chat_proto, publish_manifest=True)
farmer.include(struct_output_client_proto, publish_manifest=True)
farmer.include(proto, publish_manifest=True)


if __name__ == "__main__":
    farmer.run()

#money making farm :D just enter your agents and start printing money!
