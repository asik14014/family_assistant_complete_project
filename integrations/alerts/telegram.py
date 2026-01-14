# integrations/alerts/telegram.py
from __future__ import annotations
import os, requests
from dataclasses import dataclass
from typing import Optional

@dataclass
class TelegramAlerter:
    bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id: str = os.getenv("TELEGRAM_CHAT_ID", "")

    def __post_init__(self):
        if not self.bot_token or not self.chat_id:
            raise RuntimeError("TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID are required")

    def send(self, text: str, parse_mode: Optional[str] = "Markdown") -> None:
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        data = {"chat_id": self.chat_id, "text": text, "parse_mode": parse_mode}
        r = requests.post(url, data=data, timeout=15)
        try:
            r.raise_for_status()
        except Exception:
            raise RuntimeError(f"Telegram error [{r.status_code}]: {r.text}")
