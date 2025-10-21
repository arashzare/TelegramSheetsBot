import os
import datetime
import json
import asyncio
import gspread
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.environ.get('BOT_TOKEN')
if not TOKEN:
    raise ValueError("BOT_TOKEN environment variable is not set")

SHEET_ID = os.environ.get('SHEET_ID')
if not SHEET_ID:
    raise ValueError("SHEET_ID environment variable is not set. Please provide your Google Sheet ID from the URL")

creds_json = os.environ.get('GOOGLE_SHEETS_CREDENTIALS')
if not creds_json:
    raise ValueError("GOOGLE_SHEETS_CREDENTIALS environment variable is not set")

try:
    creds_dict = json.loads(creds_json)
except json.JSONDecodeError as e:
    raise ValueError(f"GOOGLE_SHEETS_CREDENTIALS is not valid JSON: {str(e)}")

gc = gspread.service_account_from_dict(creds_dict)

try:
    sheet = gc.open_by_key(SHEET_ID).sheet1
    print(f"✅ Connected to Google Sheet (ID: {SHEET_ID})")
except Exception as e:
    print(f"❌ Failed to connect to Google Sheet: {str(e)}")
    print("Please ensure:")
    print("1. Google Sheets API is enabled in your Google Cloud project")
    print("2. The spreadsheet is shared with the service account email")
    raise

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hi! Send me your expense like:\n\n"
        "Lunch 12.50\n\n"
        "or send a photo of your receipt."
    )

async def add_expense(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    parts = text.split()
    
    if not parts:
        await update.message.reply_text(
            "❌ Please send in this format:\n"
            "Example: Coffee 3.75"
        )
        return
    
    try:
        amount = float(parts[-1])
        description = " ".join(parts[:-1])
        
        if not description:
            await update.message.reply_text(
                "❌ Please include a description.\n"
                "Example: Coffee 3.75"
            )
            return
        
        if amount < 0:
            await update.message.reply_text(
                "❌ Amount must be positive.\n"
                "Example: Coffee 3.75"
            )
            return
        
        date = datetime.date.today().isoformat()
        await asyncio.to_thread(sheet.append_row, [date, description, amount, ""])
        await update.message.reply_text(f"✅ Saved: {description} - ${amount}")
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid amount. Please send in this format:\n"
            "Example: Coffee 3.75"
        )
    except Exception as e:
        await update.message.reply_text(
            f"❌ Error saving expense: {str(e)}"
        )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        photo = update.message.photo[-1]
        file_id = photo.file_id
        date = datetime.date.today().isoformat()
        await asyncio.to_thread(sheet.append_row, [date, "Receipt Photo", "", file_id])
        await update.message.reply_text("📸 Receipt saved to Google Sheet!")
    except Exception as e:
        await update.message.reply_text(
            f"❌ Error saving receipt: {str(e)}"
        )

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, add_expense))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    print("🤖 Bot is running...")
    app.run_polling()
