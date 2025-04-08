import sqlite3
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_file):
        self.db_file = db_file
        self.create_tables()

    def create_tables(self):
        try:
            conn = sqlite3.connect(self.db_file)
            c = conn.cursor()
            
            # Пайдаланушылар кестесі
            c.execute('''CREATE TABLE IF NOT EXISTS users
                        (user_id INTEGER PRIMARY KEY,
                         username TEXT,
                         subscription_type TEXT,
                         subscription_start TIMESTAMP,
                         subscription_end TIMESTAMP,
                         invite_link TEXT,
                         is_active BOOLEAN DEFAULT 0)''')
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Кесте жасау қатесі: {e}")

    def add_user(self, user_id: int, username: str):
        try:
            conn = sqlite3.connect(self.db_file)
            c = conn.cursor()
            c.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)",
                     (user_id, username))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Пайдаланушы қосу қатесі: {e}")

    def set_subscription(self, user_id: int, subscription_type: str, invite_link: str):
        try:
            conn = sqlite3.connect(self.db_file)
            c = conn.cursor()
            
            now = datetime.now()
            if subscription_type == "one_month":
                end_date = now + timedelta(days=30)
            else:  # unlimited
                end_date = now + timedelta(years=100)  # Шексіз мерзім үшін

            c.execute("""UPDATE users 
                        SET subscription_type = ?,
                            subscription_start = ?,
                            subscription_end = ?,
                            invite_link = ?,
                            is_active = 1
                        WHERE user_id = ?""",
                     (subscription_type, now, end_date, invite_link, user_id))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Жазылым орнату қатесі: {e}")
            return False

    def deactivate_subscription(self, user_id: int):
        try:
            conn = sqlite3.connect(self.db_file)
            c = conn.cursor()
            
            c.execute("""UPDATE users 
                        SET is_active = 0
                        WHERE user_id = ?""",
                     (user_id,))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Жазылымды өшіру қатесі: {e}")
            return False

    def get_expired_subscriptions(self):
        try:
            conn = sqlite3.connect(self.db_file)
            c = conn.cursor()
            
            now = datetime.now()
            c.execute("""SELECT user_id, invite_link 
                        FROM users 
                        WHERE is_active = 1 
                        AND subscription_end < ?""",
                     (now,))
            
            expired = c.fetchall()
            conn.close()
            return expired
        except Exception as e:
            logger.error(f"Мерзімі біткен жазылымдарды алу қатесі: {e}")
            return []

    def get_user_subscription(self, user_id: int):
        try:
            conn = sqlite3.connect(self.db_file)
            c = conn.cursor()
            
            c.execute("""SELECT subscription_type, subscription_end, invite_link, is_active 
                        FROM users 
                        WHERE user_id = ?""",
                     (user_id,))
            
            result = c.fetchone()
            conn.close()
            return result
        except Exception as e:
            logger.error(f"Пайдаланушы жазылымын алу қатесі: {e}")
            return None