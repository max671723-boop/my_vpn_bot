import telebot
from flask import Flask, request
import json
import os
import random
import time

TOKEN = '8480626201:AAG9AzRxwdYboj5SNLeNcVtOrNOvlNY_vsM'
ADMIN_ID = 7210975276
WEBHOOK_URL = https://my-vpn-bot-gvob.onrender.com/8480626201:AAG9AzRxwdYboj5SNLeNcVtOrNOvlNY_vsM

bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)

DATA_FILE = 'data.json'

# Load data or initialize
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    user_data = data.get('user_data', {})
    name_to_chat_id = data.get('name_to_chat_id', {})
    orders_history = data.get('orders_history', {})
else:
    user_data = {}
    name_to_chat_id = {}
    orders_history = {}

admin_state = {}
PER_PAGE = 5

def save_data():
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump({
            'user_data': user_data,
            'name_to_chat_id': name_to_chat_id,
            'orders_history': orders_history
        }, f, ensure_ascii=False, indent=4)

@bot.message_handler(commands=['start'])
def start(message):
    if message.chat.id == ADMIN_ID:
        send_admin_panel(message.chat.id)
    else:
        bot.send_message(message.chat.id, "👋 خوش آمدید!\nلطفا یک گزینه انتخاب کنید:")
        markup = telebot.types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            telebot.types.InlineKeyboardButton("📦 ثبت سفارش", callback_data="order"),
            telebot.types.InlineKeyboardButton("📂 مشاهده سفارش‌های من", callback_data="my_orders"),
            telebot.types.InlineKeyboardButton("📤 ثبت سفارش وقتی ربات قطع بود", url="https://forms.gle/bXFYN6dj6nV4nqFh8")
        )
        bot.send_message(message.chat.id, "یک گزینه را انتخاب کنید:", reply_markup=markup)

def send_admin_panel(chat_id):
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        telebot.types.InlineKeyboardButton('📩 ارسال فاکتور', callback_data='admin_invoice'),
        telebot.types.InlineKeyboardButton('🔋 ارسال حجم باقی‌مانده', callback_data='admin_volume'),
        telebot.types.InlineKeyboardButton('📤 ارسال حجم با دستور /send', callback_data='admin_send_command'),
        telebot.types.InlineKeyboardButton('📚 مشاهده همه سفارش‌ها', callback_data='admin_show_orders')
    )
    bot.send_message(chat_id, "سلام ادمین! پنل مدیریت در پایین:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    chat_id = call.message.chat.id
    data = call.data

    # -- مشتری --
    if data == "order":
        markup = telebot.types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            telebot.types.InlineKeyboardButton("1️⃣ سرویس معمولی", callback_data="normal"),
            telebot.types.InlineKeyboardButton("2️⃣ سرویس نامحدود", callback_data="unlimited")
        )
        bot.edit_message_text("🔰 نوع سرویس را انتخاب کنید:", chat_id, call.message.message_id, reply_markup=markup)

    elif data == "normal":
        user_data[str(chat_id)] = {"service_type": "معمولی"}
        save_data()
        markup = telebot.types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            telebot.types.InlineKeyboardButton("20 گیگ", callback_data="20"),
            telebot.types.InlineKeyboardButton("30 گیگ", callback_data="30"),
            telebot.types.InlineKeyboardButton("40 گیگ", callback_data="40"),
            telebot.types.InlineKeyboardButton("50 گیگ", callback_data="50")
        )
        bot.edit_message_text("💾 حجم مورد نظر را انتخاب کنید:", chat_id, call.message.message_id, reply_markup=markup)

    elif data == "unlimited":
        user_data[str(chat_id)] = {"service_type": "نامحدود", "volume": "نامحدود"}
        save_data()
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("🕐 یک‌ماهه", callback_data="1month"))
        bot.edit_message_text("⏳ مدت زمان فقط یک‌ماهه است. ادامه دهید:", chat_id, call.message.message_id, reply_markup=markup)

    elif data in ["20", "30", "40", "50"]:
        user_data[str(chat_id)]["volume"] = data + " گیگ"
        save_data()
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("🕐 یک‌ماهه", callback_data="1month"))
        bot.edit_message_text("⏳ مدت زمان فقط یک‌ماهه است. ادامه دهید:", chat_id, call.message.message_id, reply_markup=markup)

    elif data == "1month":
        user_data[str(chat_id)]["duration"] = "1 ماهه"
        save_data()
        bot.edit_message_text("👤 لطفا نام و نام خانوادگی خود را وارد کنید:", chat_id, call.message.message_id)
        bot.register_next_step_handler_by_chat_id(chat_id, finish_order)

    elif data == "my_orders":
        chat_str = str(chat_id)
        user_orders = [order for name, order in orders_history.items() if name_to_chat_id.get(name) == chat_str]

        if not user_orders:
            bot.send_message(chat_id, "❌ سفارشی برای شما ثبت نشده است.")
        else:
            text = "📦 سفارش‌های شما:\n\n"
            for order in user_orders:
                text += (
                    f"📄 فاکتور: {order['invoice_id']}\n"
                    f"🔘 نوع سرویس: {order['service_type']}\n"
                    f"📦 حجم: {order['volume']}\n"
                    f"🕐 مدت: {order['duration']}\n"
                    f"👤 نام: {order['full_name']}\n\n"
                )
            bot.send_message(chat_id, text)

    # -- ادمین --
    elif chat_id == ADMIN_ID:
        if data == 'admin_invoice':
            bot.send_message(ADMIN_ID, "👤 لطفا نام کامل مشتری را وارد کنید تا فاکتور ارسال شود:")
            bot.register_next_step_handler_by_chat_id(ADMIN_ID, handle_invoice_name)

        elif data == 'admin_volume':
            bot.send_message(ADMIN_ID, "✏️ لطفا نام کامل مشتری را وارد کنید (مثلا: علی احمدی):")
            bot.register_next_step_handler_by_chat_id(ADMIN_ID, handle_send_volume)

        elif data == 'admin_send_command':
            bot.send_message(ADMIN_ID, "✏️ لطفا دستور را به شکل زیر وارد کنید:\n/send username حجم (مثلا: /send ali 5)")

        elif data == 'admin_show_orders':
            all_orders = list(orders_history.values())
            if not all_orders:
                bot.send_message(ADMIN_ID, "🚫 هیچ سفارشی ثبت نشده است.")
                return
            admin_state[ADMIN_ID] = {"page": 0, "orders": all_orders}
            show_orders_page(ADMIN_ID)

    # صفحه‌بندی سفارش‌ها (ادمین)
    elif data == "prev_orders":
        if chat_id != ADMIN_ID:
            bot.answer_callback_query(call.id, "شما دسترسی ندارید.")
            return
        admin_state[ADMIN_ID]["page"] = max(admin_state[ADMIN_ID]["page"] - 1, 0)
        show_orders_page(ADMIN_ID)
        bot.answer_callback_query(call.id)

    elif data == "next_orders":
        if chat_id != ADMIN_ID:
            bot.answer_callback_query(call.id, "شما دسترسی ندارید.")
            return
        max_page = (len(admin_state[ADMIN_ID]["orders"]) - 1) // PER_PAGE
        admin_state[ADMIN_ID]["page"] = min(admin_state[ADMIN_ID]["page"] + 1, max_page)
        show_orders_page(ADMIN_ID)
        bot.answer_callback_query(call.id)

