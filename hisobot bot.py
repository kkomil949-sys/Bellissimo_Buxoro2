import json
import os
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

TOKEN = 8744849749:AAEhtT4o6bjXubPExZpfyqS8zxMdDL7OMQ4

ADMIN_ID = 1810923583
DATA_FILE = "xodimlar.json"

ISM = 0

def yukla():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def saqla(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = yukla()

    if user_id in data:
        ism = data[user_id]["ism"]
        keyboard = [["📸 Hisobot yuborish"]]
        await update.message.reply_text(
            f"Salom, *{ism}*! 👋\nBugungi hisobot rasmingizni yuboring.",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            "Salom! 👋\n*Ism va familiyangizni* kiriting:",
            reply_markup=ReplyKeyboardRemove(),
            parse_mode="Markdown"
        )
        return ISM

async def ism_kiriting(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    ism = update.message.text
    data = yukla()
    data[user_id] = {"ism": ism, "hisobotlar": []}
    saqla(data)

    keyboard = [["📸 Hisobot yuborish"]]
    await update.message.reply_text(
        f"✅ *{ism}* — saqlandi!\nEndi kunlik hisobot rasmingizni yubora olasiz.",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
        parse_mode="Markdown"
    )
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"🆕 Yangi xodim:\n👤 *{ism}*",
        parse_mode="Markdown"
    )
    return ConversationHandler.END

async def hisobot_boshlash(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = yukla()
    if user_id not in data:
        await update.message.reply_text("Avval /start bilan ro'yxatdan o'ting!")
        return
    await update.message.reply_text("📸 Rasmni yuboring:", reply_markup=ReplyKeyboardRemove())
    context.user_data["kutilmoqda"] = True

async def rasm_qabul(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("kutilmoqda"):
        return

    user_id = str(update.effective_user.id)
    data = yukla()
    if user_id not in data:
        await update.message.reply_text("Avval /start bilan ro'yxatdan o'ting!")
        return

    photo = update.message.photo[-1]
    file_id = photo.file_id
    sana = datetime.now().strftime("%d.%m.%Y %H:%M")
    izoh = update.message.caption or ""

    data[user_id]["hisobotlar"].append({"file_id": file_id, "sana": sana, "izoh": izoh})
    saqla(data)
    context.user_data["kutilmoqda"] = False

    keyboard = [["📸 Hisobot yuborish"]]
    await update.message.reply_text(
        f"✅ Hisobot qabul qilindi! *{sana}*",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
        parse_mode="Markdown"
    )

    ism = data[user_id]["ism"]
    caption = f"📋 *Yangi hisobot*\n👤 {ism}\n📅 {sana}"
    if izoh:
        caption += f"\n💬 {izoh}"
    await context.bot.send_photo(chat_id=ADMIN_ID, photo=file_id, caption=caption, parse_mode="Markdown")

async def admin_xodimlar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Siz admin emassiz!")
        return
    data = yukla()
    if not data:
        await update.message.reply_text("Hali hech kim ro'yxatdan o'tmagan.")
        return
    matn = "👥 *Barcha xodimlar:*\n\n"
    for i, (uid, x) in enumerate(data.items(), 1):
        jami = len(x["hisobotlar"])
        oxirgi = x["hisobotlar"][-1]["sana"] if x["hisobotlar"] else "Hali yo'q"
        matn += f"{i}. 👤 *{x['ism']}*\n   📊 {jami} ta hisobot | 🕐 {oxirgi}\n\n"
    await update.message.reply_text(matn, parse_mode="Markdown")

async def admin_bugun(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Siz admin emassiz!")
        return
    data = yukla()
    bugun = datetime.now().strftime("%d.%m.%Y")
    topildi = False
    for uid, xodim in data.items():
        bugungi = [h for h in xodim["hisobotlar"] if h["sana"].startswith(bugun)]
        for h in bugungi:
            topildi = True
            caption = f"👤 *{xodim['ism']}*\n📅 {h['sana']}"
            if h["izoh"]:
                caption += f"\n💬 {h['izoh']}"
            await context.bot.send_photo(chat_id=ADMIN_ID, photo=h["file_id"], caption=caption, parse_mode="Markdown")
    if not topildi:
        await update.message.reply_text(f"📭 Bugun ({bugun}) hech kim hisobot yubormagan.")

def main():
    app = Application.builder().token(TOKEN).build()

    royxat_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={ISM: [MessageHandler(filters.TEXT & ~filters.COMMAND, ism_kiriting)]},
        fallbacks=[CommandHandler("start", start)]
    )

    app.add_handler(royxat_handler)
    app.add_handler(MessageHandler(filters.Regex("📸 Hisobot yuborish"), hisobot_boshlash))
    app.add_handler(MessageHandler(filters.PHOTO, rasm_qabul))
    app.add_handler(CommandHandler("xodimlar", admin_xodimlar))
    app.add_handler(CommandHandler("bugun", admin_bugun))

    print("✅ Bot ishga tushdi!")
    app.run_polling()

if __name__ == "__main__":
    main()
