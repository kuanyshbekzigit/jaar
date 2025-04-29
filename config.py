import os
from aiogram import Bot, Dispatcher, types
from module.database import Database
from dotenv import load_dotenv

load_dotenv()

# Bot main configuration
CHANNEL_NAME = os.getenv('CHANNEL_NAME')
CHANNEL_ID = os.getenv('CHANNEL_ID')
CHAT_ID = os.getenv('CHAT_ID')
TOKEN = os.getenv('TOKEN')

# OCR configuration
TESSERACT_PATH = os.getenv('TESSERACT_PATH')

# Payment configuration
KASPI_CARD_NUMBER = os.getenv('KASPI_CARD_NUMBER')
KASPI_PHONE = os.getenv('KASPI_PHONE')
RECIPIENT_NAME = os.getenv('RECIPIENT_NAME')
ONE_MONTH_PRICE = float(os.getenv('ONE_MONTH_PRICE', 350))
UNLIMITED_PRICE = float(os.getenv('UNLIMITED_PRICE', 3500))

# Manager contacts
MANAGER_TELEGRAM = os.getenv('MANAGER_TELEGRAM')

# Initialize objects
bot = Bot(token=TOKEN)
dp = Dispatcher()

# File storage directory
pdf_path = 'tmp'
if not os.path.exists(pdf_path):
    os.makedirs(pdf_path)

# Database and OCR initialization
db = Database('database/users.db')

HANDLER_MSG = {
    'start': 'Сәлем! Мен Kaspi чектерін тексеретін ботпын. Чекті жүктеп, мені тексеруге жіберіңіз.',
    'info': ("ℹ️ Jaryq Dybys жобасы туралы:\n\n"
            "🎬 Біз – қазақ тілінде аниме дубляждайтын ерікті топ.\n\n"
            "Біздің жетістіктеріміз:\n"
            "✅ 50+ аниме дубляждалған\n"
            "✅ 1000+ белсенді жазылушы\n"
            "✅ Жоғары сапалы дубляж\n\n"
            "Жазылым артықшылықтары:\n"
            "🔸 Барлық дубляждарға қолжетімділік\n"
            "🔸 Жаңа шығарылымдар туралы хабарландырулар\n"
            "🔸 Эксклюзивті контент\n\n"
            f"Ботты жасаған: @david667s және @Joy_designer"),
}

TARRIF_MSG= {
    'one_month': (
                "Сіз 1 айлық тарифін таңдадыңыз.\n\n"
                "🎬 Бұл тарифке кіреді:\n"
                "- 1 ай бойы арнаға толық қолжетімділік\n"
                "- Барлық дубляждарды көру мүмкіндігі\n"
                "- Жаңа аудармалар шыққан кезде хабарландыру\n\n"
                "💳 Төлем жасау үшін:\n"
                f"Kaspi Gold: {KASPI_CARD_NUMBER}\n"
                f"Алушы: {RECIPIENT_NAME}\n"
                "Сома: 350₸\n\n"
                "📝 Төлем жасағаннан кейін түбіртекті тек PDF форматында жіберіңіз."
            ),
    'unlimited':(
                "Сіз ШЕКСІЗ тарифін таңдадыңыз.\n\n"
                "🎬 Бұл тарифке кіреді:\n"
                "- Шексіз мерзімге арнаға толық қолжетімділік\n"
                "- Барлық дубляждарды көру мүмкіндігі\n"
                "- Жаңа аудармалар шыққан кезде хабарландыру\n"
                "- VIP қолдау\n"
                "- Жаңа аниме аударма сұраныстарын жіберу мүмкіндігі\n\n"
                "💳 Төлем жасау үшін:\n"
                f"Kaspi Gold: {KASPI_CARD_NUMBER}\n"
                f"Алушы: {RECIPIENT_NAME}\n"
                "Сома: 3500₸\n\n"
                "📝 Төлем жасағаннан кейін түбіртекті тек PDF форматында жіберіңіз."
            )
}
