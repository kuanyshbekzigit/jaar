import asyncio
import os
from datetime import datetime
from dotenv import load_dotenv
from aiogram import Bot
from database import Database

# Конфигурацияны жүктеу
load_dotenv('../config/.env')
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

class SubscriptionScheduler:
    def __init__(self):
        self.bot = Bot(token=BOT_TOKEN)
        self.db = Database()
    
    async def check_expiring_subscriptions(self):
        """Аяқталатын жазылымдарды тексеру"""
        expiring_subs = self.db.get_expiring_subscriptions()
        
        for sub in expiring_subs:
            if datetime.now() >= sub.expiry_date:
                # Жазылым мерзімі аяқталған - пайдаланушыны чаттан шығару
                try:
                    # Пайдаланушыны чаттан шығару
                    await self.bot.ban_chat_member(
                        chat_id=CHAT_ID,
                        user_id=sub.user_id,
                        until_date=0
                    )
                    # Бан тізімінен алып тастау (келесі жолы қайта кіре алу үшін)
                    await self.bot.unban_chat_member(
                        chat_id=CHAT_ID,
                        user_id=sub.user_id
                    )
                    self.db.deactivate_subscription(sub.user_id)
                    
                    # Пайдаланушыға хабарлама жіберу
                    await self.bot.send_message(
                        sub.user_id,
                        "Сіздің жазылымыңыз аяқталды.\n"
                        "Жазылымды жаңарту үшін /start командасын жіберіңіз."
                    )
                except Exception as e:
                    print(f"Error removing user {sub.user_id}: {e}")
            else:
                # Ескерту жіберу
                try:
                    await self.bot.send_message(
                        sub.user_id,
                        "Ескерту: Сіздің жазылымыңыз ертең аяқталады.\n"
                        "Жазылымды жаңарту үшін /start командасын жіберіңіз."
                    )
                except Exception as e:
                    print(f"Error sending notification to user {sub.user_id}: {e}")
    
    async def run(self):
        """Жоспарлаушыны іске қосу"""
        while True:
            await self.check_expiring_subscriptions()
            # Әр сағат сайын тексеру
            await asyncio.sleep(3600)

async def main():
    scheduler = SubscriptionScheduler()
    await scheduler.run()

if __name__ == "__main__":
    asyncio.run(main()) 