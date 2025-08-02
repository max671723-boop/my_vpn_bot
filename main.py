from flask import Flask, request, render_template_string, abort import os import requests

app = Flask(name)

BOT_TOKEN = "8067456175:AAFsowei6yZZsEExG6jZWBYxE1KQ_dBcZ3I" API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}" ADMIN_ID = 7210975276 SUPPORT_USERNAME = "@vpn_seller_support"  # یوزرنیم پشتیبانی

orders = []

def send_message(chat_id, text, reply_markup=None): url = f"{API_URL}/sendMessage" payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"} if reply_markup: payload["reply_markup"] = reply_markup requests.post(url, json=payload)

def answer_callback(query_id, text): url = f"{API_URL}/answerCallbackQuery" requests.post(url, json={"callback_query_id": query_id, "text": text})

@app.route(f"/{BOT_TOKEN}", methods=["POST"]) def webhook(): update = request.get_json()

if "message" in update:
    message = update["message"]
    chat_id = message["chat"]["id"]
    user_id = message["from"]["id"]
    username = message["from"].get("username", "ندارد")
    text = message.get("text", "")

    if text == "/start":
        keyboard = {
            "inline_keyboard": [
                [{"text": "🛒 ثبت سفارش جدید", "callback_data": "new_order"}],
                [{"text": "📋 سفارش‌های من", "callback_data": "my_orders"}],
                [{"text": "📞 پشتیبانی سریع", "callback_data": "support"}],
                [{"text": "ℹ️ راهنما", "callback_data": "help"}]
            ]
        }
        send_message(chat_id, "سلام! خوش آمدید. یکی از گزینه‌های زیر را انتخاب کنید:", reply_markup=keyboard)

    else:
        orders.append({
            "id": len(orders)+1,
            "user_id": user_id,
            "username": username,
            "text": text,
            "response": None
        })
        send_message(chat_id, "✅ سفارش شما ثبت شد و به ادمین ارسال گردید.")
        send_message(ADMIN_ID, f"📩 سفارش جدید از @{username} (ID: {user_id}):\n{text}")

elif "callback_query" in update:
    query = update["callback_query"]
    query_id = query["id"]
    data = query["data"]
    user_id = query["from"]["id"]
    chat_id = query["message"]["chat"]["id"]
    username = query["from"].get("username", "ندارد")

    answer_callback(query_id, "در حال پردازش...")

    if data == "new_order":
        send_message(chat_id, "✍️ لطفا متن سفارش خود را ارسال کنید.")
    elif data == "my_orders":
        user_orders = [o for o in orders if o["user_id"] == user_id]
        if not user_orders:
            send_message(chat_id, "📭 شما هنوز سفارشی ثبت نکرده‌اید.")
        else:
            result = ""
            for o in user_orders:
                result += f"\n🧾 سفارش #{o['id']}\n📝 {o['text']}\n📤 پاسخ: {o['response'] or 'در انتظار پاسخ'}\n"
            send_message(chat_id, result.strip())
    elif data == "support":
        send_message(chat_id, f"📞 برای پشتیبانی مستقیم با ما در تماس باشید:

{SUPPORT_USERNAME}") elif data == "help": send_message(chat_id, "ℹ️ برای ثبت سفارش، روی دکمه "ثبت سفارش جدید" کلیک کنید و مشخصات سرویس را وارد نمایید. در صورت نیاز به پیگیری، از دکمه "سفارش‌های من" استفاده نمایید.")

return "OK", 200

def check_admin(user_id): return user_id == ADMIN_ID

@app.route("/admin", methods=["GET"]) def admin_panel(): from flask import request user_id = request.args.get("user_id", type=int) if not check_admin(user_id): return abort(403, description="دسترسی فقط برای ادمین مجاز است.")

html = """
<h2>پنل ادمین - سفارش‌های ثبت‌شده</h2>
<table border="1" cellpadding="6" cellspacing="0">
    <tr><th>شماره</th><th>کاربر</th><th>متن سفارش</th></tr>
    {% for o in orders %}
    <tr>
        <td>#{{ o.id }}</td>
        <td>@{{ o.username }}<br>(<a href='https://t.me/{{ o.username }}' target='_blank'>باز کردن تلگرام</a>)</td>
        <td>{{ o.text }}</td>
    </tr>
    {% endfor %}
</table>
"""
return render_template_string(html, orders=orders)

if name == "main": port = int(os.environ.get("PORT", 5000)) app.run(host="0.0.0.0", port=port)

