import os
import asyncio
import nest_asyncio
from dotenv import load_dotenv
from services.amazon.reviews.worker import run_review_monitor

load_dotenv()
nest_asyncio.apply()

loop = asyncio.get_event_loop()
loop.run_until_complete(run_review_monitor())