from telegram import Update
from telegram.ext import BaseFilter
from cache.redis_client import redis_client

class IsAuthorizedFilter(BaseFilter):
    async def __call__(self, update: Update) -> bool:
        user_id = update.effective_user.id if update.effective_user else None
        if user_id is None:
            return False
        return redis_client.exists(f"user:{user_id}")
