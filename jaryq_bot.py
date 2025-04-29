"""
Jaryq Dybys Bot - Telegram bot for managing anime dubbing channel subscriptions
Handles user registration, payments verification via Kaspi receipts, and subscription management
"""

import asyncio
import logging
import sys
import os
import tempfile
from aiogram import  types
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

from config import *
from module.ocr_handler import ocr

# Set console encoding for Windows
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Initialize logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_invite_link(user_id: int) -> str:
    """Create one-time invite link for user
    Args:
        user_id: Telegram user ID
    Returns:
        Invite link string or None if failed
    """
    try:
        # Create a new invite link
        invite_link = await bot.create_chat_invite_link(
            chat_id=CHANNEL_ID,
            member_limit=1,
            expire_date=0  # Permanent link
        )
        return invite_link.invite_link
    except Exception as e:
        logger.error(f"Error creating invite link: {e}")
        return None

async def remove_from_channel(user_id: int):
    """Remove user from channel and unban them
    Args:
        user_id: Telegram user ID
    Returns:
        True if successful, False otherwise
    """
    try:
        # Remove user from the channel
        await bot.ban_chat_member(
            chat_id=CHANNEL_ID,
            user_id=user_id
        )
        # Unban user (allow rejoining)
        await bot.unban_chat_member(
            chat_id=CHANNEL_ID,
            user_id=user_id
        )
        return True
    except Exception as e:
        logger.error(f"Error removing user from channel: {e}")
        return False

async def check_expired_subscriptions():
    """Check for expired subscriptions and handle them:
    - Get expired subscriptions from database
    - Remove users from channel
    - Send notifications
    - Update subscription status
    Runs every hour
    """
    while True:
        try:
            # Get expired subscriptions
            expired = db.get_expired_subscriptions()
            
            for user_id, invite_link in expired:
                # Deactivate subscription
                db.deactivate_subscription(user_id)
                
                # Remove user from the channel
                await remove_from_channel(user_id)
                
                # Send notification to user
                try:
                    await bot.send_message(
                        user_id,
                        "Сіздің жазылым мерзіміңіз аяқталды. Жазылымды жаңарту үшін /start командасын жіберіңіз."
                    )
                except:
                    pass
                
        except Exception as e:
            logger.error(f"Error checking expired subscriptions: {e}")
        
        # Check every hour
        await asyncio.sleep(3600)

