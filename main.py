import os
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, ContextTypes, CommandHandler,
    MessageHandler, CallbackQueryHandler, filters
)

TOKEN = "8480626201:AAG9AzRxwdYboj5SNLeNcVtOrNOvlNY_vsM"
ADMIN_ID = 7210975276
PORT = int(os.environ.get("PORT", 10000))

app = Flask(__name__)

# دیتای موقت سفارش‌ها
USERS = {}

PACKAGES = {
    "20": {"label": "۲۰ گیگ یک ماهه", "price": 100000},
    "30": {"label": "۳۰ گیگ یک ماهه", "price": 150000},
    "40": {"label": "۴۰ گیگ یک ماهه", "price": 200000},
    "50": {"label": "۵۰ گیگ یک ماهه", "price": 250000},
    "unlimited": {"label": "نامحدود یک ماهه", "price": 350000},
}

# منوی اصلی
def main_menu():
    return ReplyKeyboardMarkup([
        [KeyboardButton("🛒 خرید سرویس")],
        [KeyboardButton("📲 راهنمای نصب"), KeyboardButton("💳 کارت به کارت")],
        [KeyboardButton("💬 پشتیبانی"), KeyboardButton("📦 سفارش‌های من")]
    ], resize_keyboard=True)

# هندلر استارت
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    USERS.setdefault(user.id, {"username": user.username, "orders": []})
    await update.message.reply_text(
        f"سلام {user.first_name}!\nبه ربات فروش VPN خوش آمدید.",
        reply_markup=main_menu()
    )

# هندلر پیام‌های متنی
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "🛒 خرید سرویس":
        keyboard = [
            [InlineKeyboardButton(f"{p['label']} - {p['price']:,} تومان", callback_data=f"buy_{k}")]
            for k, p in PACKAGES.items()
        ]
        await update.message.reply_text("لطفاً یک بسته انتخاب کنید:", reply_markup=InlineKeyboardMarkup(keyboard))
    elif text == "📦 سفارش‌های من":
        orders = USERS.get(update.effective_user.id, {}).get("orders", [])
        if not orders:
            await update.message.reply_text("سفارشی ثبت نکرده‌اید.")
            return
        msg = "📦 سفارش‌های شما:\n\n"
        for i, o in enumerate(orders, 1):
            msg += f"#{i} - {o['package']} | {o['price']} تومان | {o['status']}\n"
        await update.message.reply_text(msg)
    elif text == "📲 راهنمای نصب":
        await update.message.reply_text("برای نصب VPN اپ را باز و کانفیگ را وارد و متصل شوید.")
    elif text == "💳 کارت به کارت":
        await update.message.reply_text("💳 شماره کارت: 6037 9912 3456 7890\nبانک ملی\nلطفاً پس از پرداخت اطلاع دهید.")
    elif text == "💬 پشتیبانی":
        await update.message.reply_text("پشتیبانی: @YourSupportUsername")
    else:
        await update.message.reply_text("لطفاً از منو استفاده کنید.", reply_markup=main_menu())

# هندلر دکمه‌های اینلاین
async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    if data.startswith("buy_"):
        package_key = data[4:]
        pkg = PACKAGES.get(package_key)
        if pkg:
            order = {
                "package": pkg["label"],
                "price": pkg["price"],
                "status": "در انتظار پرداخت"
            }
            USERS[user_id]["orders"].append(order)
            await query.edit_message_text(
                f"🧾 فاکتور خرید:\n"
                f"بسته: {pkg['label']}\n"
                f"مبلغ: {pkg['price']:,} تومان\n"
                f"وضعیت: {order['status']}\n\n"
                f"💳 شماره کارت: 6037 9912 3456 7890\n"
                f"پس از پرداخت اطلاع دهید."
            )

# اجرای برنامه تلگرام
async def telegram_main():
    app_bot = ApplicationBuilder().token(TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app_bot.add_handler(CallbackQueryHandler(handle_button))

    # اجرای webhook روی همین سرور flask
    await app_bot.initialize()
    await app_bot.start()
    await app_bot.updater.start_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME')}/webhook"
    )

@app.route("/", methods=["GET"])
def home():
    return "✅ ربات فعال است"

@app.route("/webhook", methods=["POST"])
async def webhook():
    return "OK"

import asyncio
if __name__ == "__main__":
    asyncio.run(telegram_main())
    app.run(host="0.0.0.0", port=PORT)
