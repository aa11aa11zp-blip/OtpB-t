import requests
import sqlite3
import re
import time
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ---------------- CONFIG ----------------
BOT_TOKEN = "8281944831:AAGrz2zrLVLwdDd2BKISYUndRnD6yLn8pEE"
API_TOKEN = "RFdUREJBUzR9T4dVc49ndmFra1NYV5CIhpGVcnaOYmqHhJZXfYGJSQ=="
API_URL = "http://147.135.212.197/crapi/st/viewstats"

ADMIN_ID = 1316375131
CHANNELS = ["@ProTech43", "@HematTech", "@Pro43Zone", "@SQ_Botz"]

# ---------------- DATABASE ----------------
conn = sqlite3.connect("data.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    referrals INTEGER DEFAULT 0,
    invited_by INTEGER
)
""")

conn.commit()

# ---------------- JOIN CHECK ----------------
async def check_join(user_id, context):
    for ch in CHANNELS:
        try:
            member = await context.bot.get_chat_member(ch, user_id)
            if member.status in ["left", "kicked"]:
                return False
        except:
            return False
    return True

# ---------------- USER ----------------
def add_user(user_id, ref=None):
    cur.execute("INSERT OR IGNORE INTO users (user_id, invited_by) VALUES (?,?)", (user_id, ref))
    conn.commit()

    if ref:
        cur.execute("UPDATE users SET referrals = referrals + 1 WHERE user_id=?", (ref,))
        conn.commit()

def get_refs(user_id):
    cur.execute("SELECT referrals FROM users WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    return row[0] if row else 0

# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args

    ref = int(args[0]) if args else None
    add_user(user.id, ref)

    if not await check_join(user.id, context):
        btn = [[InlineKeyboardButton("📢 Join Channel", url="https://t.me/ProTech43")]]
        await update.message.reply_text(
            "⚠️ Please join all channels first!",
            reply_markup=InlineKeyboardMarkup(btn)
        )
        return

    keyboard = [
        [InlineKeyboardButton("📱 Get Number", callback_data="get")],
        [InlineKeyboardButton("👥 Referrals", callback_data="ref")]
    ]

    await update.message.reply_text(
        "✨ Welcome to OTP Bot ✨\n\nChoose option:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ---------------- BUTTONS ----------------
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    if query.data == "get":
        refs = get_refs(user_id)

        if refs < 2:
            link = f"https://t.me/YOUR_BOT?start={user_id}"
            await query.message.reply_text(
                f"❌ Need 2 referrals!\n\n🔗 Your link:\n{link}"
            )
            return

        cur.execute("UPDATE users SET referrals = referrals - 2 WHERE user_id=?", (user_id,))
        conn.commit()

        await query.message.reply_text("📩 Send Service Name (WhatsApp / Telegram)")

        context.user_data["wait_service"] = True

    elif query.data == "ref":
        refs = get_refs(user_id)
        link = f"https://t.me/YOUR_BOT?start={user_id}"

        await query.message.reply_text(
            f"👥 Referrals: {refs}\n\n🔗 Link:\n{link}"
        )

# ---------------- FETCH OTP ----------------
def fetch_sms():
    try:
        r = requests.get(API_URL, params={"token": API_TOKEN}, timeout=10)
        data = r.json()
        return data if isinstance(data, list) else []
    except:
        return []

# ---------------- MESSAGE ----------------
async def message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("wait_service"):
        context.user_data["wait_service"] = False

        number = "+1234567890"  # API نه number واخله که غواړې

        context.user_data["number"] = number

        await update.message.reply_text(
            f"📞 Number:\n{number}\n\n⏳ Waiting OTP..."
        )

        # OTP check loop
        for i in range(10):
            data = fetch_sms()

            for entry in data:
                msg = entry[2]

                otp = re.search(r"\b\d{4,8}\b", msg)
                if otp:
                    await update.message.reply_text(
                        f"✅ OTP Received:\n\n🔑 {otp.group()}"
                    )
                    return

            time.sleep(5)

        await update.message.reply_text("❌ OTP not received!")

# ---------------- BROADCAST ----------------
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return

    text = " ".join(context.args)

    cur.execute("SELECT user_id FROM users")
    users = cur.fetchall()

    for u in users:
        try:
            await context.bot.send_message(chat_id=u[0], text=text)
        except:
            pass

    await update.message.reply_text("✅ Broadcast Sent")

# ---------------- MAIN ----------------
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(buttons))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message))
app.add_handler(CommandHandler("broadcast", broadcast))

print("🚀 Bot Running...")
app.run_polling() 
