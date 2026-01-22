import os
import requests
from flask import Flask, request
import telebot
from threading import Thread

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)

OPENAI_URL = "https://api.openai.com/v1/chat/completions"

# Генерация текста через GPT-3.5
def generate_text(prompt):
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 500,
        "temperature": 0.8
    }
    try:
        r = requests.post(OPENAI_URL, json=data, headers=headers, timeout=20)
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"]
        else:
            return f"Помилка OpenAI API: {r.status_code}"
    except Exception as e:
        return f"Помилка з'єднання: {e}"

# Отправка ответа в Telegram в отдельном потоке
def reply_gpt(chat_id, text):
    response = generate_text(text)
    bot.send_message(chat_id, response)

# Команда /start
@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, "Привіт! Напиши будь-яке повідомлення")

# Обработка всех сообщений через поток
@bot.message_handler(func=lambda m: True)
def handle_message(message):
    Thread(target=reply_gpt, args=(message.chat.id, message.text)).start()

# Webhook
@app.route("/webhook", methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(request.json)
    Thread(target=bot.process_new_updates, args=([update],)).start()
    return "", 200  # мгновенный ответ Telegram

# Проверка работы
@app.route("/")
def index():
    return "Bot is running", 200

if __name__ == "__main__":
    # Устанавливаем webhook на Render
    bot.remove_webhook()
    bot.set_webhook(url=f"https://your-render-domain.onrender.com/webhook")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
