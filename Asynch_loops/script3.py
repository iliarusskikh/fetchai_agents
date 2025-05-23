import asyncio
from uagents import Agent, Context

agent = Agent(
    name="looper",
    seed="<YOUR_SEED>",
    port=8001,
    endpoint=["http://127.0.0.1:8001/submit"],
)

@agent.on_event("startup")
async def startup(ctx: Context):
    ctx.logger.info(">>> Looper is starting up.")

@agent.on_event("shutdown")
async def shutdown(ctx: Context):
    ctx.logger.info(">>> Looper is shutting down.")

async def coro():
    while True:
        print("doing hard work...")
        await asyncio.sleep(1)

if __name__ == "__main__":
    print("Running the agent and coro without an external loop...")
    # Run the agent and coro concurrently using asyncio.run
    async def main():
        # Start coro as a task
        task = asyncio.create_task(coro())
        # Run the agent
        await agent.run_async()
        # Optionally, await the coro task (though it runs indefinitely)
        await task

    asyncio.run(main())
