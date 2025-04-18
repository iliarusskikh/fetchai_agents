from datetime import datetime
from uuid import uuid4
from typing import Any

import os
import logging
import requests
import json

from uagents import Agent, Context, Model, Protocol, Field
from enum import Enum
from uagents.experimental.quota import QuotaProtocol, RateLimit
from uagents_core.models import ErrorMessage

agent = Agent()



# Import the necessary components of the chat protocol
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    EndSessionContent,
    StartSessionContent,
    TextContent,
    chat_protocol_spec,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Solana RPC endpoint
SOLANA_RPC_URL = "https://api.mainnet-beta.solana.com"

class SolanaRequest(Model):
    address: str = Field(
        description="Solana wallet address to check",
    )

class SolanaResponse(Model):
    balance: str = Field(
        description="Formatted Solana wallet balance",
    )
    
class StructuredOutputPrompt(Model):
    prompt: str
    output_schema: dict[str, Any]

class StructuredOutputResponse(Model):
    output: dict[str, Any]

    
    

# Startup Handler - Print agent details
@agent.on_event("startup")
async def startup_handler(ctx: Context):
    ctx.logger.info(f"my address is {ctx.agent.address}")
    
    
    
async def get_balance_from_address(address: str) -> str:
    """
    Get the balance for a Solana address using the Solana RPC API
    
    Args:
        address: Solana wallet address
        
    Returns:
        Formatted balance string
    """
    try:
        logger.info(f"Getting balance for address: {address}")
        
        # Prepare the request payload
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getBalance",
            "params": [address]
        }
        
        # Set headers
        headers = {
            "Content-Type": "application/json"
        }
        
        # Make the API request
        response = requests.post(SOLANA_RPC_URL, headers=headers, json=payload)
        response.raise_for_status()
        
        # Parse the response
        result = response.json()
        
        if "error" in result:
            error_msg = f"Error: {result['error']['message']}"
            logger.error(error_msg)
            return error_msg
            
        if "result" in result and "value" in result["result"]:
            # Convert lamports to SOL (1 SOL = 1,000,000,000 lamports)
            lamports = result["result"]["value"]
            sol_balance = lamports / 1_000_000_000
            
            # Format the result
            result_str = f"{sol_balance:.9f} SOL ({lamports} lamports)"
            logger.info(f"Balance for {address}: {result_str}")
            return result_str
        else:
            error_msg = "No balance information found"
            logger.error(error_msg)
            return error_msg
            
    except requests.exceptions.RequestException as e:
        error_msg = f"Request error: {str(e)}"
        logger.error(error_msg)
        return error_msg
    except json.JSONDecodeError as e:
        error_msg = f"JSON decode error: {str(e)}"
        logger.error(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(error_msg)
        return error_msg



# AI Agent Address for structured output processing
AI_AGENT_ADDRESS = 'agent1q2gmk0r2vwk6lcr0pvxp8glvtrdzdej890cuxgegrrg86ue9cahk5nfaf3c'
#ai agent agent1q0h70caed8ax769shpemapzkyk65uscw4xwk6dc4t3emvp5jdcvqs9xs32y
#test-agent://agent1q2gmk0r2vwk6lcr0pvxp8glvtrdzdej890cuxgegrrg86ue9cahk5nfaf3c
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

chat_proto = Protocol(spec=chat_protocol_spec)
struct_output_client_proto = Protocol(
    name="StructuredOutputClientProtocol", version="0.1.0"
)



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
                    prompt=item.text, output_schema=SolanaRequest.schema()
                ),
            )
        else:
            ctx.logger.info(f"Got unexpected content from {sender}")

@chat_proto.on_message(ChatAcknowledgement)
async def handle_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    ctx.logger.info(
        f"Got an acknowledgement from {sender} for {msg.acknowledged_msg_id}"
    )


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
                "Sorry, I couldn't process your request. Please include a valid Solana wallet address."
            ),
        )
        return

    try:
        # Parse the structured output to get the address
        wallet_request = SolanaRequest.parse_obj(msg.output)
        address = wallet_request.address
        
        if not address:
            await ctx.send(
                session_sender,
                create_text_chat(
                    "Sorry, I couldn't find a valid Solana wallet address in your query."
                ),
            )
            return
        
        # Get the balance for this address
        balance = await get_balance_from_address(address)
        
        # Create a nicely formatted response
        response_text = f"Wallet Balance for `{address}`:\n{balance}\n\n[View on Solana Explorer](https://explorer.solana.com/address/{address})"
        
        # Send the response back to the user
        await ctx.send(session_sender, create_text_chat(response_text))
        
    except Exception as err:
        ctx.logger.error(err)
        await ctx.send(
            session_sender,
            create_text_chat(
                "Sorry, I couldn't check the wallet balance. Please try again later."
            ),
        )
        return






proto = QuotaProtocol(
    storage_reference=agent.storage,
    name="Solana-Wallet-Protocol",
    version="0.1.0",
    default_rate_limit=RateLimit(window_size_minutes=60, max_requests=300),
)

@proto.on_message(
    SolanaRequest, replies={SolanaResponse, ErrorMessage}
)
async def handle_request(ctx: Context, sender: str, msg: SolanaRequest):
    ctx.logger.info(f"Received wallet balance request for address: {msg.address}")
    try:
        balance = await get_balance_from_address(msg.address)
        ctx.logger.info(f"Successfully fetched wallet balance for {msg.address}")
        await ctx.send(sender, SolanaResponse(balance=balance))
    except Exception as err:
        ctx.logger.error(err)
        await ctx.send(sender, ErrorMessage(error=str(err)))

agent.include(proto, publish_manifest=True)

### Health check related code
def agent_is_healthy() -> bool:
    """
    Implement the actual health check logic here.
    For example, check if the agent can connect to the Solana RPC API.
    """
    try:
        import asyncio
        asyncio.run(get_balance_from_address("AtTjQKXo1CYTa2MuxPARtr382ZyhPU5YX4wMMpvaa1oy"))
        return True
    except Exception:
        return False

class HealthCheck(Model):
    pass

class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"

class AgentHealth(Model):
    agent_name: str
    status: HealthStatus

health_protocol = QuotaProtocol(
    storage_reference=agent.storage, name="HealthProtocol", version="0.1.0"
)

@health_protocol.on_message(HealthCheck, replies={AgentHealth})
async def handle_health_check(ctx: Context, sender: str, msg: HealthCheck):
    status = HealthStatus.UNHEALTHY
    try:
        if agent_is_healthy():
            status = HealthStatus.HEALTHY
    except Exception as err:
        ctx.logger.error(err)
    finally:
        await ctx.send(sender, AgentHealth(agent_name="solana_wallet_agent", status=status))

agent.include(health_protocol, publish_manifest=True)
agent.include(chat_proto, publish_manifest=True)
agent.include(struct_output_client_proto, publish_manifest=True)

if __name__ == "__main__":
    agent.run()
