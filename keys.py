from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


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
    """Выбор марки авто (для пользователя)."""
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🚗 Mercedes", callback_data="brand_mercedes"))
    markup.row(InlineKeyboardButton("🚗 BMW", callback_data="brand_bmw"))
    markup.row(InlineKeyboardButton("✏️ Другая марка", callback_data="brand_other"))
    markup.row(InlineKeyboardButton("⬅️ В главное меню", callback_data="back_main"))
    return markup


from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def catalog_model_keyboard(brand_name: str):
    kb = InlineKeyboardMarkup()

    if brand_name == "Mercedes":
        kb.add(InlineKeyboardButton("CLA",      callback_data="model_mercedes_cla"))
        kb.add(InlineKeyboardButton("E-Class",  callback_data="model_mercedes_e"))
        kb.add(InlineKeyboardButton("C-Class",  callback_data="model_mercedes_c"))

    elif brand_name == "BMW":
        kb.add(InlineKeyboardButton("3 Series", callback_data="model_bmw_3"))
        kb.add(InlineKeyboardButton("4 Series", callback_data="model_bmw_4"))
        kb.add(InlineKeyboardButton("5 Series", callback_data="model_bmw_5"))

    # ВАЖНО: вот здесь строго back_brands
    kb.add(InlineKeyboardButton("⬅ Выбрать другую марку", callback_data="back_brands"))
    kb.add(InlineKeyboardButton("⬅ В главное меню",       callback_data="back_main"))

    return kb


# ---------- АДМИНСКИЕ КЛАВИАТУРЫ ----------

def admin_brands_keyboard(brands) -> InlineKeyboardMarkup:
    """Клавиатура выбора марки при добавлении товара (для менеджера)."""
    markup = InlineKeyboardMarkup()
    for brand in brands:
        markup.row(
            InlineKeyboardButton(
                f"🚗 {brand.name}",
                callback_data=f"admin_brand_{brand.id}",
            )
        )

    markup.row(InlineKeyboardButton("➕ Добавить марку", callback_data="admin_brand_add"))
    markup.row(InlineKeyboardButton("⬅️ В главное меню", callback_data="back_main"))
    return markup


def admin_models_keyboard(models) -> InlineKeyboardMarkup:
    """Клавиатура выбора модели (одна или несколько)."""
    markup = InlineKeyboardMarkup()

    for model in models:
        markup.row(
            InlineKeyboardButton(
                model.name,
                callback_data=f"admin_model_{model.id}",
            )
        )

    # новая кнопка — включить режим выбора нескольких моделей
    markup.row(
        InlineKeyboardButton(
            "☑ Подходит для нескольких моделей",
            callback_data="admin_models_multi",
        )
    )

    markup.row(InlineKeyboardButton("➕ Добавить модель", callback_data="admin_model_add"))
    markup.row(InlineKeyboardButton("⬅️ В главное меню", callback_data="back_main"))
    return markup


def admin_models_multi_keyboard(models, selected_ids: list[int] | None = None) -> InlineKeyboardMarkup:
    """
    Клавиатура выбора нескольких моделей.
    Повторное нажатие можно использовать как «переключатель».
    """
    selected_ids = selected_ids or []
    markup = InlineKeyboardMarkup()

    for model in models:
        prefix = "✅ " if model.id in selected_ids else "▫ "
        markup.row(
            InlineKeyboardButton(
                f"{prefix}{model.name}",
                callback_data=f"admin_model_{model.id}",
            )
        )

    markup.row(
        InlineKeyboardButton(
            "✅ Готово, перейти дальше",
            callback_data="admin_models_done",
        )
    )
    markup.row(InlineKeyboardButton("⬅️ В главное меню", callback_data="back_main"))
    return markup
