# Telegram Expense Tracker Bot

## Overview
A Python Telegram bot that connects to Google Sheets for automatic expense tracking. Users can send text messages with expense details (e.g., "Lunch 12.50") or photo receipts, and the bot logs them to a Google Sheet with timestamps. Receipt photos are automatically analyzed using Google Cloud Vision OCR to extract the date, restaurant name, and total amount.

## Features
- Text-based expense logging (description + amount)
- Photo receipt OCR with automatic extraction of:
  - Date (from receipt)
  - Restaurant/vendor name (from receipt header)
  - Total amount (from receipt)
- Automatic date stamping
- Real-time confirmation messages
- Google Sheets integration for data persistence
- Async operations to prevent blocking

## Architecture
- **bot.py**: Main bot application with Telegram handlers, Google Sheets integration, and Vision OCR
- **requirements.txt**: Python dependencies (python-telegram-bot, gspread, google-auth, google-cloud-vision)
- Uses gspread library with service account authentication for Google Sheets
- Uses Google Cloud Vision API for receipt OCR

## Setup Requirements
1. **Telegram Bot Token**: Obtain from @BotFather on Telegram
2. **Google Cloud Service Account**: Create in Google Cloud Console with both:
   - Google Sheets API enabled
   - Cloud Vision API enabled
3. **Google Sheet ID**: The spreadsheet ID from the URL where expenses will be logged
4. **Share Sheet**: Share the Google Sheet with the service account email (from credentials JSON) with Editor access

## Environment Variables
- `BOT_TOKEN`: Telegram bot token from BotFather
- `GOOGLE_SHEETS_CREDENTIALS`: JSON service account credentials (used for both Sheets and Vision APIs)
- `SHEET_ID`: Google Sheet ID from the spreadsheet URL

## Google Sheet Structure
The bot saves data in the following format:
- Column A: Date (YYYY-MM-DD)
- Column B: Description (restaurant/vendor name or manual entry)
- Column C: Amount (numerical value)
- Column D: Image URL/File ID (for receipt photos)

## Important Setup Note
The Google Cloud project associated with your service account credentials MUST have these APIs enabled:
- Google Sheets API: https://console.developers.google.com/apis/api/sheets.googleapis.com/overview
- Cloud Vision API: https://console.developers.google.com/apis/api/vision.googleapis.com/overview

The same service account is used for both APIs, making setup simple and secure.

## Recent Changes
- 2025-10-21: Initial project setup with Python 3.11
- 2025-10-21: Created bot.py with expense tracking and receipt photo handling
- 2025-10-21: Installed dependencies (python-telegram-bot, gspread, google-auth)
- 2025-10-21: Improved error handling and validation
- 2025-10-21: Changed to use SHEET_ID instead of SHEET_NAME to avoid Drive API requirement
- 2025-10-21: Added async operations with asyncio.to_thread to prevent event loop blocking
- 2025-10-21: Fixed photo handling to store file_id instead of file_path
- 2025-10-21: Added Google Cloud Vision OCR for automatic receipt data extraction
- 2025-10-21: Replaced OpenAI Vision API with Google Cloud Vision API
- 2025-10-21: Implemented intelligent text parsing to extract date, restaurant name, and amount from receipts

## User Preferences
- Using Google Cloud Vision API for OCR (not OpenAI)
- Single service account for both Sheets and Vision APIs
- Receipt OCR extracts: date, restaurant name, and total amount
