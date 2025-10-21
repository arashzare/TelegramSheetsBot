import os
import datetime
import json
import asyncio
import gspread
import re
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from google.cloud import vision
from google.oauth2 import service_account

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

try:
    vision_credentials = service_account.Credentials.from_service_account_info(creds_dict)
    vision_client = vision.ImageAnnotatorClient(credentials=vision_credentials)
    print("✅ Google Cloud Vision client initialized for receipt OCR")
except Exception as e:
    print(f"⚠️ Warning: Could not initialize Vision API: {str(e)}")
    print("Receipt OCR will not work.")
    vision_client = None


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


def extract_receipt_info(text):
    date = datetime.date.today().isoformat()
    description = "Unknown"
    amount = 0.0
    
    lines = text.split('\n')
    
    date_patterns = [
        r'\d{4}[-/]\d{1,2}[-/]\d{1,2}',
        r'\d{1,2}[-/]\d{1,2}[-/]\d{4}',
        r'\d{1,2}[-/]\d{1,2}[-/]\d{2}',
    ]
    
    for line in lines:
        for pattern in date_patterns:
            match = re.search(pattern, line)
            if match:
                date_str = match.group()
                try:
                    if '/' in date_str:
                        date_parts = date_str.split('/')
                        if len(date_parts[0]) == 4:
                            parsed_date = datetime.datetime.strptime(date_str, '%Y/%m/%d')
                        elif len(date_parts[2]) == 4:
                            parsed_date = datetime.datetime.strptime(date_str, '%m/%d/%Y')
                        else:
                            parsed_date = datetime.datetime.strptime(date_str, '%m/%d/%y')
                    else:
                        date_parts = date_str.split('-')
                        if len(date_parts[0]) == 4:
                            parsed_date = datetime.datetime.strptime(date_str, '%Y-%m-%d')
                        elif len(date_parts[2]) == 4:
                            parsed_date = datetime.datetime.strptime(date_str, '%m-%d-%Y')
                        else:
                            parsed_date = datetime.datetime.strptime(date_str, '%m-%d-%y')
                    date = parsed_date.strftime('%Y-%m-%d')
                    break
                except:
                    pass
        if date != datetime.date.today().isoformat():
            break
    
    if len(lines) > 0:
        description = lines[0].strip()
    
    amount_patterns = [
        r'total[:\s]*\$?\s*(\d+\.\d{2})',
        r'amount[:\s]*\$?\s*(\d+\.\d{2})',
        r'\$\s*(\d+\.\d{2})',
        r'(\d+\.\d{2})',
    ]
    
    for line in reversed(lines):
        line_lower = line.lower()
        for pattern in amount_patterns:
            match = re.search(pattern, line_lower)
            if match:
                try:
                    amount = float(match.group(1))
                    break
                except:
                    pass
        if amount > 0:
            break
    
    return date, description, amount


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.reply_text("🔍 Analyzing receipt image...")
        
        photo = update.message.photo[-1]
        file_id = photo.file_id
        
        photo_file = await context.bot.get_file(file_id)
        photo_bytes = await photo_file.download_as_bytearray()
        
        if not vision_client:
            await update.message.reply_text("❌ OCR not available. Vision API not initialized.")
            return
        
        image = vision.Image(content=bytes(photo_bytes))
        
        response = await asyncio.to_thread(
            vision_client.text_detection,
            image=image
        )
        
        if response.error.message:
            raise Exception(f"Vision API error: {response.error.message}")
        
        if not response.text_annotations:
            await update.message.reply_text("❌ No text found in the image.")
            return
        
        detected_text = response.text_annotations[0].description
        
        print(f"Detected text:\n{detected_text}", flush=True)
        
        date, description, amount = extract_receipt_info(detected_text)
        
        row_data = [date, description, str(amount), file_id]
        
        print(f"Saving receipt: Date={date}, Description={description}, Amount={amount}, FileID={file_id}", flush=True)
        await asyncio.to_thread(sheet.append_row, row_data)
        
        await update.message.reply_text(
            f"✅ Receipt saved!\n\n"
            f"📅 Date: {date}\n"
            f"🏪 Restaurant: {description}\n"
            f"💰 Amount: ${amount}"
        )
            
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
