# Jaryq Dybys Bot

A Telegram bot for subscription management.

## Installation

1. Install Python 3.8+
2. Install Tesseract OCR:
   - Windows: https://github.com/UB-Mannheim/tesseract/wiki
   - Linux: `sudo apt install tesseract-ocr`
   - Mac: `brew install tesseract`

2.1. Install additional language packs for OCR:
   1. Download the following trained data files:
      - Kazakh: [kaz.traineddata](https://github.com/tesseract-ocr/tessdata/raw/main/kaz.traineddata)
      - Russian: [rus.traineddata](https://github.com/tesseract-ocr/tessdata/raw/main/rus.traineddata)
   2. Copy these files to Tesseract's tessdata directory:
      - Windows: `C:\Program Files\Tesseract-OCR\tessdata`
      - Linux: `/usr/share/tesseract-ocr/4.00/tessdata`
      - Mac: `/usr/local/share/tessdata`

3. Install required packages:
```bash
pip install -r requirements.txt
```

4. Configure the `.env` file:
```
BOT_TOKEN=your_bot_token
CHAT_ID=your_chat_id
TESSERACT_PATH=C:\\Program Files\\Tesseract-OCR\\tesseract.exe

KASPI_CARD_NUMBER=your_card_number
RECIPIENT_NAME=your_name
ONE_MONTH_PRICE=350
UNLIMITED_PRICE=3500
MANAGER_TELEGRAM='@manager_username'
```

## Running

```bash
python jaryq_bot.py
```

## Features

- Subscription types: 1 month (350₸) and unlimited (3500₸)
- Automatic Kaspi receipt verification
- Automatic chat membership management
- Subscription storage in SQLite database

## Developers
[Қуаныш](https://t.me/Joy_designer)
[Дәуіт Сұраған](https://t.me/david667s)