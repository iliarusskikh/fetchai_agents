#pip install fastapi uvicorn
#pip install aiohttp
from uagents import Agent, Context, Model, Bureau, Protocol
import time
import json


class RequestMessage(Model):
    text: str
 
class ResponseMessage(Model):
    text: str
    

initiator_agent = Agent(
    name="InitiatorAgent",
    seed="initiator recovery phrase123123",
)
 
responder_agent = Agent(
    name="ResponderAgent",
    seed="responder recovery phrase123123",
)



@initiator_agent.on_event("startup")
async def introduce_agent(ctx: Context):
    ctx.logger.info(f"Agent1 started with address: {initiator_agent.address}")

@responder_agent.on_event("startup")
async def introduce_agent(ctx: Context):
    ctx.logger.info(f"Agent2 started with address: {responder_agent.address}")




initiator_protocol = Protocol(name="SimpleProtocol_Initiator", version="0.1.0")
responder_protocol = Protocol(name="SimpleProtocol_Responder", version="0.1.0")


@initiator_protocol.on_interval(period=10.0)
async def initiator_send_message(ctx: Context):
    await ctx.send(responder_agent.address, RequestMessage(text="Hello there from Initiator!"))
    

@responder_protocol.on_message(RequestMessage, replies=ResponseMessage)
async def responder_handle_message(ctx: Context, sender: str, msg: RequestMessage):
    ctx.logger.info(f"Received message from {sender}: {msg.text}")
    await ctx.send(sender, ResponseMessage(text="Hello there from Responder!"))


@initiator_protocol.on_message(model=ResponseMessage)
async def initiator_handle_response(ctx: Context, sender: str, msg: ResponseMessage):
    ctx.logger.info(f"Received response from {sender}: {msg.text}")
    
  

bureau = Bureau(endpoint=["http://127.0.0.1:8001/submit"])
bureau.add(initiator_agent)
bureau.add(responder_agent)



if __name__ == "__main__":
    initiator_agent.include(initiator_protocol, publish_manifest=True)
    responder_agent.include(responder_protocol, publish_manifest=True)
    bureau.run()
