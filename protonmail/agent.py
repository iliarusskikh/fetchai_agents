#pip install protonmail-api-client
#pip install "uagents-adapter[mcp]"
from uagents_adapter import MCPServerAdapter
from server import mcp
import os
from dotenv import load_dotenv
from uagents import Agent, Context, Model


# Load environment variables from .env file
load_dotenv()

# Create an MCP adapter with your MCP server
mcp_adapter = MCPServerAdapter(
    mcp_server=mcp,                     # (FastMCP) Your MCP server instance
    asi1_api_key = os.getenv('ASI1_API_KEY'),
    model="asi1-mini"              # (str) Model to use: "asi1-mini", "asi1-extended", or "asi1-fast"
)

# Create a uAgent
agent = Agent(
    name="Protonmail MCP Client",
    port=8004,
    seed="protonmail_mcp_client_11072025_secret_phrase",
    mailbox = True,
    )

# Include protocols from the adapter - imports chat protocol
for protocol in mcp_adapter.protocols:
    agent.include(protocol, publish_manifest=True)

if __name__ == "__main__":
    # Run the MCP adapter with the agent
    mcp_adapter.run(agent)

