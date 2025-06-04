import os
import asyncio
import uvicorn
from dotenv import load_dotenv
load_dotenv()
print("Environment variables loaded")

from bots.telegram_bot import run_bot
from events.scheduler import run_scheduler_loop

import threading


def start_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_bot())

if __name__ == "__main__":
    threading.Thread(target=run_scheduler_loop, daemon=True).start()
    threading.Thread(target=start_bot, daemon=True).start()
    uvicorn.run("interface:app", host="0.0.0.0", port=8000)