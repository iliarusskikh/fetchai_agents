import os
import logging
import sys
import requests
import atexit
from dotenv import load_dotenv
from uagents import Agent, Context, Model
import asyncio

load_dotenv()       # Load environment variables

# Log on exit
def log_and_exit():
    logging.debug("🚨 Script terminated unexpectedly")
atexit.register(log_and_exit)

# Catch unexpected errors
def handle_unexpected_exception(exc_type, exc_value, exc_traceback):
    logging.error("🔥 Uncaught Exception:", exc_info=(exc_type, exc_value, exc_traceback))
sys.excepthook = handle_unexpected_exception



# Initialize Agent
agent = Agent(
    name="TestLocalChild",
    port=8005,
    seed="test_localhost_phrase_1234555336",
    endpoint=["http://127.0.0.1:8005/submit"],
    )


@agent.on_event("startup")
async def startup(ctx: Context):
    """Initialize agent with a startup message"""
    ctx.logger.info(f"✅ Agent started: {ctx.agent.address}")


if __name__ == "__main__":
    agent.run()
