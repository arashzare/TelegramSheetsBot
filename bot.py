import os
import datetime
import json
import asyncio
import base64
import gspread
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from openai import OpenAI

TOKEN = os.environ.get('BOT_TOKEN')
if not TOKEN:
    raise ValueError("BOT_TOKEN environment variable is not set")

SHEET_ID = os.environ.get('SHEET_ID')
if not SHEET_ID:
    raise ValueError("SHEET_ID environment variable is not set. Please provide your Google Sheet ID from the URL")

creds_json = os.environ.get('GOOGLE_SHEETS_CREDENTIALS')
if not creds_json:
    raise ValueError(
        "GOOGLE_SHEETS_CREDENTIALS environment variable is not set")

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

OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    print("⚠️ Warning: OPENAI_API_KEY not set. Receipt OCR will not work.")
    openai_client = None
else:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    print("✅ OpenAI client initialized for receipt OCR")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Hi! Send me your expense like:\n\n"
                                    "Lunch 12.50\n\n"
                                    "or send a photo of your receipt.")


async def add_expense(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    parts = text.split()

    if not parts:
        await update.message.reply_text("❌ Please send in this format:\n"
                                        "Example: Coffee 3.75")
        return

    try:
        amount = float(parts[-1])
        description = " ".join(parts[:-1])

        if not description:
            await update.message.reply_text("❌ Please include a description.\n"
                                            "Example: Coffee 3.75")
            return

        if amount < 0:
            await update.message.reply_text("❌ Amount must be positive.\n"
                                            "Example: Coffee 3.75")
            return

        date = datetime.date.today().isoformat()
        row_data = [date, description, str(amount), ""]
        print(f"Saving row: {row_data}", flush=True)
        await asyncio.to_thread(sheet.append_row, row_data)
        print(f"Row saved successfully: Date={date}, Description={description}, Amount={amount}", flush=True)
        await update.message.reply_text(f"✅ Saved: {description} - ${amount}")
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid amount. Please send in this format:\n"
            "Example: Coffee 3.75")
    except Exception as e:
        await update.message.reply_text(f"❌ Error saving expense: {str(e)}")


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.reply_text("🔍 Analyzing receipt image...")
        
        photo = update.message.photo[-1]
        file_id = photo.file_id
        
        photo_file = await context.bot.get_file(file_id)
        photo_bytes = await photo_file.download_as_bytearray()
        
        base64_image = base64.b64encode(photo_bytes).decode('utf-8')
        
        if not openai_client:
            await update.message.reply_text("❌ OCR not available. Please set OPENAI_API_KEY.")
            return
        
        # the newest OpenAI model is "gpt-5" which was released August 7, 2025.
        # do not change this unless explicitly requested by the user
        response = await asyncio.to_thread(
            lambda: openai_client.chat.completions.create(
                model="gpt-5",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Analyze this receipt image and extract the total amount. "
                                       "Only return the numerical value of the total amount (e.g., 12.50). "
                                       "If you cannot find a total, return 0. "
                                       "Do not include currency symbols or any other text."
                            },
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                            }
                        ]
                    }
                ],
                max_completion_tokens=100
            )
        )
        
        amount_text = response.choices[0].message.content.strip()
        
        try:
            amount = float(amount_text)
        except ValueError:
            amount = 0.0
        
        date = datetime.date.today().isoformat()
        description = "Receipt Photo"
        row_data = [date, description, str(amount), file_id]
        
        print(f"Saving receipt: Date={date}, Amount={amount}, FileID={file_id}", flush=True)
        await asyncio.to_thread(sheet.append_row, row_data)
        
        if amount > 0:
            await update.message.reply_text(f"✅ Receipt saved! Amount detected: ${amount}")
        else:
            await update.message.reply_text("✅ Receipt saved but amount could not be detected. Amount set to 0.")
            
    except Exception as e:
        print(f"Error processing receipt: {str(e)}", flush=True)
        await update.message.reply_text(f"❌ Error processing receipt: {str(e)}")


if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, add_expense))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    print("🤖 Bot is running...")
    app.run_polling()
