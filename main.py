from flask import Flask, request
import requests
import os
import json

TOKEN = "8067456175:AAFsowei6yZZsEExG6jZWBYxE1KQ_dBcZ3I"
ADMIN_ID = 7210975276

app = Flask(__name__)
API = f"https://api.telegram.org/bot{TOKEN}"

# لیست حجم‌ها
VOLUMES = {
    "20 گیگ یک ماهه 🟢": "20GB",
    "30 گیگ یک ماهه 🔵": "30GB",
    "40 گیگ یک ماهه 🟣": "40GB",
    "50 گیگ یک ماهه 🔴": "50GB",
    "نامحدود یک ماهه ⚫": "Unlimited"
}

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = request.get_json()
    if "message" in update:
        handle_message(update["message"])
    elif "callback_query" in update:
        handle_callback(update["callback_query"])
    return "ok"

def handle_message(message):
    chat_id = message["chat"]["id"]
    text = message.get("text", "")
    first_name = message["from"].get("first_name", "")

    if text == "/start":
        keyboard = {
            "inline_keyboard": [
                [{"text": name, "callback_data": vol}] for name, vol in VOLUMES.items()
            ]
        }
        requests.post(f"{API}/sendMessage", json={
            "chat_id": chat_id,
            "text": f"سلام {first_name} 👋\n\nبرای ثبت سفارش، یکی از حجم‌های زیر رو انتخاب کن:",
            "reply_markup": keyboard
        })

def handle_callback(callback):
    chat_id = callback["message"]["chat"]["id"]
    data = callback["data"]
    username = callback["from"].get("username", "ندارد")
    name = callback["from"].get("first_name", "ندارد")

    # ارسال پیام به همکار
    requests.post(f"{API}/sendMessage", json={
        "chat_id": chat_id,
        "text": f"✅ سفارش شما با حجم {data} ثبت شد.\n\n💬 لطفاً برای پرداخت با ادمین هماهنگ کنید.\n📬 منتظر دریافت کانفیگ در پیام خصوصی باشید."
    })

    # ارسال به ادمین
    requests.post(f"{API}/sendMessage", json={
        "chat_id": ADMIN_ID,
        "text": f"📥 سفارش جدید:\n👤 نام: {name}\n🔗 یوزرنیم: @{username}\n💾 حجم: {data}\n\n💡 لطفاً فایل کانفیگ را پس از هماهنگی ارسال کن."
    })

@app.route("/")
def index():
    return "Bot is running!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
