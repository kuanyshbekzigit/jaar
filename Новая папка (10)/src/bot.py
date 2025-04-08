import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from database import Database
from ocr_handler import OCRHandler
import os

# Set console encoding to UTF-8
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Логгер инициализациясы
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Конфигурацияны тікелей орнату
os.environ['BOT_TOKEN'] = '7711781091:AAHAO6a3CnbH8LfZ3HIOD0DyxhHvZKniPXA'
os.environ['CHANNEL_ID'] = '-1002273910123'

# Бот инициализациясы
print("Бот инициализациясы...")
bot = Bot(token=os.environ['BOT_TOKEN'])
dp = Dispatcher()
db = Database('database/users.db')
ocr = OCRHandler()
CHANNEL_ID = int(os.environ['CHANNEL_ID'])
print("Бот инициализациясы сәтті аяқталды")

# Арнаға шақыру сілтемесін жасау
async def create_invite_link(user_id: int) -> str:
    try:
        # Жаңа шақыру сілтемесін жасау
        invite_link = await bot.create_chat_invite_link(
            chat_id=CHANNEL_ID,
            member_limit=1,
            expire_date=0  # Мәңгілік сілтеме
        )
        return invite_link.invite_link
    except Exception as e:
        logger.error(f"Шақыру сілтемесін жасау қатесі: {e}")
        return None

# Арнадан шығару
async def remove_from_channel(user_id: int):
    try:
        # Пайдаланушыны арнадан шығару
        await bot.ban_chat_member(
            chat_id=CHANNEL_ID,
            user_id=user_id
        )
        # Бұғаттауды алып тастау (пайдаланушы қайта қосыла алады)
        await bot.unban_chat_member(
            chat_id=CHANNEL_ID,
            user_id=user_id
        )
        return True
    except Exception as e:
        logger.error(f"Арнадан шығару қатесі: {e}")
        return False

# Мерзімі біткен жазылымдарды тексеру
async def check_expired_subscriptions():
    while True:
        try:
            # Мерзімі біткен жазылымдарды алу
            expired = db.get_expired_subscriptions()
            
            for user_id, invite_link in expired:
                # Жазылымды өшіру
                db.deactivate_subscription(user_id)
                
                # Пайдаланушыны арнадан шығару
                await remove_from_channel(user_id)
                
                # Пайдаланушыға хабарлама жіберу
                try:
                    await bot.send_message(
                        user_id,
                        "Сіздің жазылым мерзіміңіз аяқталды. Жазылымды жаңарту үшін /start командасын жіберіңіз."
                    )
                except:
                    pass
                
        except Exception as e:
            logger.error(f"Мерзімі біткен жазылымдарды тексеру қатесі: {e}")
        
        # Әр 1 сағат сайын тексеру
        await asyncio.sleep(3600)

# Батырмалар
def get_tariff_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="1 ай – 350₸", callback_data="tariff:one_month")],
        [InlineKeyboardButton(text="Шексіз – 3500₸", callback_data="tariff:unlimited")],
    ])
    return keyboard

def get_payment_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Артқа", callback_data="back_to_tariffs")]
    ])
    return keyboard

# Старт командасы
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    try:
        db.add_user(message.from_user.id, message.from_user.username)
        
        await message.answer(
            "🎬 Сәлеметсіз! Jaryq Dybys арнасына қош келдіңіз!\n\n"
            "Бұл бот – Jaryq Dybys арнасына жазылуды басқаруға арналған ресми Telegram-бот.\n\n"
            "🎯 Jaryq Dybys – жапон анимелерін қазақ тіліне дыбыстайтын ерікті топ.\n"
            "Арнада сіз таба аласыз:\n"
            "- Танымал анимелердің қазақша дубляжы\n"
            "- Эксклюзивті аудармалар\n"
            "- Жаңа шыққан анимелердің аудармасы\n\n"
            "Жазылым түрін таңдаңыз:",
            reply_markup=get_tariff_keyboard()
        )
    except Exception as e:
        print(f"Старт командасы қатесі: {e}")
        logger.error(f"Старт командасы қатесі: {e}")
        await message.answer("Қате орын алды. Қайтадан /start командасын жіберіңіз.")