def finish_order(message):
    chat_id = str(message.chat.id)
    full_name = message.text.strip()
    username = message.from_user.username or ""
    if chat_id not in user_data:
        bot.send_message(message.chat.id, "⚠️ خطا! لطفا دوباره سفارش خود را شروع کنید.")
        return
    user_data[chat_id]["full_name"] = full_name
    user_data[chat_id]["username"] = username
    name_to_chat_id[full_name] = chat_id
    service_type = user_data[chat_id].get("service_type", "نامشخص")
    volume = user_data[chat_id].get("volume", "نامحدود")
    duration = user_data[chat_id].get("duration", "نامشخص")
    invoice_id = random.randint(100000, 999999)
    order_info = {
        "full_name": full_name,
        "service_type": service_type,
        "volume": volume,
        "duration": duration,
        "invoice_id": invoice_id,
        "username": username
    }
    orders_history[full_name] = order_info
    save_data()

    summary = (
        f"🆕 سفارش جدید ثبت شد:\n"
        f"📄 فاکتور شماره: {invoice_id}\n"
        f"🔘 نوع سرویس: {service_type}\n"
        f"📦 حجم: {volume}\n"
        f"🕐 مدت زمان: {duration}\n"
        f"👤 نام مشتری: {full_name}\n"
        f"🔗 یوزرنیم تلگرام: @{username if username else 'ندارد'}"
    )
    bot.send_message(ADMIN_ID, summary)
    bot.send_message(message.chat.id, "✅ سفارش شما ثبت شد. منتظر تماس باشید.")

