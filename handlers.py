from config import bot, MANAGER_CHAT_ID
from keys import (
    main_menu_keyboard,
    back_keyboard,
    catalog_brand_keyboard,
    catalog_model_keyboard,
    admin_brands_keyboard,
    admin_models_keyboard,
    admin_models_multi_keyboard,
)
from state import user_state, support_threads
from db import (
    add_product_with_fitments,
    get_all_brands,
    get_models_for_brand_id,
    create_brand,
    create_model,
    get_brand_and_model_names,
    delete_product_by_id,
    get_products_for_brand_model,
)

# ================== /start ================== #

@bot.message_handler(commands=["start"])
def handle_start(message):
    chat_id = message.chat.id
    user_state.pop(chat_id, None)  # сброс состояния

    text = (
        "Привет! Я бот-помощник по тюнингу авто 🚗\n\n"
        "Я могу:\n"
        "• подобрать тюнинг под твою машину\n"
        "• показать, как это будет выглядеть (ИИ-визуализация)\n"
        "• передать твой запрос менеджеру\n\n"
        "Выбери, с чего начнём:"
    )
    bot.send_message(chat_id, text, reply_markup=main_menu_keyboard())


# ============ ОБРАБОТКА INLINE-КНОПОК ============ #

@bot.callback_query_handler(func=lambda call: True)
def handle_menu_callback(call):
    chat_id = call.message.chat.id
    data = call.data
    step = user_state.get(chat_id, {}).get("step")

    # Лог, чтобы видеть, что приходит от кнопок
    print(f"[CALLBACK] chat={chat_id}, data={data}")

    # ----- назад к выбору бренда (пользователь) ----- #
    if data == "back_brands":
        user_state[chat_id] = {"step": "catalog_brand"}
        text = "Выбери марку автомобиля:"
        bot.edit_message_text(
            text,
            chat_id=chat_id,
            message_id=call.message.message_id,
            reply_markup=catalog_brand_keyboard(),
        )
        return


    # ----- КАТАЛОГ (пользователь) ----- #
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

    # ----- выбор марки (пользователь) ----- #
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
        # ждём ручной ввод
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

    # ----- выбор модели (пользователь, одна модель) ----- #
    elif data.startswith("model_"):
        mapping = {
            "model_mercedes_cla": ("Mercedes", "CLA"),
            "model_mercedes_e": ("Mercedes", "E-Class"),
            "model_mercedes_c": ("Mercedes", "C-Class"),
            "model_bmw_3": ("BMW", "3 Series"),
            "model_bmw_4": ("BMW", "4 Series"),
            "model_bmw_5": ("BMW", "5 Series"),
        }

        if data not in mapping:
            bot.answer_callback_query(call.id, "Неизвестная модель.", show_alert=True)
            return

        brand, model = mapping[data]
        user_state[chat_id] = {"step": "catalog_done", "brand": brand, "model": model}

        # достаём товары из БД
        products = get_products_for_brand_model(brand, model)

        # --- если товаров нет --- #
        if not products:
            text = (
                f"Ты выбрал: *{brand} {model}*.\n\n"
                "К сожалению, у нас пока нет компонентов для тюнинга этой модели.\n\n"
                "Вы можете написать нашему менеджеру, и он постарается подобрать варианты."
            )
            bot.edit_message_text(
                text,
                chat_id=chat_id,
                message_id=call.message.message_id,
                parse_mode="Markdown",
                reply_markup=back_keyboard(),
            )

        # --- если товары есть --- #
        else:
            header = (
                f"✅ Ты выбрал: *{brand} {model}*.\n\n"
                f"Вот что у нас есть для этой модели (всего {len(products)} шт.):"
            )
            # здесь БЕЗ клавиатуры, просто редактируем текст выбора
            bot.edit_message_text(
                header,
                chat_id=chat_id,
                message_id=call.message.message_id,
                parse_mode="Markdown",
            )

            # отправляем каждый товар отдельным сообщением
            for p in products:
                name = getattr(p, "name", "Без названия")
                years = getattr(p, "years", None)
                desc = getattr(p, "description", None)
                photo_id = getattr(p, "photo_file_id", None)
                pid = getattr(p, "id", None)

                caption_lines = [f"*{name}*"]
                if years:
                    caption_lines.append(f"_Годы: {years}_")
                if desc:
                    caption_lines.append(desc)
                if pid is not None:
                    caption_lines.append(f"`id: {pid}`")

                caption = "\n".join(caption_lines)

                if photo_id:
                    bot.send_photo(
                        chat_id,
                        photo_id,
                        caption=caption,
                        parse_mode="Markdown",
                    )
                else:
                    bot.send_message(
                        chat_id,
                        caption,
                        parse_mode="Markdown",
                    )

            # финальное сообщение после каталога
            bot.send_message(
                chat_id,
                "Это все товары, подходящие к этой марке и модели.",
                reply_markup=back_keyboard(),
            )



    # ----- ГЛАВНОЕ МЕНЮ ----- #
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

    # ----- ПОДБОР ПО ФОТО (заглушка) ----- #
    elif data == "menu_photo":
        user_state[chat_id] = {"step": "photo_demo"}
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

    # ----- СВЯЗАТЬСЯ С МЕНЕДЖЕРОМ (пользователь) ----- #
    elif data == "menu_manager":
        user_state[chat_id] = {"step": "support"}
        text = (
            "Если у вас возникла проблема или вы не можете найти тюнинг на своё авто,\n"
            "просто напишите сюда ваш вопрос и прикрепите фото/видео.\n\n"
            "Бот перешлёт всё нашему менеджеру, и он ответит вам здесь.\n\n"
            "Когда закончите, можете вернуться в главное меню."
        )
        bot.edit_message_text(
            text,
            chat_id=chat_id,
            message_id=call.message.message_id,
            parse_mode="Markdown",
            reply_markup=back_keyboard(),
        )

    # ====== АДМИН: выбор марки для нового товара ====== #

    elif data == "admin_brand_add" and step == "add_product_brand":
        state = user_state[chat_id]
        state["step"] = "add_product_brand_add"
        user_state[chat_id] = state
        bot.edit_message_text(
            "Введите название новой марки:",
            chat_id=chat_id,
            message_id=call.message.message_id,
        )

    elif data.startswith("admin_brand_") and step == "add_product_brand":
        brand_id = int(data.split("_")[-1])
        state = user_state[chat_id]
        state["brand_id"] = brand_id
        state["step"] = "add_product_model"
        user_state[chat_id] = state

        models = get_models_for_brand_id(brand_id)
        text = "Выберите модель для этой марки:"
        bot.edit_message_text(
            text,
            chat_id=chat_id,
            message_id=call.message.message_id,
            reply_markup=admin_models_keyboard(models),
        )

    # ====== АДМИН: выбор модели (одна или несколько) ====== #

    elif data == "admin_models_multi" and step == "add_product_model":
        # включаем режим мультивыбора
        state = user_state[chat_id]
        state["step"] = "add_product_models_multi"
        state["model_ids"] = []
        user_state[chat_id] = state

        brand_id = state["brand_id"]
        models = get_models_for_brand_id(brand_id)
        bot.edit_message_text(
            "Режим выбора нескольких моделей.\n"
            "Нажимайте на модели, чтобы добавить/убрать их из выбора.\n"
            "Когда закончите — нажмите «✅ Готово, перейти дальше».",
            chat_id=chat_id,
            message_id=call.message.message_id,
            reply_markup=admin_models_multi_keyboard(models, []),
        )

    elif data.startswith("admin_model_") and step == "add_product_model":
        # одиночный выбор модели
        model_id = int(data.split("_")[-1])
        state = user_state[chat_id]
        state["model_ids"] = [model_id]
        state["step"] = "add_product_years"
        user_state[chat_id] = state

        bot.edit_message_text(
            "Введите годы выпуска авто, для которых подходит товар "
            "(например: `2018–2020` или `с 2017 года`):",
            chat_id=chat_id,
            message_id=call.message.message_id,
            parse_mode="Markdown",
        )

    elif data.startswith("admin_model_") and step == "add_product_models_multi":
        # мультивыбор: переключаем модель в списке
        model_id = int(data.split("_")[-1])
        state = user_state[chat_id]
        selected = state.get("model_ids", [])
        if model_id in selected:
            selected.remove(model_id)
        else:
            selected.append(model_id)
        state["model_ids"] = selected
        user_state[chat_id] = state

        brand_id = state["brand_id"]
        models = get_models_for_brand_id(brand_id)

        # текст с перечнем выбранных моделей
        if selected:
            model_names = []
            for m in models:
                if m.id in selected:
                    model_names.append(m.name)
            selected_text = ", ".join(model_names)
        else:
            selected_text = "пока ничего не выбрано"

        bot.edit_message_text(
            f"Выбор нескольких моделей.\n\nТекущий выбор: *{selected_text}*.\n\n"
            "Нажимайте на модели, чтобы добавить/убрать их из выбора.\n"
            "Когда закончите — нажмите «✅ Готово, перейти дальше».",
            chat_id=chat_id,
            message_id=call.message.message_id,
            parse_mode="Markdown",
            reply_markup=admin_models_multi_keyboard(models, selected),
        )

    elif data == "admin_models_done" and step == "add_product_models_multi":
        state = user_state[chat_id]
        selected = state.get("model_ids", [])
        if not selected:
            bot.answer_callback_query(
                call.id,
                "Нужно выбрать хотя бы одну модель.",
                show_alert=True,
            )
            return

        state["step"] = "add_product_years"
        user_state[chat_id] = state

        bot.edit_message_text(
            "Введите годы выпуска авто, для которых подходит товар "
            "(например: `2018–2020` или `с 2017 года`):",
            chat_id=chat_id,
            message_id=call.message.message_id,
            parse_mode="Markdown",
        )

    bot.answer_callback_query(call.id)


