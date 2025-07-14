import asyncio
import json
from uuid import uuid4

import httpx
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import MessageSendParams, SendMessageRequest

async def interactive_client():
    """Interactive A2A client for testing agents."""
    
    agents = {}
    
    async with httpx.AsyncClient(timeout=30) as client:
        # Discover agents
        agent_configs = [
            ("Perplexity Search", "http://localhost:9002"),
            ("Finance Q&A", "http://localhost:9003"),
        ]
        
        print("🔍 Discovering agents...")
        for name, url in agent_configs:
            try:
                resolver = A2ACardResolver(client, url)
                card = await resolver.get_agent_card()
                a2a_client = A2AClient(client, card, url=url)
                agents[name] = a2a_client
                print(f"✅ {name} ready")
            except Exception as e:
                print(f"❌ {name} failed: {e}")
        
        if not agents:
            print("No agents available. Make sure they're running!")
            return
        
        print(f"\n📋 Available agents: {list(agents.keys())}")
        print("💡 Type 'quit' to exit, 'list' to see agents\n")
        
        context_id = str(uuid4())
        
        while True:
            try:
                # Get user input
                user_input = input("You: ").strip()
                
                if user_input.lower() == 'quit':
                    break
                elif user_input.lower() == 'list':
                    print(f"Available agents: {list(agents.keys())}")
                    continue
                elif not user_input:
                    continue
                
                # Route based on keywords
                agent_name = None
                if any(word in user_input.lower() for word in ['search', 'news', 'research', 'find']):
                    agent_name = "Perplexity Search"
                elif any(word in user_input.lower() for word in ['finance', 'money', 'invest', 'stock', 'budget']):
                    agent_name = "Finance Q&A"
                else:
                    print("🤖 Which agent should I use?")
                    for i, name in enumerate(agents.keys(), 1):
                        print(f"  {i}. {name}")
                    
                    choice = input("Choose (1-2): ").strip()
                    if choice == '1':
                        agent_name = list(agents.keys())[0]
                    elif choice == '2':
                        agent_name = list(agents.keys())[1]
                    else:
                        print("Invalid choice!")
                        continue
                
                # Send to chosen agent
                print(f"🤖 Sending to {agent_name}...")
                
                payload = {
                    'message': {
                        'role': 'user',
                        'parts': [{'kind': 'text', 'text': user_input}],
                        'messageId': uuid4().hex,
                        'contextId': context_id
                    }
                }
                
                request = SendMessageRequest(
                    id=str(uuid4()),
                    params=MessageSendParams(**payload)
                )
                
                response = await agents[agent_name].send_message(request)
                result = response.model_dump(mode='json', exclude_none=True)
                
                # Extract and display response
                if 'result' in result and 'artifacts' in result['result']:
                    artifacts = result['result']['artifacts']
                    for artifact in artifacts:
                        if 'parts' in artifact:
                            for part in artifact['parts']:
                                if 'text' in part:
                                    print(f"🤖 {agent_name}: {part['text']}")
                else:
                    print(f"🤖 Raw response: {json.dumps(result, indent=2)}")
                
                print()
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ Error: {e}")
        
        print("👋 Goodbye!")

if __name__ == "__main__":
    asyncio.run(interactive_client())
