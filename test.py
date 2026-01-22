import os
import telebot
import requests
from flask import Flask, request
from threading import Thread

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)

OPENAI_URL = "https://api.openai.com/v1/chat/completions"

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
        r = requests.post(OPENAI_URL, json=data, headers=headers, timeout=15)
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"]
        else:
            return f"Помилка OpenAI API: {r.status_code}"
    except Exception as e:
        return f"Помилка з'єднання: {e}"

@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, "Привіт! Напиши будь-яке повідомлення")

def reply_gpt(message):
    reply = generate_text(message.text)
    bot.send_message(message.chat.id, reply)

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    Thread(target=reply_gpt, args=(message,)).start()

@app.route("/webhook", methods=["POST"])
def webhook():
    if request.headers.get("content-type") == "application/json":
        update = telebot.types.Update.de_json(request.json)
        bot.process_new_updates([update])
    return "", 200

@app.route("/")
def index():
    return "Bot is running", 200

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=f"https://your-render-domain.onrender.com/webhook")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