def show_orders_page(chat_id):
    state = admin_state.get(chat_id)
    if not state:
        return
    page = state["page"]
    orders = state["orders"]
    total_pages = (len(orders) - 1) // PER_PAGE + 1

    page_orders = orders[page*PER_PAGE:(page+1)*PER_PAGE]
    text = ""
    for order in page_orders:
        text += (
            f"📄 فاکتور: {order['invoice_id']}\n"
            f"🔘 نوع سرویس: {order['service_type']}\n"
            f"📦 حجم: {order['volume']}\n"
            f"🕐 مدت: {order['duration']}\n"
            f"👤 نام مشتری: {order['full_name']}\n"
            f"🔗 یوزرنیم: @{order['username'] if order['username'] else 'ندارد'}\n\n"
        )
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    btns = []
    if page > 0:
        btns.append(telebot.types.InlineKeyboardButton("⬅️ قبلی", callback_data="prev_orders"))
    if page < total_pages - 1:
        btns.append(telebot.types.InlineKeyboardButton("➡️ بعدی", callback_data="next_orders"))
    if btns:
        markup.add(*btns)
    bot.send_message(chat_id, f"📄 صفحه {page + 1} از {total_pages}\n\n{text}", reply_markup=markup)

def handle_invoice_name(message):
    name = message.text.strip()
    if name not in orders_history:
        bot.send_message(ADMIN_ID, "❌ نام مشتری یافت نشد، لطفا دوباره وارد کنید:")
        bot.register_next_step_handler_by_chat_id(ADMIN_ID, handle_invoice_name)
        return
    order = orders_history[name]
    summary = (
        f"📄 فاکتور شماره: {order['invoice_id']}\n"
        f"🔘 نوع سرویس: {order['service_type']}\n"
        f"📦 حجم: {order['volume']}\n"
        f"🕐 مدت زمان: {order['duration']}\n"
        f"👤 نام مشتری: {order['full_name']}"
    )
    chat_id = name_to_chat_id.get(name)
    if chat_id:
        bot.send_message(chat_id, f"📩 فاکتور شما:\n\n{summary}")
        bot.send_message(ADMIN_ID, "✅ فاکتور ارسال شد.")
    else:
        bot.send_message(ADMIN_ID, "❌ کاربر در دسترس نیست.")

def handle_send_volume(message):
    full_name = message.text.strip()
    if full_name not in orders_history:
        bot.send_message(ADMIN_ID, "❌ نام مشتری یافت نشد، لطفا دوباره وارد کنید:")
        bot.register_next_step_handler_by_chat_id(ADMIN_ID, handle_send_volume)
        return
    order = orders_history[full_name]
    chat_id = name_to_chat_id.get(full_name)
    if not chat_id:
        bot.send_message(ADMIN_ID, "❌ کاربر در دسترس نیست.")
        return

    volume_str = order.get('volume', 'نامشخص')

    # نمایش وضعیت حجم با آیکون و رنگ ساده
    try:
        vol_num = int(volume_str.replace(' گیگ', '').strip())
        if vol_num <= 5:
            icon = "🔴"
            status = "حجم شما رو به اتمام است!"
        else:
            icon = "🟢"
            status = "حجم شما کافی است."
    except:
        icon = "⚪️"
        status = "حجم نامشخص است."

    msg = f"{icon} سلام {full_name}!\nحجم باقی‌مانده شما: {volume_str}\n{status}"
    bot.send_message(chat_id, msg)
    bot.send_message(ADMIN_ID, "✅ پیام حجم ارسال شد.")

@bot.message_handler(commands=['send'])
def send_command(message):
    if message.chat.id != ADMIN_ID:
        return
    try:
        parts = message.text.split()
        if len(parts) != 3:
            bot.send_message(ADMIN_ID, "❌ فرمت دستور اشتباه است.\nمثال درست: /send ali 5")
            return
        username = parts[1].strip('@')
        vol = parts[2]
        found_name = None
        for name, order in orders_history.items():
            if order.get('username', '').lower() == username.lower():
                found_name = name
                break
        if not found_name:
            bot.send_message(ADMIN_ID, "❌ کاربر یافت نشد.")
            return
        chat_id = name_to_chat_id.get(found_name)
        if not chat_id:
            bot.send_message(ADMIN_ID, "❌ کاربر در دسترس نیست.")
            return
        icon = "🔴" if int(vol) <= 5 else "🟢"
        status = "حجم شما رو به اتمام است!" if int(vol) <= 5 else "حجم شما کافی است."
        msg = f"{icon} سلام {found_name}!\nحجم باقی‌مانده شما: {vol} گیگ\n{status}"
        bot.send_message(chat_id, msg)
        bot.send_message(ADMIN_ID, "✅ پیام حجم ارسال شد.")
    except Exception as e:
        bot.send_message(ADMIN_ID, f"❌ خطا در ارسال پیام: {e}")

# Flask webhook handlers
@server.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@server.route('/')
def index():
    return "Bot is running."

bot.remove_webhook()
bot.set_webhook(url=WEBHOOK_URL + TOKEN)

if __name__ == '__main__':
    server.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
