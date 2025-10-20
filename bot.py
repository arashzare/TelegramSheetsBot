import os
import datetime
import json
import gspread
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.environ.get('BOT_TOKEN')
SHEET_NAME = os.environ.get('SHEET_NAME', 'Expenses')

creds_json = os.environ.get('GOOGLE_SHEETS_CREDENTIALS', '{}')
if not creds_json or creds_json == '{}':
    raise ValueError("GOOGLE_SHEETS_CREDENTIALS environment variable is not set")
creds_dict = json.loads(creds_json)
gc = gspread.service_account_from_dict(creds_dict)

sheet = gc.open(SHEET_NAME).sheet1

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hi! Send me your expense like:\n\n"
        "Lunch 12.50\n\n"
        "or send a photo of your receipt."
    )

async def add_expense(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    parts = text.split()
    try:
        amount = float(parts[-1])
        description = " ".join(parts[:-1])
        date = datetime.date.today().isoformat()
        sheet.append_row([date, description, amount, ""])
        await update.message.reply_text(f"✅ Saved: {description} - ${amount}")
    except:
        await update.message.reply_text(
            "❌ Please send in this format:\n"
            "Example: Coffee 3.75"
        )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    file = await photo.get_file()
    file_url = file.file_path
    date = datetime.date.today().isoformat()
    sheet.append_row([date, "Receipt Photo", "", file_url])
    await update.message.reply_text("📸 Receipt saved to Google Sheet!")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, add_expense))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    print("🤖 Bot is running...")
    app.run_polling()
