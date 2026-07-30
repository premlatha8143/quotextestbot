import asyncio
import os

from dotenv import load_dotenv

from bot.quotex_client import QuotexClient
from bot.signal_engine import SignalEngine

load_dotenv()


async def main():
    client = QuotexClient(
        os.getenv("QUOTEX_EMAIL"),
        os.getenv("QUOTEX_PASSWORD"),
    )

    ok = await client.connect()

    if not ok:
        print("Connection failed")
        return

    engine = SignalEngine(client)

    result = await engine.analyze()

    print(result)

    await client.disconnect()


asyncio.run(main())