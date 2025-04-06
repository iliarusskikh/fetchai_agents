from uagents.agent import AgentRepresentation #to use txn wallet
from uagents import Agent, Bureau, Context, Model
from logging import Logger


class MessageRequest(Model):
    status: str

class MessageResponse(Model):
    status: str


agent = Agent(
    name="Agent2 sync communication test",
    port=8004,
    seed="123123123123oijvrpjviewjpojpovjo1212",
    endpoint=["http://localhost:8004/submit"],
)


@agent.on_event("startup")
async def introduce_agent(ctx: Context):
    ctx.logger.info(agent.address)
    
 
@agent.on_message(model=MessageRequest)
async def receive_message_request(ctx: Context, sender: str, msg: MessageRequest):
   ctx.logger.info(f"Received message: {msg.status}")
   await ctx.send(sender, MessageResponse(status="Connection established!"))


if __name__ == "__main__":
    agent.run()

