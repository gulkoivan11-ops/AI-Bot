import os
import telebot
import requests
from flask import Flask, request
from threading import Thread

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
                        "text": f"{prompt}\nВідповідай коротко, але в такому ж стилі, як і запит. Мову відповіді обирай як у запиті."
                    }
                ]
            }
        ]
    }
    try:
        r = requests.post(f"{GEMINI_URL}?key={GEMINI_API_KEY}", json=payload, timeout=15)
        if r.status_code == 200:
            return r.json()["candidates"][0]["content"]["parts"][0]["text"]
        else:
            return f"Помилка Gemini API: {r.status_code}"
    except Exception as e:
        return f"Помилка з'єднання: {e}"

@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, "Привіт! Напиши будь-яке повідомлення")

def reply_gemini(message):
    reply = generate_text(message.text)
    bot.send_message(message.chat.id, reply)

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    Thread(target=reply_gemini, args=(message,)).start()

@app.route("/webhook", methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(request.json)
    bot.process_new_updates([update])
    return "", 200

@app.route("/")
def index():
    return "Bot is running", 200

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=f"https://gemini-telegram-bot.onrender.com/webhook")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
