import os
import asyncio
from dotenv import load_dotenv
from telegram.ext import Application, CallbackQueryHandler
from bots.telegram.handlers.review_handler import button_handler
from services.streams.review_stream_worker import run_stream_worker

load_dotenv()
print("Environment variables loaded")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

async def run_review_bot():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CallbackQueryHandler(button_handler))
    asyncio.create_task(run_stream_worker(app))
    await app.run_polling()

if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_review_bot())
