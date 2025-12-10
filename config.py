import os
from dotenv import load_dotenv
import telebot

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("Не задан BOT_TOKEN в .env")

# username и chat_id менеджера (chat_id пока можно оставить 0)
MANAGER_USERNAME = os.getenv("MANAGER_USERNAME", "noisy_bmw_g20")
MANAGER_CHAT_ID = int(os.getenv("MANAGER_CHAT_ID", "0"))

# один общий бот на весь проект
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")
