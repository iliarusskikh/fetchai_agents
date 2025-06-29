from uagents_adapter import MCPServerAdapter
from server import mcp

# Create an MCP adapter with your MCP server
mcp_adapter = MCPServerAdapter(
    mcp_server=mcp,                     # (FastMCP) Your MCP server instance
    asi1_api_key="API_ASI",  # (str) Your ASI:One API key - as secret phrase
    model="asi1-mini"              # (str) Model to use: "asi1-mini", "asi1-extended", or "asi1-fast"
)

# Create a uAgent
agent = Agent()

# Include protocols from the adapter - imports chat protocol
for protocol in mcp_adapter.protocols:
    agent.include(protocol, publish_manifest=True)

if __name__ == "__main__":
    # Run the MCP adapter with the agent
    mcp_adapter.run(agent)