# ============ КАТАЛОГ: ручной ввод марки/модели ============ #

@bot.message_handler(func=lambda m: user_state.get(m.chat.id, {}).get("step") == "catalog_custom")
def handle_custom_car(message):
    chat_id = message.chat.id
    text_input = message.text.strip()

    user_state[chat_id] = {"step": "catalog_done_custom", "car": text_input}

    text = (
        f"✅ Принял: *{text_input}*.\n\n"
        "К сожалению, у нас пока нет компонентов для тюнинга вашего авто.\n\n"
        "Вы можете написать нашему менеджеру — он обязательно вам поможет и подскажет!"
    )

    bot.send_message(
        chat_id,
        text,
        parse_mode="Markdown",
        reply_markup=back_keyboard(),
    )


# ============ ПОДДЕРЖКА: пользователь → менеджеру ============ #

@bot.message_handler(func=lambda m: user_state.get(m.chat.id, {}).get("step") == "support")
def handle_support_message(message):
    chat_id = message.chat.id

    if MANAGER_CHAT_ID == 0:
        bot.send_message(
            chat_id,
            "Сервис обратной связи ещё не настроен. Попробуйте позже 🙏",
            reply_markup=back_keyboard(),
        )
        return

    state = user_state.get(chat_id, {})
    if not state.get("notified_manager"):
        user_state[chat_id]["notified_manager"] = True

        username = message.from_user.username or "нет username"
        name_parts = [
            message.from_user.first_name or "",
            message.from_user.last_name or "",
        ]
        name = " ".join(p for p in name_parts if p).strip() or "нет имени"

        header = (
            "📩 *Новый запрос от пользователя*\n\n"
            f"id: `{chat_id}`\n"
            f"username: @{username}\n"
            f"имя: {name}\n\n"
            "Ответьте *reply* на любое из пересланных сообщений, "
            "и бот отправит ваш ответ пользователю."
        )
        bot.send_message(MANAGER_CHAT_ID, header, parse_mode="Markdown")

    forwarded = bot.forward_message(MANAGER_CHAT_ID, chat_id, message.message_id)
    support_threads[forwarded.message_id] = chat_id

    if not state.get("informed_user"):
        user_state[chat_id]["informed_user"] = True
        bot.send_message(
            chat_id,
            "Ваше сообщение отправлено менеджеру. "
            "Ответ придёт сюда в этот чат 👌",
        )


