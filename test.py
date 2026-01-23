import os
import requests
from flask import Flask, request
import telebot

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# 🔹 Хранилище контекста
# chat_id -> list of messages
dialog_context = {}

MAX_MESSAGES = 10  # сколько последних сообщений хранить (user+assistant)


def ask_groq(chat_id, text):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    # если диалога ещё нет — создаём
    if chat_id not in dialog_context:
        dialog_context[chat_id] = [
            {
                "role": "system",
                "content": "Ти розумний, дружній асистент. Відповідай чітко, логічно і по суті."
            }
        ]

    # добавляем сообщение пользователя
    dialog_context[chat_id].append({
        "role": "user",
        "content": text
    })

    # обрезаем старые сообщения
    if len(dialog_context[chat_id]) > MAX_MESSAGES * 2:
        dialog_context[chat_id] = dialog_context[chat_id][-MAX_MESSAGES * 2 :]

    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": dialog_context[chat_id],
        "temperature": 0.7
    }

    try:
        r = requests.post(GROQ_URL, json=payload, headers=headers, timeout=25)

        if r.status_code == 200:
            answer = r.json()["choices"][0]["message"]["content"]

            # сохраняем ответ ассистента в контекст
            dialog_context[chat_id].append({
                "role": "assistant",
                "content": answer
            })
        else:
            answer = f"Groq error {r.status_code}: {r.text}"

    except Exception as e:
        answer = f"Connection error: {e}"

    bot.send_message(chat_id, answer)


@bot.message_handler(commands=["start"])
def start(message):
    dialog_context.pop(message.chat.id, None)  # сброс контекста
    bot.send_message(
        message.chat.id,
        "Привіт! Я бот на LLaMA-3 70B 🧠\n"
        "Я памʼятаю контекст розмови. Просто пиши 🙂"
    )


@bot.message_handler(commands=["reset"])
def reset(message):
    dialog_context.pop(message.chat.id, None)
    bot.send_message(message.chat.id, "Контекст очищено 🔄")


@bot.message_handler(func=lambda m: True)
def handle_message(message):
    ask_groq(message.chat.id, message.text)


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
    bot.set_webhook(
        url=f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME')}/webhook"
    )
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))


