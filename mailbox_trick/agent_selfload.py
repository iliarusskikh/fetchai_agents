import os
import logging
import sys
import requests
import atexit
from dotenv import load_dotenv
from uagents import Agent, Context, Model
import asyncio
import json
from functools import partial


load_dotenv() # Load environment variables

MY_COOKIE = os.getenv("MY_COOKIE")

# Configure Logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

# Log on exit
def log_and_exit():
    logging.debug("🚨 Script terminated unexpectedly")
atexit.register(log_and_exit)

# Catch unexpected errors
def handle_unexpected_exception(exc_type, exc_value, exc_traceback):
    logging.error("🔥 Uncaught Exception:", exc_info=(exc_type, exc_value, exc_traceback))
sys.excepthook = handle_unexpected_exception



# Initialize Agent
agent = Agent(
    name="TestLocalhost",
    port=8004,
    seed="test_localhost_phrase_123456",
    endpoint=["http://127.0.0.1:8004/submit"],
    #mailbox=True,
    )


@agent.on_event("startup")
async def startup(ctx: Context):
    """Initialize agent with a startup message"""
    ctx.logger.info(f"✅ Agent started: {ctx.agent.address}")
    await run_in_thread(get_connected,ctx)

    #await get_connected(ctx)



async def run_in_thread(func, *args, **kwargs):
    """
    Run a synchronous function in a separate thread to avoid blocking the event loop.
    Supports both positional and keyword arguments.
    """
    return await asyncio.to_thread(partial(func, *args, **kwargs))


def get_connected(ctx: Context):#ctx: Context
    access_token = get_access_token(ctx)# Get access token
    
    if access_token:
        ctx.logger.info(f"Registering mailbox..")
        register_mailbox(ctx, agent._port, access_token) # Register mailbox

        set_metadata(ctx.agent.address, "some_order_id", access_token)
    else:
        ctx.logger.error("Failed to get access token, skipping mailbox registration and metadata")


#Local Inspector -> on agent_inspector page, right click, inspect page -> network -> open GET request -> Cookies
def get_access_token(ctx: Context) -> str | None:
    """Retrieve access token from Agentverse API"""
    session_url = "https://agentverse.ai/api/session"
    headers = {"Cookie": MY_COOKIE}
    
    try:
        resp = requests.get(session_url, headers=headers)
        if resp.ok:
            access_token = resp.json().get("credentials", {}).get("accessToken")
            if access_token:
                ctx.logger.info(f"Retrieved Access Token!")
                return access_token
            else:
                ctx.logger.info(f"Access token not found in response: {resp.text}")
                return None
        else:
            ctx.logger.info(f"Retrieving Access Token - Failed: {resp.status_code} {resp.text}")
            return None
    except Exception as e:
        ctx.logger.error(f"Error retrieving access token: {e}")
        return None


def register_mailbox(ctx: Context, port: int, access_token: str) -> None:
    """Register the agent's mailbox with Agentverse"""
    connect_url = f"http://127.0.0.1:{port}/connect"
    payload = {
        "user_token": access_token,
        "agent_type": "mailbox"
    }
    
    try:
        ctx.logger.info(f"POST request to '/connect'..")
        resp = requests.post(connect_url, json=payload)

        if resp.ok:
            ctx.logger.info(f"Registering Mailbox - Status: {resp.text}")
        else:
            ctx.logger.info(f"Registering Mailbox - Failed: {resp.status_code} {resp.text}")

    except Exception as e:
        ctx.logger.error(f"Error registering mailbox: {e}")
        


def set_metadata(address: str, order_id: str, access_token: str) -> None:
    """Set metadata for the agent in Agentverse"""
    url = f"https://agentverse.ai/v1/agents/{address}"
    payload = {
        "name": "This is a test agent!",
        "readme": None,
        "avatar_url": None, #"https://storage.googleapis.com/agentverse-prod-assets/agent-avatars-pub/...",
        "short_description": "Some description"
    }
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    try:
        resp = requests.put(url, headers=headers, data=json.dumps(payload))
        if resp.ok:
            print("Setting Agent-Metadata - Status:", resp.text)
        else:
            print(f"Setting Agent-Metadata - Failed: {resp.status_code} {resp.text}")
    except Exception as e:
        print(f"Error setting metadata: {e}")




if __name__ == "__main__":
    agent.run()
