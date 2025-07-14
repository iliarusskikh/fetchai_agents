#pip install --upgrade uagents-adapter
#pip install python-a2a
#pip install "uagents-adapter[a2a-inbound]"

import asyncio
import json
from uuid import uuid4
from typing import Dict, Any

import httpx
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import (
    AgentCard,
    MessageSendParams,
    SendMessageRequest,
)

class SimpleA2AClient:
    """Simple A2A client for multi-agent coordination."""
    
    def __init__(self):
        self.agents: Dict[str, dict] = {}
        self.httpx_client = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.httpx_client = httpx.AsyncClient(timeout=100)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.httpx_client:
            await self.httpx_client.aclose()
    
    async def discover_agent(self, url: str, name: str):
        """Discover an agent and add to available agents."""
        try:
            resolver = A2ACardResolver(self.httpx_client, url)
            agent_card = await resolver.get_agent_card()
            
            client = A2AClient(self.httpx_client, agent_card, url=url)
            
            self.agents[name] = {
                'card': agent_card,
                'client': client,
                'url': url
            }
            
            print(f"✅ Discovered {name}: {agent_card.name}")
            print(f"   Description: {agent_card.description}")
            print(f"   Skills: {[skill.name for skill in agent_card.skills]}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to discover {name} at {url}: {e}")
            return False
    
    async def send_to_agent(self, agent_name: str, message: str, context_id: str = None) -> dict:
        """Send a message to a specific agent."""
        if agent_name not in self.agents:
            raise ValueError(f"Agent {agent_name} not found")
        
        client = self.agents[agent_name]['client']
        
        payload = {
            'message': {
                'role': 'user',
                'parts': [{'kind': 'text', 'text': message}],
                'messageId': uuid4().hex,
            }
        }
        
        if context_id:
            payload['message']['contextId'] = context_id
        
        request = SendMessageRequest(
            id=str(uuid4()),
            params=MessageSendParams(**payload)
        )
        
        response = await client.send_message(request)
        return response.model_dump(mode='json', exclude_none=True)
    
    def list_agents(self):
        """List all discovered agents."""
        print("\n📋 Available Agents:")
        for name, info in self.agents.items():
            card = info['card']
            print(f"  • {name} ({card.name})")
            print(f"    URL: {info['url']}")
            print(f"    Description: {card.description}")
            print()

async def main():
    """Demonstrate A2A client with multi-agent coordination."""
    
    async with SimpleA2AClient() as client:
        print("🔍 Discovering agents...")
        
        # Discover both agents
        agents_to_discover = [
            ("perplexity", "http://localhost:9002"),
            ("finance", "http://localhost:9003"),
        ]
        
        for name, url in agents_to_discover:
            await client.discover_agent(url, name)
        
        # List discovered agents
        client.list_agents()
        
#        # Example 1: Single agent query
#        print("🧪 Example 1: Single Agent Query")
#        print("-" * 40)
#        
#        try:
#            response = await client.send_to_agent(
#                "perplexity",
#                "What are the latest trends in sustainable investing?",
#                context_id="search-session-001"
#            )
#            print("Perplexity Response:")
#            print(json.dumps(response, indent=2))
#        except Exception as e:
#            print(f"Error querying Perplexity agent: {e}")
#        
#        print("\n" + "="*50 + "\n")
        
        # Example 2: Coordinated multi-agent query
        print("🧪 Example 2: Multi-Agent Coordination")
        print("-" * 40)
        
        # Query both agents with related questions
        search_task = client.send_to_agent(
            "perplexity",
            "Find recent news about ESG investment performance in 2025",
            context_id="coordination-001"
        )
        
        finance_task = client.send_to_agent(
            "finance",
            "How should I evaluate ESG investment opportunities for my portfolio?",
            context_id="coordination-002"
        )
        
        try:
            # Wait for both responses
            search_result, finance_result = await asyncio.gather(search_task, finance_task)
            
#            print("🔍 Search Agent (ESG News):")
#            print(json.dumps(search_result, indent=2))
#            print("\n" + "-"*40 + "\n")
            
            print("💰 Finance Agent (ESG Evaluation):")
#            print(json.dumps(finance_result, indent=2))
            
            #_______________________________________________________________
            try:
                # Navigate to status.message.parts
                status_message_parts = (finance_result.get("result", {}).get("status", {}).get("message", {}).get("parts", []))[0].get("text","")
                # Check if parts is a list and not empty
                if not status_message_parts:
                    print("No response found.")
                else:
                    # Find the specific text component
                    print(status_message_parts)

            except json.JSONDecodeError as e:
                print(f"Error parsing JSON: {e}")
            except Exception as e:
                print(f"An error occurred: {e}")
            #_______________________________________________________________

        except Exception as e:
            print(f"Error in multi-agent coordination: {e}")

if __name__ == "__main__":
    print("🚀 A2A Multi-Agent Client Example")
    print("=" * 50)
    asyncio.run(main())
