import os
from dotenv import load_dotenv
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- конфиг --- #
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError("Не задан BOT_TOKEN в .env")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")

# простое состояние по пользователям
user_state = {}  # chat_id -> dict


# --- клавиатуры --- #
def main_menu_keyboard() -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("📸 Подбор по фото", callback_data="menu_photo"))
    markup.row(InlineKeyboardButton("📂 Каталог тюнинга", callback_data="menu_catalog"))
    markup.row(InlineKeyboardButton("💬 Связаться с менеджером", callback_data="menu_manager"))
    return markup


def back_keyboard() -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("⬅️ В главное меню", callback_data="back_main"))
    return markup


def catalog_brand_keyboard() -> InlineKeyboardMarkup:
    """Выбор марки авто."""
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🚗 Mercedes", callback_data="brand_mercedes"))
    markup.row(InlineKeyboardButton("🚗 BMW", callback_data="brand_bmw"))
    markup.row(InlineKeyboardButton("✏️ Другая марка", callback_data="brand_other"))
    markup.row(InlineKeyboardButton("⬅️ В главное меню", callback_data="back_main"))
    return markup


def catalog_model_keyboard(brand: str) -> InlineKeyboardMarkup:
    """Выбор модели для конкретной марки."""
    markup = InlineKeyboardMarkup()

    if brand == "Mercedes":
        markup.row(InlineKeyboardButton("CLA", callback_data="model_mercedes_cla"))
        markup.row(InlineKeyboardButton("E-Class", callback_data="model_mercedes_e"))
        markup.row(InlineKeyboardButton("C-Class", callback_data="model_mercedes_c"))
    elif brand == "BMW":
        markup.row(InlineKeyboardButton("3 Series", callback_data="model_bmw_3"))
        markup.row(InlineKeyboardButton("4 Series", callback_data="model_bmw_4"))
        markup.row(InlineKeyboardButton("5 Series", callback_data="model_bmw_5"))

    markup.row(InlineKeyboardButton("⬅️ Выбрать другую марку", callback_data="back_brands"))
    markup.row(InlineKeyboardButton("⬅️ В главное меню", callback_data="back_main"))
    return markup


# --- /start --- #
@bot.message_handler(commands=["start"])
def handle_start(message):
    user_state.pop(message.chat.id, None)  # сброс состояния
    text = (
        "Привет! Я бот-помощник по тюнингу авто 🚗\n\n"
        "Я смогу:\n"
        "• подобрать обвесы и диски под твою машину\n"
        "• показать, как это будет выглядеть (ИИ-визуализация)\n"
        "• передать твой запрос менеджеру\n\n"
        "Выбери, с чего начнём:"
    )
    bot.send_message(message.chat.id, text, reply_markup=main_menu_keyboard())


