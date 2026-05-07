import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str = os.getenv('TELEGRAM_BOT_TOKEN', '')

    mysql_host: str = os.getenv('MYSQL_HOST', 'localhost')
    mysql_port: int = int(os.getenv('MYSQL_PORT', 3306))
    mysql_user: str = os.getenv('MYSQL_USER', 'root')
    mysql_password: str = os.getenv('MYSQL_PASSWORD', '')
    mysql_database: str = os.getenv('MYSQL_DATABASE', 'samur_bot')

    timezone: str = os.getenv('TIMEZONE', 'Europe/Madrid')

settings = Settings()