#curl -d '{"text": "test"}' -H "Content-Type: application/json" -X POST http://localhost:8000/rest/post
#curl http://localhost:8000/rest/get
#pip install aiohttp

from uagents import Agent, Context, Model
import aiohttp  # For async HTTP requests
from logging import Logger
import time


# Define your models (same as Agent2)
class Request(Model):
    text: str

class Response(Model):
    timestamp: int
    text: str
    agent_address: str


agent = Agent(
    name="Agent1 RESTapi communication test",
    port=8002,
    seed="this is a seed for RESTapi example agent1",
    endpoint=["http://localhost:8002/submit"],
)

@agent.on_event("startup")
async def introduce_agent(ctx: Context):
    ctx.logger.info(agent.address)

@agent.on_interval(period=10)
async def send_message(ctx: Context):
    # URLs for Agent2's endpoints
    post_url = "http://localhost:8004/rest/post"
    get_url = "http://localhost:8004/rest/get"
    
    # Prepare POST payload
    post_payload = Request(text="REST connection established!").json()

    # Use a single aiohttp session for both requests
    async with aiohttp.ClientSession() as session:
    
        # Send POST request
        async with session.post(post_url, data=post_payload, headers={"Content-Type": "application/json"}) as post_resp:
            if post_resp.status == 200:
                post_response = await post_resp.json()
                ctx.logger.info(f"POST response from Agent2: {post_response}")
            else:
                ctx.logger.error(f"POST failed: {post_resp.status}")


        # Send GET request
        async with session.get(get_url) as get_resp:
            if get_resp.status == 200:
                get_response = await get_resp.json()
                ctx.logger.info(f"GET response from Agent2: {get_response}")
            else:
                ctx.logger.error(f"GET failed: {get_resp.status}")


if __name__ == "__main__":
    agent.run()
