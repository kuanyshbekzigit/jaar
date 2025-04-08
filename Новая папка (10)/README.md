# Jaryq Dybys Bot

Telegram бот жазылымды басқаруға арналған.

## Орнату

1. Python 3.8+ орнатыңыз
2. Tesseract OCR орнатыңыз:
   - Windows: https://github.com/UB-Mannheim/tesseract/wiki
   - Linux: `sudo apt install tesseract-ocr`
   - Mac: `brew install tesseract`

3. Қажетті пакеттерді орнатыңыз:
```bash
pip install -r requirements.txt
```

4. `.env` файлын конфигурациялаңыз:
```
BOT_TOKEN=your_bot_token
CHAT_ID=your_chat_id
KASPI_CARD_NUMBER=your_card_number
KASPI_PHONE=your_phone
RECIPIENT_NAME=your_name
ONE_MONTH_PRICE=350
UNLIMITED_PRICE=3500
TESSERACT_PATH=C:/Program Files/Tesseract-OCR/tesseract.exe
```

## Іске қосу

```bash
python src/bot.py
```

## Мүмкіндіктері

- Жазылым түрлері: 1 ай (350₸) және шексіз (3500₸)
- Kaspi чектерін автоматты тексеру
- Чат мүшелігін автоматты басқару
- SQLite дерекқорында жазылымдарды сақтау 