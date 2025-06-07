import os
import time
import boto3
import logging
import redis
import asyncio
import telegram
import json
from datetime import datetime
from database.db import get_db_session
from database.models import User
from cache.redis_client import redis_client
from dotenv import load_dotenv
from services.amazon.amazon_client import get_access_token
from services.amazon.order_api import get_order_details, get_order_items_details
from services.amazon.order_parser import parse_order_data, parse_order_items


def extract_order_status(raw_body: str) -> tuple[str | None, str | None]:
    """Return order ID and status from a raw SQS notification."""
    try:
        outer = json.loads(raw_body)
        payload = outer.get("Payload", {})
        notif = payload.get("OrderChangeNotification", {})
        summary = notif.get("Summary", {})
        order_id = notif.get("AmazonOrderId")
        status = summary.get("OrderStatus")
        return order_id, status
    except Exception as e:
        logger.error(f"Failed to parse order status: {e}")
        return None, None


load_dotenv()

# Логгирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sqs_listener")

# Telegram Bot
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
bot = telegram.Bot(token=TELEGRAM_TOKEN)

region_name=os.getenv("AWS_REGION")
aws_access_key_id=os.getenv("AWS_ACCESS_KEY")
aws_secret_access_key=os.getenv("AWS_SECRET_KEY")

# SQS
sqs = boto3.client(
    "sqs",
    region_name=region_name,
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
)
QUEUE_URL = os.getenv("SQS_QUEUE_URL")

def get_authorized_user_ids():
    """Берёт список всех Telegram ID, кто авторизован."""
    with get_db_session() as session:
        users = session.query(User).filter_by(amazon_authorized=True).all()
        return [int(user.telegram_id) for user in users if user.telegram_id]


def process_message(message_body: str):
    """Обрабатываем сообщение перед отправкой в Telegram (можно доработать фильтрацию)"""
    return (
        f"🔔 <b>Amazon Notification</b>\n\n"
        f"{message_body}"
        )

def get_order(order_id: str):
    access_token = get_access_token()
    marketplace_id = "ATVPDKIKX0DER"  # для amazon.com
    return get_order_details(order_id, access_token, marketplace_id)

def get_items(order_id: str):
    access_token = get_access_token()
    marketplace_id = "ATVPDKIKX0DER"  # для amazon.com
    return get_order_items_details(order_id, access_token, marketplace_id)

def format_amazon_notification(raw_body: str) -> str:
    try:
        outer = json.loads(raw_body)
        payload = outer.get("Payload", {})
        notif = payload.get("OrderChangeNotification", {})
        summary = notif.get("Summary", {})
        order_id = notif.get("AmazonOrderId")
        status = summary.get("OrderStatus")
        sku = summary.get("OrderItems", [{}])[0].get("SellerSKU")
        quantity = summary.get("OrderItems", [{}])[0].get("Quantity")
        purchase_date = summary.get("PurchaseDate")
        fulfillment = summary.get("FulfillmentType")

        pretty_status = {
            "Pending": "🆕 Новый заказ.",
            "Unshipped": "📦 Подтверждён, готов к отгрузке.",
            "Shipped": "🚚 Заказ отправлен.",
            "Canceled": "❌ 	Заказ отменён.",
            "Delivered": "✅ Заказ доставлен",
        }.get(status, status)

        formatted_date = (
            datetime.fromisoformat(purchase_date.replace("Z", "+00:00"))
            .strftime("%d.%m.%Y, %H:%M") if purchase_date else "—"
        )

        fulfillment_type = "FBA" if fulfillment == "AFN" else fulfillment

        # Детали
        order_data = parse_order_data(get_order(order_id))
        order_items = parse_order_items(get_items(order_id))
        print(order_items)

        # Title
        titles = [item.get("Title", "Unknown Item") for item in order_items]
        combined_title = ", ".join(titles)

        # 💰 Сумма заказа
        order_total = order_data.get("OrderTotal", {})
        amount = order_total.get("Amount")
        currency = order_total.get("CurrencyCode")
        total_str = f"{amount} {currency}" if amount and currency else "—"

        # 📍 Адрес
        address = order_data.get("ShippingAddress", {})
        city = address.get("City")
        region = address.get("StateOrRegion")
        postal = address.get("PostalCode")
        country = address.get("CountryCode")

        address_str = (
            f"{city}, {region}, {postal}, {country}"
            if all([city, region, postal, country])
            else "—"
        )

        return (
            f"📦 <b>Заказ!</b>\n\n"
            f"🛍️ <b>Товары:</b> {combined_title}\n"
            f"📌 <b>Статус:</b> {pretty_status}\n"
            f"🔢 <b>Кол-во:</b> {quantity or '—'}\n"
            f"📅 <b>Дата покупки:</b> {formatted_date}\n"
            f"💵 <b>Сумма:</b> {total_str}\n"
            f"📍 <b>Адрес доставки:</b> {address_str}\n"
            f"🛒 <b>Номер:</b> {order_id}\n"
            f"🔁 <b>Тип выполнения:</b> {fulfillment_type}"
        )
    except Exception as e:
        return f"⚠️ Ошибка при обработке уведомления: {e}"


async def notify_users(message: str, user_ids: list[int]):
    for uid in user_ids:
        try:
            await bot.send_message(chat_id=uid, text=message, parse_mode="HTML")
        except Exception as e:
            logger.warning(f"Failed to send message to {uid}: {e}")


async def listen_to_queue():
    logger.info("Listening to SQS...")

    while True:
        try:
            response = sqs.receive_message(
                QueueUrl=QUEUE_URL,
                MaxNumberOfMessages=10,
                WaitTimeSeconds=20,
            )

            messages = response.get("Messages", [])
            if messages:
                authorized_users = get_authorized_user_ids()
                for msg in messages:
                    msg_body = msg["Body"]
                    logger.info(f"Received SQS notification: {msg_body}")
                    prepared_message = format_amazon_notification(msg_body)
                    processed = process_message(prepared_message)
                    await notify_users(processed, authorized_users)

                    order_id, status = extract_order_status(msg_body)
                    if status == "Shipped" and order_id:
                        redis_client.xadd("review_queue", {"orderId": order_id})
                        logger.info(
                            f"Added order {order_id} to review_queue at {datetime.utcnow()}"
                        )

                    # Удаляем сообщение из очереди
                    sqs.delete_message(
                        QueueUrl=QUEUE_URL,
                        ReceiptHandle=msg["ReceiptHandle"]
                    )
        except Exception as e:
            logger.error(f"Error while polling SQS: {e}")
            time.sleep(5)  # wait before retry
