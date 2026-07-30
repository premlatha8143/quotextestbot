import asyncio
import os
from dotenv import load_dotenv

from bot.quotex_client import QuotexClient

load_dotenv()


async def main():
    client = QuotexClient(
        email=os.getenv("QUOTEX_EMAIL"),
        password=os.getenv("QUOTEX_PASSWORD"),
        account_type=os.getenv("ACCOUNT_TYPE", "demo"),
    )

    ok = await client.connect()

    print("Connected:", ok)

    if ok:
        balance = await client.get_balance()
        print("Balance:", balance)

    await client.disconnect()


asyncio.run(main())