from uagents import Agent, Context, Model
from logging import Logger
import time
from typing import Any, Dict


# Define your models
class Request(Model):
    text: str

class Response(Model):
    timestamp: int
    text: str
    agent_address: str


agent = Agent(
    name="Agent2 RESTapi communication test",
    port=8004,
    seed="this is a seed for RESTapi example agent2",
    endpoint=["http://localhost:8004/submit"],
)


@agent.on_event("startup")
async def introduce_agent(ctx: Context):
    ctx.logger.info(agent.address)
    
    
    
# GET endpoint example
@agent.on_rest_get("/rest/get", Response)
async def handle_get(ctx: Context) -> Dict[str, Any]:
    ctx.logger.info("Received GET request")
    return {
        "timestamp": int(time.time()),
        "text": "Hello from the GET handler!",
        "agent_address": ctx.agent.address,
    }

# POST endpoint example
@agent.on_rest_post("/rest/post", Request, Response)
async def handle_post(ctx: Context, req: Request) -> Response:
    ctx.logger.info("Received POST request")
    return Response(
        text=f"Received: {req.text}",
        agent_address=ctx.agent.address,
        timestamp=int(time.time()),
    )
    
    
if __name__ == "__main__":
    agent.run()

