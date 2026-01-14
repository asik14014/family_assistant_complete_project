import os
import asyncio
from dotenv import load_dotenv
from bots.telegram_bot import run_bot

load_dotenv()
print("Environment variables loaded")

if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_bot())