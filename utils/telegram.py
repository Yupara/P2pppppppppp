import os
import requests

# Получи токен бота у @BotFather и поставь его в .env
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("TELEGRAM_ADMIN_CHAT_ID")  # твой Telegram ID

API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

def send_message(chat_id: str, text: str):
    url = f"{API_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    requests.post(url, data=payload)

def notify_admin(text: str):
    send_message(ADMIN_CHAT_ID, text)
