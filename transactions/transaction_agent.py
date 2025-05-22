
from datetime import datetime
from uuid import uuid4
from uagents import Agent, Protocol, Context, Model


import os
import logging
from logging import Logger
import sys
import requests
import atexit

import cosmpy
from cosmpy.aerial.wallet import LocalWallet
from cosmpy.crypto.keypairs import PrivateKey
from cosmpy.aerial.client import LedgerClient, NetworkConfig
from uagents.network import get_faucet, wait_for_tx_to_complete

import asyncio
from dotenv import load_dotenv

ONETESTFET=50000000000000000 #0.05 fet

load_dotenv()
# Ensure API key is loaded

# Initialise 
agent = Agent(
    name="Transaction wallet execution",
    port=8005,
    seed="dfekwifeioweikfowlkew secret phrase",
    endpoint=["http://127.0.0.1:8005/submit"],
)



@agent.on_event("startup")
async def startup_handler(ctx: Context):
    ctx.logger.info(f"My name is {ctx.agent.name} and my address is {ctx.agent.address}")
    await asyncio.sleep(20)




@agent.on_interval(3000)
async def testtest(ctx: Context):#ctx: Context
    # Creating a random private key
    #private_key = PrivateKey()
    #ledger: LedgerClient = get_ledger()

    ledger_client = LedgerClient(NetworkConfig.fetchai_mainnet())

    mnemonic = "armor dummy word bla bla your mnemonic words for asi wallet" # ADD YOUR MNEMONICS FOR ASI1 WALLET
    wallet = LocalWallet.from_mnemonic(mnemonic)
    
    ctx.logger.info(f"wallet: {wallet.address()}")

    balances = ledger_client.query_bank_all_balances(wallet.address())
    ctx.logger.info(f"Output: {balances}")
    
    #private_key = PrivateKey('<base64 encoded private key>') # Here is where you provide the base64 encoded private key string
    #wallet = LocalWallet(private_key)
    

    #pk = wallet._private_key
    #ctx.logger.info(f"private key: {pk}")

    #keplr wallet fetch1pegsqxt7du740qefluk3axncyt302pduqza0jt
    destination_address = 'fetch1pegsqxt7du740qefluk3axncyt302pduqza0jt' #change to destination address
    tx = ledger_client.send_tokens(destination_address, ONETESTFET, "afet", wallet)

    tx.wait_to_complete()

    ctx.logger.info(f"TX {tx.tx_hash} waiting to complete...done")

    balances = ledger_client.query_bank_all_balances(wallet.address())
    ctx.logger.info(f"After transaction: {balances}")



    # my_wallet = LocalWallet.from_unsafe_seed("registration test wallet")
    # pk = my_wallet._private_key
 




if __name__ == '__main__':
    #load_dotenv()
    agent.run()


