import asyncio
import logging
from cache.redis_client import redis_client as redis
from bots.telegram.handlers.review_handler import send_review_prompt

logger = logging.getLogger(__name__)

STREAM_KEY = "review_queue"
GROUP_NAME = "review_bot"
CONSUMER_NAME = "bot1"

async def run_stream_worker(app):
    try:
        redis.xgroup_create(name=STREAM_KEY, groupname=GROUP_NAME, id="0-0", mkstream=True)
    except Exception:
        pass  # group may already exist

    while True:
        try:
            messages = redis.xreadgroup(
                groupname=GROUP_NAME,
                consumername=CONSUMER_NAME,
                streams={STREAM_KEY: '>'},
                block=5000
            )
            for _stream, msgs in messages:
                for msg_id, msg_data in msgs:
                    order_id = msg_data.get('orderId')
                    if order_id:
                        await send_review_prompt(app, order_id)
                    redis.xack(STREAM_KEY, GROUP_NAME, msg_id)
        except Exception as e:
            logger.error(f"Stream worker error: {e}")
            await asyncio.sleep(1)
