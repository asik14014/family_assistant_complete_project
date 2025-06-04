# middlewares/middleware.py
import logging
from telegram import Update
from telegram.ext import ContextTypes
from cache.redis_client import redis_client

logger = logging.getLogger("middleware")

async def authorize_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if update.effective_user is None:
        return True  # игнорируем system events

    user_id = str(update.effective_user.id)
    key = f"user:{user_id}"

    if not redis_client.exists(key):
        logger.warning(f"Unauthorized user {user_id} tried to access the bot.")
        if update.message:
            await update.message.reply_text("⛔️ You are not authorized to use this bot.")
        return False

    return True


async def process_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Application-level middleware for authorization."""
    is_authorized = await authorize_user(update, context)
    if not is_authorized:
        raise Exception("Blocked unauthorized user.")
