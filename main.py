import os
from dotenv import load_dotenv
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Грузим токен из .env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError("Не задан BOT_TOKEN в .env")

# Создаём бота
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")


def main_menu_keyboard() -> InlineKeyboardMarkup:
    """Главное меню с тремя пунктами."""
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("📸 Подбор по фото", callback_data="menu_photo"),
    )
    markup.row(
        InlineKeyboardButton("📂 Каталог тюнинга", callback_data="menu_catalog"),
    )
    markup.row(
        InlineKeyboardButton("💬 Связаться с менеджером", callback_data="menu_manager"),
    )
    return markup


def back_keyboard() -> InlineKeyboardMarkup:
    """Меню с одной кнопкой 'Назад в главное меню'."""
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("⬅️ В главное меню", callback_data="back_main")
    )
    return markup


# --- /start --- #
@bot.message_handler(commands=["start"])
def handle_start(message):
    text = (
        "Привет! Я бот-помощник по тюнингу авто 🚗\n\n"
        "Я смогу:\n"
        "• подобрать обвесы и диски под твою машину\n"
        "• показать, как это будет выглядеть (ИИ-визуализация)\n"
        "• передать твой запрос менеджеру\n\n"
        "Выбери, с чего начнём:"
    )
    bot.send_message(message.chat.id, text, reply_markup=main_menu_keyboard())


# --- обработка нажатий на кнопки --- #
@bot.callback_query_handler(func=lambda call: True)
def handle_menu_callback(call):
    data = call.data

    if data == "menu_photo":
        # Пользователь выбрал "Подбор по фото" → остаётся только кнопка "Назад"
        text = (
            "📸 *Подбор по фото*\n\n"
            "Отправь мне фото своей машины (желательно сбоку или 3/4 спереди), "
            "и я помогу подобрать тюнинг.\n\n"
        )
        bot.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode="Markdown",
            reply_markup=back_keyboard(),
        )

    elif data == "menu_catalog":
        # Пользователь выбрал "Каталог" → только кнопка "Назад"
        text = (
            "📂 *Каталог тюнинга*\n\n"
            "Здесь будет каталог наших обвесов и дисков, "
            "фильтр по марке, модели и году авто.\n\n"
        )
        bot.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode="Markdown",
            reply_markup=back_keyboard(),
        )

    elif data == "menu_manager":
        # Пользователь выбрал "Связаться с менеджером" → только кнопка "Назад"
        text = (
            "💬 *Связаться с менеджером*\n\n"
            "Напиши свой вопрос и контакт (телеграм/телефон), "
            "а мы заберём это как лид и передадим живому человеку.\n\n"
        )
        bot.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode="Markdown",
            reply_markup=back_keyboard(),
        )

    elif data == "back_main":
        # Вернуться в главное меню: восстанавливаем исходный текст и три пункта
        text = (
            "Привет! Я бот-помощник по тюнингу авто 🚗\n\n"
            "Я смогу:\n"
            "• подобрать обвесы и диски под твою машину\n"
            "• показать, как это будет выглядеть (ИИ-визуализация)\n"
            "• передать твой запрос менеджеру\n\n"
            "Выбери, с чего начнём:"
        )
        bot.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=main_menu_keyboard(),
        )

    # убираем "часики" на кнопке
    bot.answer_callback_query(call.id)


if __name__ == "__main__":
    print("Bot started, polling...")
    bot.infinity_polling()