# ============ ПОДДЕРЖКА: ответ менеджера пользователю ============ #

@bot.message_handler(func=lambda m: m.chat.id == MANAGER_CHAT_ID and m.reply_to_message is not None)
def handle_manager_reply(message):
    original_chat_id = support_threads.get(message.reply_to_message.message_id)
    if not original_chat_id:
        return

    bot.copy_message(
        original_chat_id,
        from_chat_id=MANAGER_CHAT_ID,
        message_id=message.message_id,
    )


# ============ АДМИН: удаление товара по ID ============ #

@bot.message_handler(commands=["delete_product"])
def handle_delete_product_command(message):
    chat_id = message.chat.id
    if chat_id != MANAGER_CHAT_ID:
        bot.reply_to(message, "Эта команда доступна только менеджеру.")
        return

    user_state[chat_id] = {"step": "delete_product_id"}
    bot.reply_to(
        message,
        "🗑 Удаление товара.\n\n"
        "Введите *ID товара*, который хотите удалить.\n"
        "ID можно посмотреть в сообщении после добавления товара (строка `id в базе: ...`).",
        parse_mode="Markdown",
    )


@bot.message_handler(func=lambda m: user_state.get(m.chat.id, {}).get("step") == "delete_product_id")
def admin_delete_product_by_id_handler(message):
    chat_id = message.chat.id
    text = message.text.strip()

    try:
        product_id = int(text)
    except ValueError:
        bot.reply_to(message, "ID должен быть числом. Введите ещё раз.")
        return

    ok = delete_product_by_id(product_id)
    user_state.pop(chat_id, None)

    if ok:
        bot.reply_to(
            message,
            f"✅ Товар с id `{product_id}` удалён из базы.",
            parse_mode="Markdown",
        )
    else:
        bot.reply_to(
            message,
            f"⚠ Товар с id `{product_id}` не найден.",
            parse_mode="Markdown",
        )


