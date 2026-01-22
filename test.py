import os
import telebot
import requests
from flask import Flask, request

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

def generate_text(prompt):
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": f"{prompt}\nВідповідай коротко, але в такому ж стилі, як і запит до цього речення. Мову відповіді обирай як у запиті."
                    }
                ]
            }
        ]
    }
    r = requests.post(
        f"{GEMINI_URL}?key={GEMINI_API_KEY}",
        json=payload,
        timeout=15
    )
    if r.status_code == 200:
        return r.json()["candidates"][0]["content"]["parts"][0]["text"]
    return "Помилка отримання відповіді від ІІ"

@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, "Привіт! Напиши будь-яке повідомлення")

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    reply = generate_text(message.text)
    bot.send_message(message.chat.id, reply)

@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def webhook():
    json_data = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_data)
    bot.process_new_updates([update])
    return "OK", 200

@app.route("/")
def index():
    return "Bot is running", 200

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(
        url=f"https://gemini-telegram-bot.onrender.com/{TELEGRAM_TOKEN}",
        allowed_updates=["message"]
    )
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
