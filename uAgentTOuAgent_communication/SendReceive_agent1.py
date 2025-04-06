from uagents.agent import AgentRepresentation #to use txn wallet
from uagents import Agent, Bureau, Context, Model
from logging import Logger


class MessageRequest(Model):
    status: str

class MessageResponse(Model):
    status: str


agent = Agent(
    name="Agent1 sync communication test",
    port=8002,
    seed="123123123123oijvrpjviewjpojpovjo",
    endpoint=["http://localhost:8002/submit"],
)


@agent.on_event("startup")
async def introduce_agent(ctx: Context):
    ctx.logger.info(agent.address)

 
@agent.on_interval(5)
async def send_message(ctx: Context):
    reply, status = await ctx.send_and_receive("agent1qd5t7hcnc9mjvknhwl6xgzm3hwlq7h8z52w7ker2k9wtqgh602ljvyfmn3x", MessageRequest(status="Success!"), response_type=MessageResponse)
    if isinstance(reply, MessageResponse):
        ctx.logger.info(f"Received awaited response from agent2: {reply.status}")
    else:
        ctx.logger.info(f"Failed to receive response from agent2: {status}")
    
 

if __name__ == "__main__":
    agent.run()