# --- обработка inline-кнопок --- #
@bot.callback_query_handler(func=lambda call: True)
def handle_menu_callback(call):
    chat_id = call.message.chat.id
    data = call.data

    # ----- главный каталог ----- #
    if data == "menu_catalog":
        user_state[chat_id] = {"step": "catalog_brand"}
        text = (
            "📂 *Каталог тюнинга*\n\n"
            "Сначала выбери марку автомобиля, затем модель.\n\n"
            "Если твоей марки нет в списке — выбери *«Другая марка»* "
            "и введи её вручную."
        )
        bot.edit_message_text(
            text,
            chat_id=chat_id,
            message_id=call.message.message_id,
            parse_mode="Markdown",
            reply_markup=catalog_brand_keyboard(),
        )

    # ----- выбор марки ----- #
    elif data == "brand_mercedes":
        user_state[chat_id] = {"step": "catalog_model", "brand": "Mercedes"}
        text = "Марка: *Mercedes*.\nТеперь выбери модель:"
        bot.edit_message_text(
            text,
            chat_id=chat_id,
            message_id=call.message.message_id,
            parse_mode="Markdown",
            reply_markup=catalog_model_keyboard("Mercedes"),
        )

    elif data == "brand_bmw":
        user_state[chat_id] = {"step": "catalog_model", "brand": "BMW"}
        text = "Марка: *BMW*.\nТеперь выбери модель:"
        bot.edit_message_text(
            text,
            chat_id=chat_id,
            message_id=call.message.message_id,
            parse_mode="Markdown",
            reply_markup=catalog_model_keyboard("BMW"),
        )

    elif data == "brand_other":
        # ждём ручной ввод марки+модели
        user_state[chat_id] = {"step": "catalog_custom"}
        text = (
            "✏️ *Своя марка и модель*\n\n"
            "Напиши марку и модель автомобиля одним сообщением.\n\n"
            "Например: `Toyota Camry 2018`."
        )
        bot.edit_message_text(
            text,
            chat_id=chat_id,
            message_id=call.message.message_id,
            parse_mode="Markdown",
            reply_markup=back_keyboard(),
        )

    # ----- выбор модели (готовые марки) ----- #
    elif data.startswith("model_"):
        mapping = {
            "model_mercedes_cla": ("Mercedes", "CLA"),
            "model_mercedes_e": ("Mercedes", "E-Class"),
            "model_mercedes_c": ("Mercedes", "C-Class"),
            "model_bmw_3": ("BMW", "3 Series"),
            "model_bmw_4": ("BMW", "4 Series"),
            "model_bmw_5": ("BMW", "5 Series"),
        }
        brand, model = mapping.get(data, ("?", "?"))
        user_state[chat_id] = {"step": "catalog_done", "brand": brand, "model": model}

        text = (
            f"✅ Ты выбрал: *{brand} {model}*.\n\n"
            "На следующем шаге здесь будет список комплектов тюнинга, "
            "которые подходят под эту модель.\n\n"
            "Пока это демо, но структура уже готова 👍"
        )
        bot.edit_message_text(
            text,
            chat_id=chat_id,
            message_id=call.message.message_id,
            parse_mode="Markdown",
            reply_markup=back_keyboard(),
        )

    # ----- назад к выбору бренда ----- #
    elif data == "back_brands":
        user_state[chat_id] = {"step": "catalog_brand"}
        text = "Выбери марку автомобиля:"
        bot.edit_message_text(
            text,
            chat_id=chat_id,
            message_id=call.message.message_id,
            reply_markup=catalog_brand_keyboard(),
        )

    # ----- главное меню (откуда угодно) ----- #
    elif data == "back_main":
        user_state.pop(chat_id, None)
        text = (
            "Привет! Я бот-помощник по тюнингу авто 🚗\n\n"
            "Выбери, с чего начнём:"
        )
        bot.edit_message_text(
            text,
            chat_id=chat_id,
            message_id=call.message.message_id,
            reply_markup=main_menu_keyboard(),
        )

    # ----- остальные пункты меню / заглушки ----- #
    elif data == "menu_photo":
        text = (
            "📸 *Подбор по фото*\n\n"
            "Отправь мне фото своей машины (желательно сбоку или 3/4 спереди), "
            "и я помогу подобрать тюнинг.\n\n"
            "_Пока это демо-режим: просто пришли фото, а дальше допилим логику._"
        )
        bot.edit_message_text(
            text,
            chat_id=chat_id,
            message_id=call.message.message_id,
            parse_mode="Markdown",
            reply_markup=back_keyboard(),
        )

    elif data == "menu_manager":
        text = (
            "Если у вас возникла проблема или вы не можете найти тюнинг на своё авто,\n"
            "то напишите нашему менеджеру [Ивану](https://t.me/noisy_bmw_g20)."
        )
        bot.edit_message_text(
            text,
            chat_id=chat_id,
            message_id=call.message.message_id,
            parse_mode="Markdown",
            reply_markup=back_keyboard(),
        )


# --- обработка ручного ввода марки/модели --- #
@bot.message_handler(func=lambda m: user_state.get(m.chat.id, {}).get("step") == "catalog_custom")
def handle_custom_car(message):
    chat_id = message.chat.id
    text_input = message.text.strip()

    user_state[chat_id] = {"step": "catalog_done_custom", "car": text_input}

    text = (
        f"✅ Принял: *{text_input}*.\n\n"
        "К сожалению, у нас пока нет компонентов для тюнинга вашего авто.\n\n"
        "Вы можете написать нашему менеджеру "
        "[Ивану](https://t.me/noisy_bmw_g20) и он обязательно вам поможет и подскажет!"
    )

    bot.send_message(
        chat_id,
        text,
        parse_mode="Markdown",
        reply_markup=back_keyboard(),  # одна кнопка: в главное меню
    )



if __name__ == "__main__":
    print("Bot started, polling...")
    bot.infinity_polling()
