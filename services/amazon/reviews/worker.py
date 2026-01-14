import asyncio
import time
from services.amazon.reviews.parser import fetch_reviews
from database.db import SessionLocal
from database.db import get_db_session
from database.crud import review_exists, save_review
from database.models import Product, User
from telegram import Bot
from dotenv import load_dotenv
import os
import logging

load_dotenv()

# Логгирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("review_worker")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

bot = Bot(token=TELEGRAM_TOKEN)

def get_authorized_user_ids():
    """Берёт список всех Telegram ID, кто авторизован."""
    with get_db_session() as session:
        users = session.query(User).filter_by(amazon_authorized=True).all()
        return [int(user.telegram_id) for user in users if user.telegram_id]
    
def notify_users(message: str, user_ids: list[int]):
    for uid in user_ids:
        try:
            bot.send_message(chat_id=uid, text=message, parse_mode="HTML")
        except Exception as e:
            logger.warning(f"Failed to send message to {uid}: {e}")

def send_to_telegram(review: dict):
    authorized_users = get_authorized_user_ids()
    text = f"🟡 Новый отзыв на товар\n⭐ {review['rating']}\n📌 {review['title']}\n📝 {review['text']}"
    notify_users(text, authorized_users)

def monitor_asin(asin: str):
    session = SessionLocal()
    try:
        reviews = fetch_reviews(asin)
        for r in reviews:
            if review_exists(session, r['id']):
                break
            if save_review(session, asin, r):
                send_to_telegram(r)
    finally:
        session.close()

def run_review_monitor():
    session = SessionLocal()
    try:
        products = session.query(Product.asin).all()
        print(f"products: {products}")
        asins = [row.asin for row in products]
    finally:
        session.close()

    for asin in asins:
        monitor_asin(asin)
    print(f"Sleep for 3600")
    time.sleep(3600)

if __name__ == "__main__":
    asyncio.run(run_review_monitor())
