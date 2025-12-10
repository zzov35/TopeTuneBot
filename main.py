from config import bot
import handlers  # просто импортируем, чтобы зарегистрировать хендлеры


if __name__ == "__main__":
    print("Bot started, polling...")
    bot.infinity_polling()