def get_tariff_keyboard():
    """Create keyboard with subscription options"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="1 ай – 350₸", callback_data="tariff:one_month")],
        [InlineKeyboardButton(text="Шексіз – 3500₸", callback_data="tariff:unlimited")]
    ])
    return keyboard

def get_payment_keyboard():
    """Create keyboard with back button"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Артқа", callback_data="back_to_tariffs")]
    ])
    return keyboard

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Handle /start command:
    - Register new user
    - Show subscription options
    """
    try:
        db.add_user(message.from_user.id, message.from_user.username)
        await message.answer(
            text=HANDLER_MSG['start'],
            reply_markup=get_tariff_keyboard()
        )
    except Exception as e:
        print(f"Старт командасы қатесі: {e}")
        logger.error(f"Старт командасы қатесі: {e}")
        await message.answer("Қате орын алды. Қайтадан /start командасын жіберіңіз.")

@dp.message(Command("info"))
async def cmd_info(message: types.Message):
    """Handle /info command:
    - Show project information
    - Provide subscription and contact options
    """
    try:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💰 Жазылу", callback_data="back_to_tariffs")],
            [InlineKeyboardButton(text="👨‍💼 Менеджермен байланысу", url=f"{MANAGER_TELEGRAM}")]
        ])
        await message.answer(text = HANDLER_MSG['info'], reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Info команда қатесі: {e}")
        await message.answer("Қате орын алды. Қайтадан /info командасын жіберіңіз.")

@dp.callback_query(lambda c: c.data.startswith('tariff:'))
async def process_tariff_selection(callback_query: CallbackQuery):
    """Handle tariff selection:
    - Show payment instructions
    - Display payment details
    """
    try:
        tariff = callback_query.data.split(':')[1]
        
        if tariff == "one_month":
            message_text = TARRIF_MSG['one_month'].format(KASPI_CARD_NUMBER, RECIPIENT_NAME)
        elif tariff == "unlimited":
            message_text = TARRIF_MSG['unlimited'].format(KASPI_CARD_NUMBER, RECIPIENT_NAME)
        else:
            await bot.answer_callback_query(callback_query.id, text="Қате тариф таңдалды")
            return
        
        await bot.edit_message_text(
            text=message_text,
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            reply_markup=get_payment_keyboard()
        )
    except Exception as e:
        print(f"Тариф таңдау қатесі: {e}")
        logger.error(f"Тариф таңдау қатесі: {e}")
        await bot.send_message(callback_query.message.chat.id, "Қате орын алды. Қайтадан /start командасын жіберіңіз.")

@dp.callback_query(lambda c: c.data == "back_to_tariffs")
async def process_back_to_tariffs(callback_query: CallbackQuery):
    """Handle back button - return to tariff selection"""
    try:
        await bot.edit_message_text(
            text="Жазылым түрін таңдаңыз:",
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            reply_markup=get_tariff_keyboard()
        )
    except Exception as e:
        print(f"Артқа қайту қатесі: {e}")
        logger.error(f"Артқа қайту қатесі: {e}")

@dp.callback_query(lambda c: c.data == "info")
async def process_info(callback_query: CallbackQuery):
    """Handle info button - show project information"""
    try:
        info_text = HANDLER_MSG['info']
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="👨‍💼 Менеджермен байланысу", url=f"{MANAGER_TELEGRAM}")],
            [InlineKeyboardButton(text="🔙 Артқа", callback_data="back_to_tariffs")]
        ])
        
        await bot.edit_message_text(
            text=info_text,
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            reply_markup=keyboard
        )
    except Exception as e:
        logger.error(f"Error displaying information: {e}")

@dp.message(lambda message: message.content_type == types.ContentType.DOCUMENT)
async def process_check(message: types.Message):
    """Process Kaspi receipt:
    - Validate PDF file
    - Extract text with OCR
    - Verify payment details
    - Create invite link if valid
    """
    try:
        # Check document type and size
        if not message.document.mime_type == "application/pdf" or message.document.file_size > 204800:
            await message.answer(
                "Тек PDF форматындағы файлдар қабылданады.\n"
                "Файл көлемі 200КБ-тан аспауы керек."
            )
            return

        # Download the document
        file_path = f"temp_{message.document.file_id}.pdf"
        
        # Download the file
        await bot.download(
            message.document,
            destination=file_path
        )

        # Read the PDF file
        with open(file_path, 'rb') as f:
            file_content = f.read()

        # Process the file with OCR
        result = await ocr.process_file(file_content, file_path)
        
        # Remove the temp file
        if os.path.exists(file_path):
            os.remove(file_path)

        # Validate the receipt
        is_valid, status = ocr.validate_check(result)
        
        if is_valid:
            print(f"Receipt validated: {status}")
            # Process payment
            await process_payment(message, 350 if status == "one_month" else 3500, message.from_user.id)
        else:
            await message.answer(
                f"Чек расталмады: {status}\n"
                "Қайтадан көріңіз немесе әкімшіге хабарласыңыз.",
                reply_markup=get_payment_keyboard()
            )
    
    except Exception as e:
        logger.error(f"Error processing receipt: {e}")
        await message.answer("Чекті өңдеу кезінде қате орын алды. Қайтадан көріңіз.")
        # Remove the temp file even if error
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)

async def process_payment(message: Message, amount: int, user_id: int):
    """Process verified payment:
    - Create invite link
    - Set subscription in database
    - Send confirmation to user
    Args:
        message: Telegram message
        amount: Payment amount
        user_id: Telegram user ID
    """
    try:
        # Create a new invite link
        invite_link = await create_invite_link(user_id)
        if not invite_link:
            await message.answer("Шақыру сілтемесін жасау кезінде қате орын алды")
            return

        # Determine subscription type
        subscription_type = "one_month" if amount == 350 else "unlimited"
        
        # Save subscription to database
        if db.set_subscription(user_id, subscription_type, invite_link):
            await message.answer(
                f"✅ Төлем расталды!\n\n"
                f"Арнаға қосылу сілтемесі:\n{invite_link}\n\n"
                "Назар аударыңыз:\n"
                "- Сілтеме тек бір рет қолданылады\n"
                "- Сілтемені басқаларға бермеңіз\n"
                f"- Жазылым мерзімі: {'1 ай' if subscription_type == 'one_month' else 'шексіз'}"
            )
        else:
            await message.answer("Жазылымды сақтау кезінде қате орын алды")
    except Exception as e:
        logger.error(f"Error processing payment: {e}")
        await message.answer("Төлемді өңдеу кезінде қате орын алды")

async def main():
    """Initialize and run the bot:
    - Start subscription checker
    - Start message polling
    """
    print("Бот басталуда...")
    
    # Start periodic subscription check
    asyncio.create_task(check_expired_subscriptions())
    
    print("Бот іске қосылуда...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())