# Тариф таңдау
@dp.callback_query(lambda c: c.data.startswith('tariff:'))
async def process_tariff_selection(callback_query: CallbackQuery):
    try:
        tariff = callback_query.data.split(':')[1]
        
        if tariff == "one_month":
            message_text = (
                "Сіз 1 айлық тарифін таңдадыңыз.\n\n"
                "🎬 Бұл тарифке кіреді:\n"
                "- 1 ай бойы арнаға толық қолжетімділік\n"
                "- Барлық дубляждарды көру мүмкіндігі\n"
                "- Жаңа аудармалар шыққан кезде хабарландыру\n\n"
                "💳 Төлем жасау үшін:\n"
                "Kaspi Gold: 4400 4302 2052 7011\n"
                "Алушы: Нұрсұлтан С\n"
                "Сома: 350₸\n\n"
                "📝 Төлем жасағаннан кейін чекті PDF форматында немесе сурет түрінде жіберіңіз."
            )
        elif tariff == "unlimited":
            message_text = (
                "Сіз ШЕКСІЗ тарифін таңдадыңыз.\n\n"
                "🎬 Бұл тарифке кіреді:\n"
                "- Шексіз мерзімге арнаға толық қолжетімділік\n"
                "- Барлық дубляждарды көру мүмкіндігі\n"
                "- Жаңа аудармалар шыққан кезде хабарландыру\n"
                "- VIP қолдау\n"
                "- Жаңа аниме аударма сұраныстарын жіберу мүмкіндігі\n\n"
                "💳 Төлем жасау үшін:\n"
                "Kaspi Gold: 4400 4302 2052 7011\n"
                "Алушы: Нұрсұлтан С\n"
                "Сома: 3500₸\n\n"
                "📝 Төлем жасағаннан кейін чекті PDF форматында немесе сурет түрінде жіберіңіз."
            )
        else:
            await bot.answer_callback_query(callback_query.id, text="Қате тариф таңдалды")
            return
        
        await bot.edit_message_text(
            message_text,
            callback_query.message.chat.id,
            callback_query.message.message_id,
            reply_markup=get_payment_keyboard()
        )
    except Exception as e:
        print(f"Тариф таңдау қатесі: {e}")
        logger.error(f"Тариф таңдау қатесі: {e}")
        await bot.send_message(callback_query.message.chat.id, "Қате орын алды. Қайтадан /start командасын жіберіңіз.")

# Артқа қайту
@dp.callback_query(lambda c: c.data == "back_to_tariffs")
async def process_back_to_tariffs(callback_query: CallbackQuery):
    try:
        await bot.edit_message_text(
            "Жазылым түрін таңдаңыз:",
            callback_query.message.chat.id,
            callback_query.message.message_id,
            reply_markup=get_tariff_keyboard()
        )
    except Exception as e:
        print(f"Артқа қайту қатесі: {e}")
        logger.error(f"Артқа қайту қатесі: {e}")

# Чекті өңдеу
@dp.message(lambda message: message.content_type in [types.ContentType.PHOTO, types.ContentType.DOCUMENT])
async def process_check(message: types.Message):
    try:
        # Файлды жүктеу
        file_path = None
        if message.content_type == types.ContentType.PHOTO:
            # Фотоны жүктеу
            photo = message.photo[-1]
            file = await bot.get_file(photo.file_id)
            file_path = file.file_path
            
            # Файлды жүктеу
            downloaded_file = await bot.download_file(file_path)
            
        elif message.content_type == types.ContentType.DOCUMENT:
            # Құжатты тексеру (PDF)
            if not message.document.mime_type == "application/pdf":
                await message.answer("Тек PDF форматындағы файлдар қабылданады.")
                return
                
            # Файлды жүктеу
            file = await bot.get_file(message.document.file_id)
            file_path = file.file_path
            downloaded_file = await bot.download_file(file_path)
        
        # OCR өңдеу
        result = await ocr.process_file(downloaded_file, file_path)
        
        # Чекті тексеру
        is_valid, status = ocr.validate_check(result)
        
        if is_valid:
            # Төлемді өңдеу
            await process_payment(message, 350 if status == "one_month" else 3500, message.from_user.id)
        else:
            await message.answer(
                f"Чек расталмады: {status}\n"
                "Қайтадан көріңіз немесе әкімшіге хабарласыңыз.",
                reply_markup=get_payment_keyboard()
            )
            
    except Exception as e:
        print(f"Чекті өңдеу қатесі: {e}")
        logger.error(f"Чекті өңдеу қатесі: {e}")
        await message.answer("Чекті өңдеу кезінде қате орын алды. Қайтадан көріңіз.")

async def main():
    print("Бот басталуда...")
    
    # Мерзімі біткен жазылымдарды тексеру тапсырмасын қосу
    asyncio.create_task(check_expired_subscriptions())
    
    print("Бот іске қосылуда...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())