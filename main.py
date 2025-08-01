import os
import logging
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, Bot
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, CallbackContext

# ======== تنظیمات ========
TOKEN = "8480626201:AAG9AzRxwdYboj5SNLeNcVtOrNOvlNY_vsM"
ADMIN_ID = 7210975276

app = Flask(__name__)

# لاگ
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=TOKEN)
dispatcher = Dispatcher(bot, None, workers=0, use_context=True)

# دیتای سفارش‌ها در حافظه (موقت)
USERS = {}

# بسته‌های فروش
PACKAGES = {
    "20": {"label": "۲۰ گیگ یک ماهه", "price": 100000},
    "30": {"label": "۳۰ گیگ یک ماهه", "price": 150000},
    "40": {"label": "۴۰ گیگ یک ماهه", "price": 200000},
    "50": {"label": "۵۰ گیگ یک ماهه", "price": 250000},
    "unlimited": {"label": "نامحدود یک ماهه", "price": 350000},
}

# منوی اصلی با دکمه‌های شیشه‌ای
def main_menu_keyboard():
    buttons = [
        [KeyboardButton("🛒 خرید سرویس")],
        [KeyboardButton("📲 راهنمای نصب"), KeyboardButton("💳 کارت به کارت")],
        [KeyboardButton("💬 پشتیبانی"), KeyboardButton("📦 سفارش‌های من")]
    ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

# دستور /start
def start(update: Update, context: CallbackContext):
    user = update.effective_user
    USERS.setdefault(user.id, {"username": user.username, "orders": []})
    text = f"سلام {user.first_name} عزیز!\nبه ربات فروش VPN خوش آمدید.\nاز منوی زیر استفاده کنید."
    update.message.reply_text(text, reply_markup=main_menu_keyboard())

# شروع خرید: نمایش بسته‌ها با دکمه‌های اینلاین
def buy_service(update: Update, context: CallbackContext):
    keyboard = []
    for key, pkg in PACKAGES.items():
        keyboard.append([InlineKeyboardButton(f"{pkg['label']} - {pkg['price']:,} تومان", callback_data=f"buy_{key}")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("حجم مورد نظر را انتخاب کنید:", reply_markup=reply_markup)

# مدیریت کلیک روی دکمه‌ها
def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data

    if data.startswith("buy_"):
        package_key = data[4:]
        pkg = PACKAGES.get(package_key)
        if not pkg:
            query.answer("بسته نامعتبر است.")
            return

        order = {
            "package": pkg['label'],
            "price": pkg['price'],
            "status": "در انتظار پرداخت"
        }
        USERS.setdefault(user_id, {"username": query.from_user.username, "orders": []})
        USERS[user_id]["orders"].append(order)

        invoice_text = (
            f"فاکتور خرید:\n"
            f"------------------------------\n"
            f"کاربر: @{query.from_user.username or query.from_user.first_name}\n"
            f"بسته: {pkg['label']}\n"
            f"مبلغ قابل پرداخت: {pkg['price']:,} تومان\n"
            f"وضعیت: {order['status']}\n"
            f"------------------------------\n"
            f"لطفاً مبلغ را به کارت زیر واریز کنید و سپس به پشتیبانی اطلاع دهید:\n\n"
            "شماره کارت: 6037 9912 3456 7890\n"
            "بانک ملی ایران"
        )
        query.answer()
        query.edit_message_text(invoice_text)

    else:
        query.answer()

# نمایش سفارش‌های کاربر
def my_orders(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    orders = USERS.get(user_id, {}).get("orders", [])
    if not orders:
        update.message.reply_text("شما هنوز سفارشی ثبت نکرده‌اید.")
        return

    text = "📦 سفارش‌های شما:\n\n"
    for i, order in enumerate(orders, 1):
        text += f"#{i} بسته: {order['package']}\n"
        text += f"وضعیت: {order['status']}\n\n"
    update.message.reply_text(text)

# متن پیام‌ها و منو
def message_handler(update: Update, context: CallbackContext):
    text = update.message.text
    if text == "🛒 خرید سرویس":
        buy_service(update, context)
    elif text == "📦 سفارش‌های من":
        my_orders(update, context)
    elif text == "💳 کارت به کارت":
        update.message.reply_text(
            "لطفاً مبلغ را به شماره کارت زیر واریز کنید:\n\n"
            "شماره کارت: 6037 9912 3456 7890\n"
            "بانک ملی ایران\n\n"
            "پس از واریز، رسید را به پشتیبانی ارسال کنید."
        )
    elif text == "📲 راهنمای نصب":
        update.message.reply_text(
            "راهنمای نصب VPN:\n"
            "1. برنامه را دانلود کنید.\n"
            "2. کانفیگ را وارد کنید.\n"
            "3. اتصال را تست کنید.\n\n"
            "برای راهنمایی بیشتر با پشتیبانی تماس بگیرید."
        )
    elif text == "💬 پشتیبانی":
        update.message.reply_text(
            "برای پشتیبانی با ادمین تماس بگیرید:\n"
            "@YourSupportUsername"
        )
    else:
        update.message.reply_text("لطفاً از منوی زیر گزینه‌ای انتخاب کنید.", reply_markup=main_menu_keyboard())

# ادمین ارسال کانفیگ به کاربر (با جواب دادن به پیام کاربر)
def admin_send_config(update: Update, context: CallbackContext):
    if update.effective_user.id != ADMIN_ID:
        update.message.reply_text("شما اجازه این کار را ندارید.")
        return
    if not update.message.reply_to_message:
        update.message.reply_text("این دستور باید به پیام کاربر جواب داده شود.")
        return
    user_id = update.message.reply_to_message.from_user.id
    config_text = update.message.text
    bot.send_message(chat_id=user_id, text=f"🔑 کانفیگ شما:\n\n{config_text}")
    update.message.reply_text("کانفیگ ارسال شد.")

# ثبت هندلر‌ها
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, message_handler))
dispatcher.add_handler(CallbackQueryHandler(button_handler))
dispatcher.add_handler(MessageHandler(Filters.reply & Filters.text, admin_send_config))

# روت ساده برای تست سلامت سرور
@app.route("/", methods=["GET"])
def index():
    return "✅ ربات فروش VPN فعال است"

# روت webhook تلگرام
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(force=True)
    update = Update.de_json(data, bot)
    dispatcher.process_update(update)
    return "OK"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
