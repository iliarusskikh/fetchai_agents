#agent1qthmuhfu5xlu4s8uwlq7z2ghxhpdqpj2r8smaushxu0qr3k3zcwuxu87t0t
from datetime import datetime
from uuid import uuid4
from uagents import Agent, Protocol, Context, Model
from uagents.experimental.quota import QuotaProtocol, RateLimit

import os
import logging
import sys
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
# Initialise agent2
agent2 = Agent()


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
    storage_reference=agent2.storage,
    name="FethcFund-CoinInfo-Protocol",
    version="0.1.0",
    default_rate_limit=RateLimit(window_size_minutes=60, max_requests=15),
)


class CoinInfoResponse(Model):
    name: str
    symbol: str
    current_price: float
    market_cap: float
    total_volume: float
    price_change_24h: float


class CoinInfoRequest(Model):
    blockchain: str = Field(
        description="Blockchain or crypto network name to check the price of its native coin",
    )

class StructuredOutputPrompt(Model):
    prompt: str
    output_schema: dict[str, Any]

class StructuredOutputResponse(Model):
    output: dict[str, Any]
    
def get_crypto_info(cryptocurrency: str) -> CoinInfoResponse:
    coin_id =""
    match cryptocurrency.lower():
        case "ethereum"|"eth"|"ethereum network"|"ethereum blockchain":
            coin_id = "ethereum"
        case "base"| "base network"|"base blockchain":
            coin_id = "ethereum"
        case "solana"|"sol"|"solana blockchain"|"solana network":
            coin_id = "solana"
        case "bsc"|"Bsc"| "bsc network"|"bnb"|"bsc blockchain":
            coin_id = "binancecoin"
        case "polygon"|"matic-network"|"matic"|"pol"|"polygon blockchain":
            coin_id = "matic-network"
        case "avalanche"|"avalanche blockchain":
            coin_id = "avalanche-2"
        case "arbitrum"|"arbitrum network"|"arb"|"arbitrum blockchain":
            coin_id = "arbitrum"
        case "optimism"|"optimism network"|"op"|"optimism blockchain":
            coin_id = "optimism"
        case "sui"|"sui blockchain":
            coin_id = "sui"
        case "ronin"|"ronin blockchain":
            coin_id = "ronin"
        case "bitcoin"|"btc"|"bitcoin blockchain":
            coin_id = "bitcoin"
        case _:
            return ValueError(f"Unsupported cryptocurrency: {cryptocurrency}. Please, input the name of the supported crypto.")  # Handle unexpected inputs
            #raise

    """Fetch cryptocurrency information from CoinGecko API"""
    
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
    
    try:
        response = requests.get(url)
        agent._logger.info(f"🚀 URL for {coin_id} received...")
        response.raise_for_status()  # Raises an error for non-200 responses

        data = response.json()
        
        return CoinInfoResponse(
            name=data['name'],
            symbol=data['symbol'].upper(),
            current_price=data['market_data']['current_price']['usd'],
            market_cap=data['market_data']['market_cap']['usd'],
            total_volume=data['market_data']['total_volume']['usd'],
            price_change_24h=data['market_data']['price_change_percentage_24h']
        )
    
    except requests.exceptions.RequestException as e:
        agent._logger.error(f"⚠️ API Request Failed: {e}")
        return CoinInfoResponse(
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
            ctx.storage.set(str(ctx.session), sender)
            await ctx.send(
                AI_AGENT_ADDRESS,
                StructuredOutputPrompt(
                    prompt=item.text, output_schema=CoinInfoRequest.schema()
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
                "Sorry, I couldn't process your request. Please include a valid blockchain name. Supported blockchains: bitcoin, ethereum, bsc, base, optimism, solana, polygon, avalanche, arbitrum, sui, ronin. Thanks!"
            ),
        )
        return

    try:
        # Parse the structured output to get the address
       blockchain_request = CoinInfoRequest.parse_obj(msg.output)
       block = blockchain_request.blockchain
        
       if not block:
           await ctx.send(session_sender,create_text_chat("Sorry, I couldn't find a valid blockchain name in your query."),)
           return
        
       response_text= str(get_crypto_info(str(block)))

       await ctx.send(session_sender, create_text_chat(response_text))

    except Exception as err:
        ctx.logger.error(err)
        await ctx.send(
            session_sender,
            create_text_chat(
                "Sorry, I couldn't check the price for a native token of the supported blockchain provided. Please try again later."
            ),
        )
        return


#agents interactions
async def process_response(ctx: Context, msg: CoinInfoRequest) -> CoinInfoResponse:
    """Process the crypto request and return formatted response"""
    agent2._logger.info(f"🔄 Fetching crypto data for: {msg.blockchain}")

    crypto_data = get_crypto_info(msg.blockchain)
    agent2._logger.info(f"📊 Crypto Info: {crypto_data}")
    return crypto_data


@proto.on_message(model=CoinInfoRequest)
async def handle_message(ctx: Context, sender: str, msg: CoinInfoRequest):
    """Handle incoming messages requesting crypto information"""
    agent2._logger.info(f"📩 Received message from {sender}: {msg.blockchain}")
    
    response = await process_response(ctx, msg)
    await ctx.send(sender, response)

    return response



# Include the protocol in the agent to enable the chat functionality
# This allows the agent to send/receive messages and handle acknowledgements using the chat protocol
agent2.include(chat_proto, publish_manifest=True)
agent2.include(proto, publish_manifest=True)
agent2.include(struct_output_client_proto, publish_manifest=True)

if __name__ == '__main__':
    agent2.run()




# Include the protocol in the agent to enable the chat functionality
# This allows the agent to send/receive messages and handle acknowledgements using the chat protocol
agent2.include(chat_proto, publish_manifest=True)
agent2.include(struct_output_client_proto, publish_manifest=True)

if __name__ == '__main__':
    agent2.run()
