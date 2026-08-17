 import os
import sqlite3
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

TOKEN = os.getenv("BOT_TOKEN")

DB = "bot.db"


def init_db():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            referrals INTEGER DEFAULT 0,
            invited_by INTEGER
        )
    """)

    conn.commit()
    conn.close()


def add_user(user_id, username, first_name, invited_by=None):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute(
        "SELECT user_id FROM users WHERE user_id = ?",
        (user_id,)
    )

    exists = cur.fetchone()

    if not exists:
        cur.execute("""
            INSERT INTO users
            (user_id, username, first_name, referrals, invited_by)
            VALUES (?, ?, ?, 0, ?)
        """, (user_id, username, first_name, invited_by))

        if invited_by and invited_by != user_id:
            cur.execute("""
                UPDATE users
                SET referrals = referrals + 1
                WHERE user_id = ?
            """, (invited_by,))

    conn.commit()
    conn.close()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    invited_by = None

    if context.args:
        try:
            invited_by = int(context.args[0])
        except ValueError:
            pass

    add_user(
        user.id,
        user.username or "",
        user.first_name or "",
        invited_by
    )

    referral_link = (
        f"https://t.me/{context.bot.username}?start={user.id}"
    )

    text = (
        f"🌱 سلام {user.first_name}!\n\n"
        "به PhoenixGrowBot 🦅 خوش آمدی.\n\n"
        "اینجا می‌توانی:\n"
        "👤 حساب خودت را مدیریت کنی\n"
        "👥 دوستانت را دعوت کنی\n"
        "📊 آمار دعوت‌هایت را ببینی\n\n"
        "🔗 لینک دعوت اختصاصی تو:\n"
        f"{referral_link}\n\n"
        "برای دیدن امکانات، /help را بزن."
    )

    await update.message.reply_text(text)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🦅 PhoenixGrowBot\n\n"
        "دستورات موجود:\n\n"
        "/start - شروع ربات\n"
        "/help - راهنما\n"
        "/stats - آمار حساب\n"
        "/ref - لینک دعوت\n\n"
        "امکانات تبلیغات و درآمدزایی در نسخه‌های بعدی اضافه می‌شوند."
    )

    await update.message.reply_text(text)


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute(
        "SELECT referrals FROM users WHERE user_id = ?",
        (user_id,)
    )

    result = cur.fetchone()
    conn.close()

    referrals = result[0] if result else 0

    await update.message.reply_text(
        f"📊 آمار حساب شما\n\n"
        f"👥 تعداد دعوت‌ها: {referrals}\n"
        f"🆔 شناسه شما: {user_id}"
    )


async def referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    bot_username = context.bot.username

    link = f"https://t.me/{bot_username}?start={user_id}"

    await update.message.reply_text(
        "🔗 لینک دعوت اختصاصی شما:\n\n"
        f"{link}\n\n"
        "این لینک را برای دوستانت ارسال کن."
    )


def main():
    if not TOKEN:
        raise RuntimeError(
            "BOT_TOKEN is not configured."
        )

    init_db()

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("ref", referral))

    print("PhoenixGrowBot is running...")

    app.run_polling()


if __name__ == "__main__":
    main()
