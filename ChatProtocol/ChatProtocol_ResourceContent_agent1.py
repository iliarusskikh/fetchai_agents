from datetime import datetime
from uuid import uuid4
from pydantic.v1 import UUID4

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
agent2 = Agent(
    name="ChatProtocolTester",
    seed="123123hel121212loage232323nt1231212coingek123123123123oooo",
)

# Initialize the chat protocol
chat_proto = Protocol(spec=chat_protocol_spec)


# Define CoinResponse model (unchanged)
class CoinResponse(Model):
    name: str
    symbol: str
    current_price: float
    market_cap: float
    total_volume: float
    price_change_24h: float

def get_crypto_info(blockchain: str) -> CoinResponse:
    match blockchain:
        case "ethereum" | "Ethereum" | "Ethereum network":
            coin_id = "ethereum"
        case "base" | "Base" | "Base network":
            coin_id = "ethereum"
        case "solana" | "Solana":
            coin_id = "solana"
        case "bsc" | "Bsc" | "Bsc network":
            coin_id = "binancecoin"
        case "polygon" | "Polygon" | "Matic-network" | "Matic":
            coin_id = "matic-network"
        case "avalanche" | "Avalanche":
            coin_id = "avalanche-2"
        case "arbitrum" | "Arbitrum" | "Arbitrum network":
            coin_id = "arbitrum"
        case "optimism" | "Optimism" | "Optimism network":
            coin_id = "optimism"
        case "sui" | "Sui":
            coin_id = "sui"
        case "ronin" | "Ronin":
            coin_id = "ronin"
        case "bitcoin" | "Bitcoin":
            coin_id = "bitcoin"
        case _:
            raise ValueError(f"Unsupported blockchain: {blockchain}")

    """Fetch cryptocurrency information from CoinGecko API"""
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
    
    try:
        response = requests.get(url)
        logging.info(f"🚀 URL for {coin_id} received...")
        response.raise_for_status()

        data = response.json()
        return CoinResponse(
            name=data['name'],
            symbol=data['symbol'].upper(),
            current_price=data['market_data']['current_price']['usd'],
            market_cap=data['market_data']['market_cap']['usd'],
            total_volume=data['market_data']['total_volume']['usd'],
            price_change_24h=data['market_data']['price_change_percentage_24h']
        )
    except requests.exceptions.RequestException as e:
        logging.error(f"⚠️ API Request Failed: {e}")
        return CoinResponse(
            name="Unknown",
            symbol="N/A",
            current_price=0.0,
            market_cap=0.0,
            total_volume=0.0,
            price_change_24h=0.0
        )

# Startup Handler - Print agent details
@agent2.on_event("startup")
async def startup_handler(ctx: Context):
    ctx.logger.info(f"My name is {ctx.agent.name} and my address is {ctx.agent.address}")

# Message Handler - Process received ChatMessages
@chat_proto.on_message(ChatMessage)
async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
    for item in msg.content:
        # Handle TextContent (existing functionality)
        if isinstance(item, TextContent):
            ctx.logger.info(f"Received TextContent from {sender}: {item.text}")
            
            # Send acknowledgment
            ack = ChatAcknowledgement(
                timestamp=datetime.utcnow(),
                acknowledged_msg_id=msg.msg_id
            )
            await ctx.send(sender, ack)

            # Fetch CoinGecko data
            try:
                coin_res = get_crypto_info(item.text)
                response_text = str(coin_res)
            except ValueError as e:
                response_text = str(e)

            # Send response
            response = ChatMessage(
                timestamp=datetime.utcnow(),
                msg_id=uuid4(),
                content=[TextContent(type="text", text=response_text)]
            )
            await ctx.send(sender, response)

        # Handle ResourceContent (new functionality)
        elif isinstance(item, ResourceContent):
            ctx.logger.info(f"Received ResourceContent from {sender}:")
            ctx.logger.info(f"Resource ID: {item.resource_id}")
            
            # Process resource(s)
            resources = item.resource if isinstance(item.resource, list) else [item.resource]
            for res in resources:
                ctx.logger.info(f"Resource: {res.uri}, Data: {res.metadata}")

            # Send acknowledgment
            ack = ChatAcknowledgement(
                timestamp=datetime.utcnow(),
                acknowledged_msg_id=msg.msg_id
            )
            await ctx.send(sender, ack)

            # Send TextContent response
            response_text = f"Processed {len(resources)} resource(s) with ID {item.resource_id}"
            response = ChatMessage(
                timestamp=datetime.utcnow(),
                msg_id=uuid4(),
                content=[TextContent(type="text", text=response_text)]
            )
            await ctx.send(sender, response)

# Acknowledgement Handler - Process received acknowledgements
@chat_proto.on_message(ChatAcknowledgement)
async def handle_acknowledgement(ctx: Context, sender: str, msg: ChatAcknowledgement):
    ctx.logger.info(f"Received acknowledgement from {sender} for message: {msg.acknowledged_msg_id}")

# Include the protocol in the agent
agent2.include(chat_proto, publish_manifest=True)

if __name__ == "__main__":
    agent2.run()
