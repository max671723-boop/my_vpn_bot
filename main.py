from flask import Flask, request
import requests
import os
from datetime import datetime
import pytz

TOKEN = "8067456175:AAFsowei6yZZsEExG6jZWBYxE1KQ_dBcZ3I"
ADMIN_ID = 7210975276

app = Flask(__name__)
API = f"https://api.telegram.org/bot{TOKEN}"

VOLUMES = {
    "20 گیگ یک ماهه 🟢": "20GB",
    "30 گیگ یک ماهه 🔵": "30GB",
    "40 گیگ یک ماهه 🟣": "40GB",
    "50 گیگ یک ماهه 🔴": "50GB",
    "نامحدود یک ماهه ⚫": "Unlimited"
}

pending_orders = {}
invoices = {}

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
    user_id = message["from"]["id"]
    first_name = message["from"].get("first_name", "")

    if text == "/start":
        keyboard = {
            "inline_keyboard": [[{"text": name, "callback_data": vol}] for name, vol in VOLUMES.items()]
        }
        requests.post(f"{API}/sendMessage", json={
            "chat_id": chat_id,
            "text": f"سلام {first_name} 👋\n\nبرای ثبت سفارش، یکی از حجم‌های زیر رو انتخاب کن:",
            "reply_markup": keyboard
        })

    elif user_id in pending_orders:
        order = pending_orders.pop(user_id)
        service_name = text.strip()

        # تاریخ و فاکتور
        tehran = pytz.timezone('Asia/Tehran')
        date_str = datetime.now(tehran).strftime('%Y/%m/%d')
        invoice_id = f"INV-{datetime.now(tehran).strftime('%Y%m%d%H%M%S')}"

        # ذخیره برای دکمه بعدی
        invoices[invoice_id] = {
            "user_id": user_id,
            "chat_id": chat_id,
            "service_name": service_name
        }

        # به کاربر
        requests.post(f"{API}/sendMessage", json={
            "chat_id": chat_id,
            "text": f"✅ سفارش شما با موفقیت ثبت شد.\n\n📝 نام سرویس: {service_name}\n💾 حجم: {order['volume']}\n📅 تاریخ ثبت: {date_str}\n🧾 شماره فاکتور: `{invoice_id}`",
            "parse_mode": "Markdown"
        })

        # به ادمین با دکمه
        admin_btn = {
            "inline_keyboard": [[
                {"text": "✅ سفارش انجام شد", "callback_data": f"done_{invoice_id}"}
            ]]
        }

        requests.post(f"{API}/sendMessage", json={
            "chat_id": ADMIN_ID,
            "text": f"📥 سفارش جدید:\n👤 نام: {order['name']}\n🔗 یوزرنیم: @{order['username']}\n💾 حجم: {order['volume']}\n📝 سرویس: {service_name}\n📅 تاریخ: {date_str}\n🧾 فاکتور: {invoice_id}",
            "reply_markup": admin_btn
        })

def handle_callback(callback):
    data = callback["data"]
    chat_id = callback["message"]["chat"]["id"]

    if data.startswith("done_"):
        invoice_id = data.split("_")[1]
        if invoice_id in invoices:
            user_info = invoices.pop(invoice_id)
            # به کاربر پیام بده
            requests.post(f"{API}/sendMessage", json={
                "chat_id": user_info["chat_id"],
                "text": f"✅ سفارش شما با شماره فاکتور `{invoice_id}` توسط ادمین تأیید و انجام شد.\nسپاس از اعتمادتون 🙏",
                "parse_mode": "Markdown"
            })
            # به ادمین هم پیام بده
            requests.post(f"{API}/sendMessage", json={
                "chat_id": chat_id,
                "text": f"📦 سفارش با شماره فاکتور `{invoice_id}` به کاربر ارسال شد.",
                "parse_mode": "Markdown"
            })
        return

    # سفارش حجم
    user_id = callback["from"]["id"]
    volume = data
    username = callback["from"].get("username", "ندارد")
    name = callback["from"].get("first_name", "ندارد")

    pending_orders[user_id] = {
        "chat_id": chat_id,
        "volume": volume,
        "username": username,
        "name": name
    }

    requests.post(f"{API}/sendMessage", json={
        "chat_id": chat_id,
        "text": "✍️ لطفاً نام دلخواه سرویس را وارد کنید:"
    })

@app.route("/")
def index():
    return "Bot is running!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
