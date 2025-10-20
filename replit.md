# Telegram Expense Tracker Bot

## Overview
A Python Telegram bot that connects to Google Sheets for automatic expense tracking. Users can send text messages with expense details (e.g., "Lunch 12.50") or photo receipts, and the bot logs them to a Google Sheet with timestamps.

## Features
- Text-based expense logging (description + amount)
- Photo receipt handling with URL storage
- Automatic date stamping
- Real-time confirmation messages
- Google Sheets integration for data persistence

## Architecture
- **bot.py**: Main bot application with Telegram handlers and Google Sheets integration
- **requirements.txt**: Python dependencies (python-telegram-bot, gspread, google-auth)
- Uses gspread library with service account authentication for Google Sheets

## Setup Requirements
1. **Telegram Bot Token**: Obtain from @BotFather on Telegram
2. **Google Sheets Service Account**: Create in Google Cloud Console with Sheets API enabled
3. **Google Sheet Name**: The spreadsheet where expenses will be logged (share with service account email)

## Environment Variables
- `BOT_TOKEN`: Telegram bot token from BotFather
- `GOOGLE_SHEETS_CREDENTIALS`: JSON service account credentials
- `SHEET_NAME`: Name of the Google Sheet (default: "Expenses")

## Recent Changes
- 2025-10-20: Initial project setup with Python 3.11
- 2025-10-20: Created bot.py with expense tracking and receipt photo handling
- 2025-10-20: Installed dependencies (python-telegram-bot, gspread, google-auth)
