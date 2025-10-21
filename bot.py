import os
import datetime
import json
import asyncio
import requests
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

OCR_API_KEY = os.environ.get('OCR_SPACE_API_KEY', 'helloworld')
print("✅ Using OCR.Space for free receipt OCR")


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


async def extract_amount_from_text(ocr_text):
    import re
    lines = ocr_text.split('\n')
    
    total_patterns = [
        r'total[:\s]*\$?\s*(\d+[.,]\d{2})',
        r'amount[:\s]*\$?\s*(\d+[.,]\d{2})',
        r'grand\s*total[:\s]*\$?\s*(\d+[.,]\d{2})',
        r'balance[:\s]*\$?\s*(\d+[.,]\d{2})',
        r'\$\s*(\d+[.,]\d{2})\s*$'
    ]
    
    for line in reversed(lines):
        line_lower = line.lower().strip()
        for pattern in total_patterns:
            match = re.search(pattern, line_lower)
            if match:
                amount_str = match.group(1).replace(',', '.')
                try:
                    return float(amount_str)
                except ValueError:
                    continue
    
    all_amounts = re.findall(r'\$?\s*(\d+[.,]\d{2})', ocr_text)
    if all_amounts:
        try:
            return max([float(amt.replace(',', '.')) for amt in all_amounts])
        except ValueError:
            pass
    
    return 0.0

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.reply_text("🔍 Analyzing receipt image...")
        
        photo = update.message.photo[-1]
        file_id = photo.file_id
        
        photo_file = await context.bot.get_file(file_id)
        file_url = photo_file.file_path
        
        def ocr_image(url):
            api_url = 'https://api.ocr.space/parse/image'
            payload = {
                'apikey': OCR_API_KEY,
                'url': url,
                'language': 'eng',
                'isOverlayRequired': False
            }
            response = requests.post(api_url, data=payload)
            result = response.json()
            
            if result.get('IsErroredOnProcessing'):
                return None
            
            if result.get('ParsedResults'):
                return result['ParsedResults'][0]['ParsedText']
            return None
        
        ocr_text = await asyncio.to_thread(ocr_image, file_url)
        
        if not ocr_text:
            await update.message.reply_text("❌ Could not read text from image. Please try again.")
            return
        
        print(f"OCR extracted text: {ocr_text[:200]}", flush=True)
        
        amount = await extract_amount_from_text(ocr_text)
        
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