# ============ АДМИН: добавление товара (мастер) ============ #

@bot.message_handler(commands=["add_product"])
def handle_add_product_command(message):
    chat_id = message.chat.id
    if chat_id != MANAGER_CHAT_ID:
        bot.reply_to(message, "Эта команда доступна только менеджеру.")
        return

    user_state[chat_id] = {"step": "add_product_name"}
    bot.reply_to(
        message,
        "🆕 Добавление товара.\n\nВведите *название* товара:",
        parse_mode="Markdown",
    )


# --- шаг 1: название --- #
@bot.message_handler(func=lambda m: user_state.get(m.chat.id, {}).get("step") == "add_product_name")
def admin_add_product_name(message):
    chat_id = message.chat.id
    name = message.text.strip()

    if not name:
        bot.reply_to(message, "Название не может быть пустым. Введите ещё раз.")
        return

    state = {
        "step": "add_product_brand",
        "name": name,
    }
    user_state[chat_id] = state

    brands = get_all_brands()
    bot.reply_to(
        message,
        f"Название: *{name}*\n\nТеперь выберите марку или добавьте новую:",
        parse_mode="Markdown",
        reply_markup=admin_brands_keyboard(brands),
    )


# --- шаг 2а: ввод новой марки --- #
@bot.message_handler(func=lambda m: user_state.get(m.chat.id, {}).get("step") == "add_product_brand_add")
def admin_add_product_brand_add(message):
    chat_id = message.chat.id
    brand_name = message.text.strip()
    if not brand_name:
        bot.reply_to(message, "Марка не может быть пустой. Введите ещё раз.")
        return

    brand_id = create_brand(brand_name)

    state = user_state.get(chat_id, {})
    state["brand_id"] = brand_id
    state["step"] = "add_product_model"
    user_state[chat_id] = state

    models = get_models_for_brand_id(brand_id)
    bot.reply_to(
        message,
        f"Марка *{brand_name}* добавлена.\nТеперь выберите модель или включите режим нескольких моделей:",
        parse_mode="Markdown",
        reply_markup=admin_models_keyboard(models),
    )


