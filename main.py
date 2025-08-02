from flask import Flask, request
import requests
import os

# تنظیمات
TOKEN = "8067456175:AAFsowei6yZZsEExG6jZWBYxE1KQ_dBcZ3I"
ADMIN_ID = 7210975276
API_URL = f"https://api.telegram.org/bot{TOKEN}/"
WEBHOOK_URL = "https://my-vpn-bot-1-m1vj.onrender.com"

# ساخت پوشه دیتا
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# ساخت اپ Flask
app = Flask(__name__)

# تابع ارسال پیام
def send_message(chat_id, text, keyboard=None):
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    if keyboard:
        payload["reply_markup"] = {"keyboard": keyboard, "resize_keyboard": True}
    requests.post(API_URL + "sendMessage", json=payload)

# تابع ذخیره مرحله کاربر
def save_step(user_id, step):
    with open(f"{DATA_DIR}/{user_id}-step.txt", "w") as f:
        f.write(step)

# تابع دریافت مرحله فعلی کاربر
def get_step(user_id):
    path = f"{DATA_DIR}/{user_id}-step.txt"
    return open(path).read() if os.path.exists(path) else "none"

# هندل درخواست‌ها (Webhook)
@app.route("/", methods=["POST"])
def webhook():
    update = request.get_json()
    if "message" not in update:
        return "ok"

    message = update["message"]
    text = message.get("text", "")
    chat_id = message["chat"]["id"]
    user_id = message["from"]["id"]
    message_id = message["message_id"]
    first_name = message["from"].get("first_name", "")

    step_file = f"{DATA_DIR}/{user_id}-step.txt"
    order_file = f"{DATA_DIR}/{user_id}-order.txt"

    # شروع ربات
    if text == "/start":
        save_step(user_id, "none")
        keyboard = [[{"text": "📝 ثبت سفارش"}, {"text": "📞 تماس با ادمین"}]]
        send_message(chat_id, f"سلام {first_name} 👋\nبه پنل همکاری فروش VPN خوش اومدی!\nاز دکمه‌های زیر استفاده کن:", keyboard)

    # مراحل سفارش
    elif text == "📝 ثبت سفارش":
        save_step(user_id, "order_name")
        send_message(chat_id, "🔸 لطفاً <b>نام مشتری</b> را وارد کن:")

    elif get_step(user_id) == "order_name":
        with open(order_file, "w") as f:
            f.write(f"👤 نام مشتری: {text}\n")
        save_step(user_id, "order_volume")
        send_message(chat_id, "🔸 حجم مورد نیاز را وارد کن (مثلاً ۳۰ گیگ):")

    elif get_step(user_id) == "order_volume":
        with open(order_file, "a") as f:
            f.write(f"📦 حجم: {text}\n")
        save_step(user_id, "order_time")
        send_message(chat_id, "🔸 مدت زمان سرویس را وارد کن (مثلاً ۱ ماهه):")

    elif get_step(user_id) == "order_time":
        with open(order_file, "a") as f:
            f.write(f"⏳ مدت زمان: {text}\n")
        with open(order_file, "r") as f:
            order_data = f.read()
        send_message(chat_id, "✅ سفارش ثبت شد و برای ادمین ارسال شد.")
        send_message(ADMIN_ID, f"📬 سفارش جدید از همکار:\n\n{order_data}\n🔝 آیدی عددی همکار: {user_id}")
        save_step(user_id, "none")

    elif text == "📞 تماس با ادمین":
        send_message(chat_id, "✉️ پیام‌تو بنویس و بفرست. من برای ادمین فوروارد می‌کنم.")

    # فوروارد پیام کاربر برای ادمین
    elif chat_id != ADMIN_ID:
        requests.post(API_URL + "forwardMessage", data={
            "chat_id": ADMIN_ID,
            "from_chat_id": chat_id,
            "message_id": message_id
        })
        send_message(chat_id, "📨 پیام شما برای ادمین فوروارد شد.")

    # ارسال پاسخ از ادمین با دستور /send
    elif text.startswith("/send") and chat_id == ADMIN_ID:
        parts = text.split(" ", 2)
        if len(parts) >= 3:
            target_id, reply_text = parts[1], parts[2]
            send_message(target_id, f"📬 پاسخ ادمین:\n{reply_text}")
            send_message(ADMIN_ID, f"✅ پیام برای کاربر {target_id} ارسال شد.")
        else:
            send_message(ADMIN_ID, "❗ فرمت اشتباه. مثال:\n/send 123456789 سلام، سرویس شما آماده‌ست.")

    return "ok"

# اجرای سرور در رندر
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
