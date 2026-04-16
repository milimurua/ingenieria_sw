import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str = os.getenv('TELEGRAM_BOT_TOKEN', '')
    db_path: str = os.getenv('SAMUR_DB_PATH', 'data/samur_telegram.db')
    timezone: str = os.getenv('TIMEZONE', 'Europe/Madrid')

settings = Settings()
