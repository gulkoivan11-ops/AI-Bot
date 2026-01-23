import os
import requests
from flask import Flask, request
import telebot
from threading import Thread

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)

OPENAI_URL = "https://api.openai.com/v1/chat/completions"


def ask_gpt(chat_id, text):
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "gpt-4o-mini",
        "input": text
    }

    try:
        r = requests.post(
            "https://api.openai.com/v1/responses",
            json=payload,
            headers=headers,
            timeout=20
        )

        if r.status_code == 200:
            data = r.json()
            answer = data["output"][0]["content"][0]["text"]
        else:
            answer = f"OpenAI error {r.status_code}: {r.text}"

    except Exception as e:
        answer = f"Connection error: {e}"

    bot.send_message(chat_id, answer)

@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, "Привіт! Напиши будь-яке повідомлення 🙂")


@bot.message_handler(func=lambda m: True)
def handle_message(message):
    Thread(target=ask_gpt, args=(message.chat.id, message.text)).start()


@app.route("/webhook", methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(request.get_json())
    bot.process_new_updates([update])
    return "OK", 200


@app.route("/")
def index():
    return "Bot is running", 200


if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME')}/webhook")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

