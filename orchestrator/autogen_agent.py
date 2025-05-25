import logging
from openai import OpenAI
from memory.memory_manager import search_memory
from telegram import ReplyKeyboardMarkup

SYSTEM_PROMPT = """
You are a helpful AI assistant for a family.

Your tasks:
- Recognize user intent (e.g., create task, show weather, send email)
- Ask for missing details
- Decide when to call specific APIs by returning action hints
- If no known action applies, answer the user's question directly

Supported actions:
- CREATE_TASK
- ADD_CALENDAR_EVENT
- GET_WEATHER
- GET_EMAIL_SUMMARY
- SHOW_HOLIDAYS

If action is needed, end response with:
ACTION:<action_type>|<parameters>

Example:
ACTION:CREATE_TASK|Buy milk today 5pm
"""

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("telegram_bot")

client = OpenAI()

# Define the reply keyboard for Telegram
reply_keyboard = [
    ["/weather", "/holiday"],
    ["/addtask", "/tasks"],
    ["/emails", "/events"]
]
reply_markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)

def build_prompt(user_id: str, user_input: str):
    memory_context = search_memory(user_id=user_id, query=user_input, top_k=5)
    prompt = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Context from memory: {memory_context}"},
        {"role": "user", "content": user_input}
    ]
    return prompt

def ask_agent(user_id: str, user_input: str):
    prompt = build_prompt(user_id, user_input)
    logger.info(f"Calling OpenAI API for user {user_id}")
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=prompt,
        temperature=0.5
    )
    reply = response.choices[0].message.content
    logger.info(f"Response from OpenAI for user {user_id}: {reply}")
    return reply, reply_markup
