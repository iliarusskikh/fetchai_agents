from datetime import datetime
from uuid import uuid4
from uagents import Agent, Protocol, Context, Model

import os
import logging
import sys
import requests
import atexit


#import the necessary components from the chat protocol
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    TextContent,
    chat_protocol_spec,
)
# Initialise agent2
agent2 = Agent(name="agent2",seed="123123hel121212loage232323nt1231212coingekoooo")

# Initialize the chat protocol
chat_proto = Protocol(spec=chat_protocol_spec)

class CoinResponse(Model):
    name: str
    symbol: str
    current_price: float
    market_cap: float
    total_volume: float
    price_change_24h: float


def get_crypto_info(blockchain: str) -> CoinResponse:
    match blockchain:
        case "ethereum"|"Ethereum"|"Ethereum network":
            coin_id = "ethereum"
        case "base"| "Base" | "Base network":
            coin_id = "ethereum"
        case "solana"|"Solana":
            coin_id = "solana"
        case "bsc"|"Bsc"| "Bsc network":
            coin_id = "binancecoin"
        case "polygon"|"Polygon"|"Matic-network"|"Matic":
            coin_id = "matic-network"
        case "avalanche"|"Avalanche":
            coin_id = "avalanche-2"
        case "arbitrum" | "Arbitrum"|"Arbitrum network":
            coin_id = "arbitrum"
        case "optimism" |"Optimism"|"Optimism network":
            coin_id = "optimism"
        case "sui"|"Sui":
            coin_id = "sui"
        case "ronin"|"Ronin":
            coin_id = "ronin"
        case "bitcoin"|"Bitcoin":
            coin_id = "bitcoin"
        case _:
            return ValueError(f"Unsupported blockchain: {blockchain}")  # Handle unexpected inputs
            #raise

    """Fetch cryptocurrency information from CoinGecko API"""
    
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
    
    try:
        response = requests.get(url)
        logging.info("🚀 URL for {coint_id} received...")
        response.raise_for_status()  # Raises an error for non-200 responses

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
    # Print agent details
    ctx.logger.info(f"My name is {ctx.agent.name} and my address is {ctx.agent.address}")



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
            

            coinres= str(get_crypto_info(item.text))

            # Send response message
            response = ChatMessage(
                timestamp=datetime.utcnow(),
                msg_id=uuid4(),
                content=[TextContent(type="text", text=coinres)]
            )
            await ctx.send(sender, response)



# Acknowledgement Handler - Process received acknowledgements
@chat_proto.on_message(ChatAcknowledgement)
async def handle_acknowledgement(ctx: Context, sender: str, msg: ChatAcknowledgement):
    ctx.logger.info(f"Received acknowledgement from {sender} for message: {msg.acknowledged_msg_id}")

# Include the protocol in the agent to enable the chat functionality
# This allows the agent to send/receive messages and handle acknowledgements using the chat protocol
agent2.include(chat_proto, publish_manifest=True)

if __name__ == '__main__':
    agent2.run()

