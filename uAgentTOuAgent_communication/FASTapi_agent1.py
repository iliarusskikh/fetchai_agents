#pip install fastapi uvicorn
#pip install aiohttp
from uagents import Agent, Context, Model
import aiohttp  # For async HTTP requests
import time
import json

# Define your models (same as Agent2)
class TestRequest(Model):
    message: str

class TestResponse(Model):
    text: str

agent = Agent(
    name="Agent1 FASTapi communication test",
    port=8002,
    seed="123123123123oijvrpjviewjpojpovjo",
    endpoint=["http://localhost:8002/submit"],
)

@agent.on_event("startup")
async def introduce_agent(ctx: Context):
    ctx.logger.info(f"Agent1 started with address: {agent.address}")



# Handle incoming queries from Agent2
@agent.on_query(model=TestRequest)
async def handle_query(ctx: Context, sender: str, msg: TestRequest):
    ctx.logger.info(f"Received query from {sender}: {msg.message}")
    # Respond with a TestResponse
    await ctx.send(sender, TestResponse(text=f"Agent1 received: {msg.message}"))



# Periodically interact with Agent2's FastAPI endpoints
@agent.on_interval(period=5)
async def interact_with_agent2(ctx: Context):
    # URLs for Agent2's FastAPI endpoints
    get_url = "http://localhost:8004/"
    post_url = "http://localhost:8004/endpoint"
    
    # Prepare POST payload
    post_payload = TestRequest(message="Hello from Agent1 via POST").json()


    # Use a single aiohttp session for both requests
    async with aiohttp.ClientSession() as session:
    
        # Send GET request to /
        async with session.get(get_url) as get_resp:
            if get_resp.status == 200:
                get_response = await get_resp.text()
                ctx.logger.info(f"GET response from Agent2: {get_response}")
            else:
                ctx.logger.error(f"GET failed: {get_resp.status}")


        # Send POST request to /endpoint
        async with session.post(post_url, data=post_payload, headers={"Content-Type": "application/json"}) as post_resp:
            if post_resp.status == 200:
                post_response = await post_resp.text()
                ctx.logger.info(f"POST response from Agent2: {post_response}")
            else:
                ctx.logger.error(f"POST failed: {post_resp.status}")



if __name__ == "__main__":
    agent.run()