# --- шаг 2б: ввод новой модели (через текст) --- #
@bot.message_handler(func=lambda m: user_state.get(m.chat.id, {}).get("step") == "add_product_model_add")
def admin_add_product_model_add(message):
    chat_id = message.chat.id
    model_name = message.text.strip()
    if not model_name:
        bot.reply_to(message, "Модель не может быть пустой. Введите ещё раз.")
        return

    state = user_state.get(chat_id, {})
    brand_id = state.get("brand_id")
    if not brand_id:
        bot.reply_to(message, "Что-то пошло не так: не найдена марка. Начните /add_product заново.")
        user_state.pop(chat_id, None)
        return

    model_id = create_model(brand_id, model_name)

    state["model_ids"] = [model_id]
    state["step"] = "add_product_years"
    user_state[chat_id] = state

    bot.reply_to(
        message,
        f"Модель *{model_name}* добавлена.\n"
        "Теперь введите годы выпуска авто, для которых подходит товар "
        "(например: `2018–2020` или `с 2017 года`):",
        parse_mode="Markdown",
    )


# --- шаг 3: годы --- #
@bot.message_handler(func=lambda m: user_state.get(m.chat.id, {}).get("step") == "add_product_years")
def admin_add_product_years(message):
    chat_id = message.chat.id
    years = message.text.strip()
    if not years:
        bot.reply_to(message, "Строка с годами не может быть пустой. Введите ещё раз.")
        return

    state = user_state.get(chat_id, {})
    state["years"] = years
    state["step"] = "add_product_description"
    user_state[chat_id] = state

    bot.reply_to(
        message,
        "Окей 👍\nТеперь введите *описание товара*.\n\n"
        "Например: `Комплект обвеса AMG-style, бампер, пороги, диффузор`.\n\n"
        "Если не хотите добавлять описание — напишите `-`.",
        parse_mode="Markdown",
    )


# --- шаг 4: описание --- #
@bot.message_handler(func=lambda m: user_state.get(m.chat.id, {}).get("step") == "add_product_description")
def admin_add_product_description(message):
    chat_id = message.chat.id
    desc = message.text.strip()

    if desc == "-":
        desc = None

    state = user_state.get(chat_id, {})
    state["description"] = desc
    state["step"] = "add_product_photo"
    user_state[chat_id] = state

    bot.reply_to(
        message,
        "Описание сохранено.\nТеперь отправьте *фото товара* одним сообщением "
        "(как обычное фото, не как файл).",
        parse_mode="Markdown",
    )


# --- шаг 5: фото --- #
@bot.message_handler(
    content_types=["photo"],
    func=lambda m: user_state.get(m.chat.id, {}).get("step") == "add_product_photo",
)
def admin_add_product_photo(message):
    chat_id = message.chat.id
    state = user_state.get(chat_id)
    if not state:
        return

    photo = message.photo[-1]
    file_id = photo.file_id

    name = state["name"]
    brand_id = state["brand_id"]
    model_ids = state["model_ids"]
    years = state.get("years")
    description = state.get("description")

    model_names = []
    brand_name = None
    for mid in model_ids:
        bname, mname = get_brand_and_model_names(brand_id, mid)
        if not bname or not mname:
            continue
        brand_name = bname
        model_names.append(mname)

    if not brand_name or not model_names:
        bot.reply_to(
            message,
            "Не удалось получить марку/модели. Попробуйте ещё раз с /add_product.",
        )
        user_state.pop(chat_id, None)
        return

    product_id = add_product_with_fitments(
        name=name,
        brand_name=brand_name,
        model_names=model_names,
        photo_file_id=file_id,
        years=years,
        description=description,
    )

    user_state.pop(chat_id, None)

    extra_desc = f"\nОписание: {description}" if description else ""

    bot.reply_to(
        message,
        f"✅ Товар *{name}* добавлен в каталог.\n"
        f"Марка: *{brand_name}*\n"
        f"Модели: {', '.join(model_names)}\n"
        f"Годы: {years}\n"
        f"id в базе: `{product_id}`"
        f"{extra_desc}",
        parse_mode="Markdown",
    )
