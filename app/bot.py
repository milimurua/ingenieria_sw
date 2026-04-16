from __future__ import annotations

import logging

from telegram.ext import ApplicationBuilder

from app.config import settings
from app.db import ensure_database
from app.handlers.commands import build_handlers
from app.services.allocation import rebalance_staff
from app.services.seed import seed_data

logging.basicConfig(
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def main() -> None:
    if not settings.telegram_bot_token:
        raise RuntimeError(
            'Falta TELEGRAM_BOT_TOKEN. Copiá .env.example a .env y completá el token del bot.'
        )

    ensure_database()
    seed_data()
    rebalance_staff()

    application = ApplicationBuilder().token(settings.telegram_bot_token).build()

    for handler in build_handlers():
        application.add_handler(handler)

    logger.info('Bot SAMUR iniciado.')
    application.run_polling(drop_pending_updates=True)
