# Telegram Expense Tracker Bot

## Overview
A Python Telegram bot that connects to Google Sheets for automatic expense tracking. Users can send text messages with expense details (e.g., "Lunch 12.50") or photo receipts, and the bot logs them to a Google Sheet with timestamps.

## Features
- Text-based expense logging (description + amount)
- Photo receipt handling with file ID storage
- Automatic date stamping
- Real-time confirmation messages
- Google Sheets integration for data persistence
- Async operations to prevent blocking

## Architecture
- **bot.py**: Main bot application with Telegram handlers and Google Sheets integration
- **requirements.txt**: Python dependencies (python-telegram-bot, gspread, google-auth)
- Uses gspread library with service account authentication for Google Sheets

## Setup Requirements
1. **Telegram Bot Token**: Obtain from @BotFather on Telegram
2. **Google Sheets Service Account**: Create in Google Cloud Console with Sheets API enabled
3. **Google Sheet ID**: The spreadsheet ID from the URL where expenses will be logged
4. **Share Sheet**: Share the Google Sheet with the service account email (from credentials JSON) with Editor access

## Environment Variables
- `BOT_TOKEN`: Telegram bot token from BotFather
- `GOOGLE_SHEETS_CREDENTIALS`: JSON service account credentials
- `SHEET_ID`: Google Sheet ID from the spreadsheet URL

## Important Setup Note
The Google Cloud project associated with your service account credentials MUST have the Google Sheets API enabled. Visit:
https://console.developers.google.com/apis/api/sheets.googleapis.com/overview?project=YOUR_PROJECT_ID

Replace YOUR_PROJECT_ID with the project ID from your service account credentials.

## Recent Changes
- 2025-10-21: Initial project setup with Python 3.11
- 2025-10-21: Created bot.py with expense tracking and receipt photo handling
- 2025-10-21: Installed dependencies (python-telegram-bot, gspread, google-auth)
- 2025-10-21: Improved error handling and validation
- 2025-10-21: Changed to use SHEET_ID instead of SHEET_NAME to avoid Drive API requirement
- 2025-10-21: Added async operations with asyncio.to_thread to prevent event loop blocking
- 2025-10-21: Fixed photo handling to store file_id instead of file_path
