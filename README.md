Бот # 🚗 TopTune Bot — AI-Powered Car Tuning Assistant

Telegram-бот для автоматизированного подбора тюнинг-запчастей с использованием компьютерного зрения (Vision AI) и реляционной базы данных.  
Проект разработан в рамках курсовой работы по направлению «Управление в технических системах» (РУДН).

## 📖 Описание
Система решает проблему сложного подбора совместимых автозапчастей. Пользователь может отправить фото автомобиля, чтобы ИИ определил модель, либо выбрать авто вручную из каталога. Бот проверяет совместимость деталей через БД и позволяет связаться с менеджером.

**Ключевые функции:**
- 📸 **Распознавание авто:** Интеграция с Vision-моделью (HuggingFace Transformers) для классификации марки и модели по фото.
- 🗄 **База данных:** SQLAlchemy (SQLite) с нормализованной схемой (Бренды, Модели, Товары, Совместимость).
- 🛠 **Админ-панель:** CRUD-операции для менеджеров (добавление товаров, фото, управление каталогом) прямо через Telegram.
- 💬 **Поддержка:** Система тикетов (пересылка сообщений между пользователем и менеджером).
- 🔄 **FSM (Finite State Machine):** Пошаговая логика диалогов (состояния пользователя хранятся в памяти).

## 🛠 Технологический стек

| Категория | Технологии |
| :--- | :--- |
| **Язык** | Python 3.9+ |
| **Bot Framework** | pyTelegramBotAPI (telebot) |
| **AI / ML** | Transformers, PyTorch, PIL, AutoModelForImageClassification |
| **Database** | SQLAlchemy (ORM), SQLite |
| **Config** | python-dotenv |
| **Architecture** | Modular (Handlers, DB, Services, AI) |

## 🏗 Архитектура
Проект следует трёхуровневой архитектуре (согласно документации проекта):
1. **Presentation Layer:** Telegram Bot API (`handlers.py`, `keys.py`).
2. **Business Logic:** Обработчики команд, управление состояниями (`state.py`), логика подбора.
3. **Data & AI Layer:** SQLAlchemy ORM модели (`db.py`), Vision AI модуль (`vision_ai.py`).

## 🚀 Быстрый старт

### Требования
- Python 3.9+
- Telegram Bot Token
- Файлы модели (папка `./car_model` или настройка API)

### Установка
1. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/zzov35/TopTuneBot.git
   cd TopTuneBot
2. Создайте виртуальное окружение и установите зависимости:
  python -m venv venv
  source venv/bin/activate  # Windows: venv\Scripts\activate
  pip install -r requirements.txt
3. Настройте переменные окружения (создайте .env):
  BOT_TOKEN=your_telegram_bot_token
  MANAGER_CHAT_ID=your_chat_id
4. Инициализируйте базу данных и запустите бота:
  python db.py  # Создание таблиц и демо-данных
  python main.py

Структура базы данных

Используется реляционная модель (SQLAlchemy):
  Brand: Марки автомобилей.
  CarModel: Модели автомобилей (связь с Brand).
  Product: Товары (название, описание, фото, цена).
  ProductFitment: Таблица совместимости (связь Product ↔ CarModel).

Демонстрация:
