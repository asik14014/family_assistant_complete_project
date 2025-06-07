import os
import logging
import asyncio
import redis
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
    CallbackContext,
)
from services.weather_client import get_weather
from services.holiday_client import get_next_holiday
from services.todoist_client import add_task, get_tasks
from services.gmail_client import get_unread_email_summary
from services.calendar_client import get_upcoming_events
from orchestrator.autogen_agent import ask_agent, reply_markup
from memory.memory_manager import save_to_memory
from database.models import User
from database.db import get_db_session
from database.crud import get_user_by_telegram_id, create_or_update_user
from bots.telegram.handlers.review_handler import button_handler
from services.streams.review_stream_worker import run_stream_worker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("telegram_bot")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    telegram_id = user.id
    logger.info(f"User {telegram_id} used /start")

    auth_key = f"auth:{telegram_id}"
    cached_auth = redis_client.get(auth_key)

    if cached_auth is None:
        with get_db_session() as db:
            user_record = create_or_update_user(
                db,
                telegram_id=telegram_id,
                name=user.username or user.full_name,
                authorized=False
            )
            redis_client.setex(auth_key, 604800, "1" if user_record.amazon_authorized else "0")

    welcome_msg = (
        f"Hi {user.name}! 👋\n\n"
        "I'm your Family Assistant. Here's what I can do:\n"
        "/weather — Get the current weather\n"
        "/holiday — See the next public holiday\n"
        "/addtask — Add a Todoist task\n"
        "/tasks — Show your task list\n"
        "/emails — Unread email summary\n"
        "/events — Upcoming calendar events\n\n"
        "Or just ask me anything, and I’ll try to help using AI."
    )
    await update.message.reply_html(welcome_msg)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("telegram.help option called")
    await update.message.reply_text(
        "Commands:\n"
        "/weather <city> - Get weather\n"
        "/holiday - Show next holiday\n"
        "/addtask <task> - Add a Todoist task\n"
        "/tasks - List your Todoist tasks\n"
        "/emails - Unread email summary\n"
        "/events - Upcoming calendar events"
    )

async def weather(update: Update, context: CallbackContext):
    logger.info("telegram.weather option called")
    city = ' '.join(context.args) if context.args else 'Calgary'
    result = get_weather(city)
    await update.message.reply_text(str(result))

async def holiday(update: Update, context: CallbackContext):
    logger.info("telegram.holiday option called")
    result = get_next_holiday()
    await update.message.reply_text(str(result))

async def add_task_command(update: Update, context: CallbackContext):
    logger.info("telegram.addTask option called")
    task = ' '.join(context.args)
    if not task:
        await update.message.reply_text("Please specify a task.")
        return
    result = add_task(task)
    await update.message.reply_text(f"Task added: {result.get('content')}")

async def list_tasks(update: Update, context: CallbackContext):
    logger.info("telegram.listTasks option called")
    tasks = get_tasks()
    if not tasks:
        await update.message.reply_text("No tasks found.")
        return
    message = "\n".join([f"- {task['content']}" for task in tasks])
    await update.message.reply_text(message)

async def email_summary(update: Update, context: CallbackContext):
    logger.info("telegram.emailSummary option called")
    summary = get_unread_email_summary()
    await update.message.reply_text(summary)

async def calendar_events(update: Update, context: CallbackContext):
    logger.info("telegram.events option called")
    events = get_upcoming_events()
    if not events:
        await update.message.reply_text("No upcoming events.")
        return
    message = "\n".join([f"{e['summary']} - {e['start']}" for e in events])
    await update.message.reply_text(message)

async def amazon_orders(update: Update, context: CallbackContext):
    logger.info("telegram.amazon_orders option called")
    city = ' '.join(context.args) if context.args else 'Calgary'
    result = get_weather(city)
    await update.message.reply_text(str(result))

async def handle_action(update: Update, action_type: str, param: str):
    if action_type == "CREATE_TASK":
        task = add_task(param)
        await update.message.reply_text(f"✅ Task added: {task.get('content')}", reply_markup=reply_markup)
    elif action_type == "ADD_CALENDAR_EVENT":
        await update.message.reply_text("📅 Calendar event created (simulated).", reply_markup=reply_markup)
    elif action_type == "GET_WEATHER":
        result = get_weather(param)
        await update.message.reply_text(result, reply_markup=reply_markup)
    elif action_type == "GET_EMAIL_SUMMARY":
        result = get_unread_email_summary()
        await update.message.reply_text(result, reply_markup=reply_markup)
    elif action_type == "SHOW_HOLIDAYS":
        result = get_next_holiday()
        await update.message.reply_text(result, reply_markup=reply_markup)
    else:
        await update.message.reply_text("❓ Sorry, I didn't recognize that action.", reply_markup=reply_markup)

async def ai_message_handler(update: Update, context: CallbackContext):
    logger.info("telegram.chat option called")
    user_id = str(update.effective_user.id)
    user_input = update.message.text

    ai_reply, markup = ask_agent(user_id=user_id, user_input=user_input)

    save_to_memory(user_id, f"User: {user_input}")
    save_to_memory(user_id, f"Assistant: {ai_reply}")

    await update.message.reply_text(ai_reply, reply_markup=markup)

    for line in ai_reply.splitlines():
        if line.startswith("ACTION:"):
            try:
                action_body = line[len("ACTION:"):].strip()
                action_type, param = action_body.split("|", 1)
                await handle_action(update, action_type.strip(), param.strip())
            except Exception as e:
                logger.warning(f"Failed to parse ACTION directive: {e}")

async def run_bot():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("weather", weather))
    app.add_handler(CommandHandler("holiday", holiday))
    app.add_handler(CommandHandler("addtask", add_task_command))
    app.add_handler(CommandHandler("tasks", list_tasks))
    app.add_handler(CommandHandler("emails", email_summary))
    app.add_handler(CommandHandler("events", calendar_events))
    #app.add_handler(CommandHandler("amazon orders", amazon_orders))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ai_message_handler))

    logger.info("🤖 Family Assistant bot is now running...")
    asyncio.create_task(run_stream_worker(app))
    await app.run_polling()
