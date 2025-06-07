import asyncio
import logging
import time
from cache.redis_client import redis_client as redis
from bots.telegram.handlers.review_handler import send_review_prompt
from services.amazon.solicitations import get_review_eligibility

logger = logging.getLogger(__name__)

STREAM_KEY = "review_queue"
GROUP_NAME = "review_bot"
CONSUMER_NAME = "bot1"
CHECK_INTERVAL = 2 * 60 * 60  # 2 hours

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
                block=0,
            )
            for _stream, msgs in messages:
                for msg_id, msg_data in msgs:
                    logger.info(f"Read from {STREAM_KEY}: {msg_data}")
                    order_id = msg_data.get("orderId")
                    ready_at = float(msg_data.get("ready_at", "0"))
                    expire_at = float(msg_data.get("expire_at", "0"))
                    now = time.time()
                    if now < ready_at:
                        logger.info(f"Order {order_id} not ready yet")
                        redis.xadd(STREAM_KEY, msg_data)
                        redis.xack(STREAM_KEY, GROUP_NAME, msg_id)
                        redis.xdel(STREAM_KEY, msg_id)
                        continue
                    if expire_at and now >= expire_at:
                        logger.info(
                            f"Order {order_id} expired, removing from queue")
                        redis.xack(STREAM_KEY, GROUP_NAME, msg_id)
                        redis.xdel(STREAM_KEY, msg_id)
                        continue
                    if order_id:
                        eligible = get_review_eligibility(order_id)
                        logger.info(f"Eligibility for {order_id}: {eligible}")
                        if eligible:
                            await send_review_prompt(app, order_id)
                            redis.xack(STREAM_KEY, GROUP_NAME, msg_id)
                            redis.xdel(STREAM_KEY, msg_id)
                        else:
                            logger.info(
                                f"Order {order_id} not eligible yet, will retry"
                            )
                            redis.xadd(STREAM_KEY, msg_data)
                            redis.xack(STREAM_KEY, GROUP_NAME, msg_id)
                            redis.xdel(STREAM_KEY, msg_id)
        except Exception as e:
            logger.error(f"Stream worker error: {e}")
        await asyncio.sleep(CHECK_INTERVAL)
