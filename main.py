from flask import Flask, request, render_template_string, abort
import os
import requests

app = Flask(__name__)

BOT_TOKEN = "8067456175:AAFsowei6yZZsEExG6jZWBYxE1KQ_dBcZ3I"
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
ADMIN_ID = 7210975276  # آیدی عددی ادمین

# آدرس وب‌هوک سرور (لینک رندر یا هر جای دیگه)
WEBHOOK_URL = f"https://my-vpn-bot-1-m1vj.onrender.com/{BOT_TOKEN}"

orders = []

def set_webhook():
    url = f"{API_URL}/setWebhook"
    params = {"url": WEBHOOK_URL}
    res = requests.get(url, params=params)
    if res.status_code == 200:
        print("Webhook set successfully.")
    else:
        print(f"Failed to set webhook: {res.text}")

def send_message(chat_id, text):
    url = f"{API_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    resp = requests.post(url, json=payload)
    return resp.json()

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = request.get_json()

    if "message" in update:
        msg = update["message"]
        user_id = msg["from"]["id"]
        username = msg["from"].get("username", "ندارد")
        chat_id = msg["chat"]["id"]
        text = msg.get("text", "").strip()

        if text == "/start":
            send_message(chat_id, "سلام! ربات پنل همکاری VPN آماده است. لطفا سفارش یا پیام خود را ارسال کنید.")
        else:
            order_id = len(orders) + 1
            orders.append({
                "id": order_id,
                "user_id": user_id,
                "username": username,
                "text": text,
                "response": None
            })
            send_message(ADMIN_ID, f"سفارش جدید #{order_id} از @{username} (ID: {user_id}):\n{text}")
            send_message(chat_id, f"سفارش شما ثبت شد با شماره: #{order_id}\nمنتظر پاسخ ادمین باشید.")

    return "OK", 200

def check_admin(user_id):
    return user_id == ADMIN_ID

@app.route("/admin", methods=["GET", "POST"])
def admin_panel():
    user_id = request.args.get("user_id", type=int)
    if not check_admin(user_id):
        return abort(403, description="دسترسی فقط برای ادمین مجاز است.")

    msg = ""
    if request.method == "POST":
        order_id = int(request.form.get("order_id", -1))
        response_text = request.form.get("response_text", "").strip()
        if order_id > 0 and response_text:
            order = next((o for o in orders if o["id"] == order_id), None)
            if order:
                order["response"] = response_text
                send_message(order["user_id"], f"پاسخ ادمین به سفارش #{order_id}:\n{response_text}")
                msg = "پاسخ ارسال شد."
            else:
                msg = "سفارش یافت نشد."

    html = """
    <h2>پنل ادمین - سفارش‌ها و پیام‌های همکاران</h2>
    <p style="color:green;">{{ msg }}</p>
    <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse;">
        <tr>
            <th>شماره سفارش</th>
            <th>کاربر (username)</th>
            <th>متن سفارش</th>
            <th>پاسخ</th>
            <th>ارسال پاسخ</th>
        </tr>
        {% for order in orders %}
        <tr>
            <td>{{ order.id }}</td>
            <td>@{{ order.username }} ({{ order.user_id }})</td>
            <td>{{ order.text }}</td>
            <td>{{ order.response or "بدون پاسخ" }}</td>
            <td>
            {% if not order.response %}
                <form method="post" style="margin:0;">
                    <input type="hidden" name="order_id" value="{{ order.id }}">
                    <textarea name="response_text" rows="2" cols="30" placeholder="جواب را اینجا بنویس..." required></textarea><br>
                    <button type="submit">ارسال پاسخ</button>
                </form>
            {% else %}
                ---
            {% endif %}
            </td>
        </tr>
        {% endfor %}
    </table>
    """

    return render_template_string(html, orders=orders, msg=msg)

if __name__ == "__main__":
    set_webhook()  # ست کردن خودکار وب‌هوک هنگام استارت برنامه
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
