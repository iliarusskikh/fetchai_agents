#curl -d '{"message": "test"}' -H "Content-Type: application/json" -X POST http://localhost:8000/endpoint
#agent1qtytjk4efrjvnm0pkz5uv54g6jp0vh6n0v5kamlvesugzejsd2l47770rfc
from logging import Logger
import time
import json
from fastapi import FastAPI, Request
from uagents import Agent, Context, Model
from uagents.query import query
#from uagents.envelope import Envelope



# Define your models
class TestRequest(Model):
    message: str
    

agent = Agent(
    name="Agent2 FASTapi communication test",
    port=8004,
    seed="this is a seed for FASTapi example agent2",
    endpoint=["http://localhost:8004/submit"],
)


@agent.on_event("startup")
async def introduce_agent(ctx: Context):
    ctx.logger.info(agent.address)
    


AGENT_ADDRESS = "agent1qg0pz9vv9d2zwevvpjegkl067yc9kkkcsmnxunj5qrky8welrpnekp4c502"
 

 
async def agent_query(req):
    response = await query(destination=AGENT_ADDRESS, message=req, timeout=15)
    if isinstance(response, Envelope):
        data = json.loads(response.decode_payload())
        return data["text"]
    return response
 
 
app = FastAPI()
 
@app.get("/")
def read_root():
    return "Hello from the Agent controller"
 
 
@app.post("/endpoint")
async def make_agent_call(req: Request):
    model = TestRequest.parse_obj(await req.json())
    try:
        res = await agent_query(model)
        return f"successful call - agent response: {res}"
    except Exception:
        return "unsuccessful agent call"
 

    
if __name__ == "__main__":
    agent.run()






 
