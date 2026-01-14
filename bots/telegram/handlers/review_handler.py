import logging
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, Application
from cache.redis_client import redis_client
from database.db import get_db_session
from database.models import User
from services.amazon.solicitations import send_review_request

logger = logging.getLogger(__name__)

REVIEW_SENT_TTL = 7 * 24 * 3600
REVIEW_PENDING_TTL = 2 * 24 * 3600


def _get_authorized_user_ids() -> list[int]:
    with get_db_session() as session:
        users = session.query(User).filter_by(amazon_authorized=True).all()
        return [int(u.telegram_id) for u in users if u.telegram_id]


async def send_review_prompt(app: Application, order_id: str):
    """Send review confirmation prompt to admins."""
    if redis_client.exists(f"review_sent:{order_id}"):
        logger.info(f"Redis check review_sent:{order_id} - exists")
        return
    if redis_client.exists(f"review_pending:{order_id}"):
        logger.info(f"Redis check review_pending:{order_id} - exists")
        return

    keyboard = [
        [
            InlineKeyboardButton("✅ Yes", callback_data=f"review_approve_{order_id}"),
            InlineKeyboardButton("❌ No", callback_data=f"review_skip_{order_id}"),
        ]
    ]
    markup = InlineKeyboardMarkup(keyboard)
    message = f"Request Amazon review for order {order_id}?"
    for uid in _get_authorized_user_ids():
        try:
            await app.bot.send_message(chat_id=uid, text=message, reply_markup=markup)
        except Exception as e:
            logger.warning(f"Failed to send review prompt to {uid}: {e}")
    redis_client.setex(f"review_pending:{order_id}", REVIEW_PENDING_TTL, 1)
    logger.info(
        f"Set review_pending:{order_id} with TTL {REVIEW_PENDING_TTL} at {time.time()}"
    )


async def send_review_request_to_amazon(order_id: str) -> bool:
    """Trigger the SP-API review request."""
    try:
        return send_review_request(order_id)
    except Exception as e:
        logger.error(f"Failed to send review request for {order_id}: {e}")
        return False


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data.startswith("review_approve_"):
        order_id = query.data.split("review_approve_")[1]
        success = await send_review_request_to_amazon(order_id)
        if success:
            await query.edit_message_text(f"✅ Review request sent for order {order_id}")
        else:
            await query.edit_message_text(f"⚠️ Failed to send review for order {order_id}")
        redis_client.setex(f"review_sent:{order_id}", REVIEW_SENT_TTL, 1)
        logger.info(
            f"Set review_sent:{order_id} with TTL {REVIEW_SENT_TTL} at {time.time()}"
        )
        redis_client.delete(f"review_pending:{order_id}")
        logger.info(f"Deleted review_pending:{order_id}")
    elif query.data.startswith("review_skip_"):
        order_id = query.data.split("review_skip_")[1]
        await query.edit_message_text(f"⏭ Skipped review request for order {order_id}")
        redis_client.setex(f"review_sent:{order_id}", REVIEW_SENT_TTL, 1)
        logger.info(
            f"Set review_sent:{order_id} with TTL {REVIEW_SENT_TTL} at {time.time()}"
        )
        redis_client.delete(f"review_pending:{order_id}")
        logger.info(f"Deleted review_pending:{order_id}")
