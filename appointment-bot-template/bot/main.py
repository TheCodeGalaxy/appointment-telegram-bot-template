from __future__ import annotations

import logging

from telegram.ext import ApplicationBuilder
from datetime import time

from bot.config import settings, app_timezone
from bot.database.connection import init_db
from bot.services.retention_service import run_daily_retention_job
from bot.handlers.admin_panel import (
    admin_menu_handler,
    cancel_booking_handler,
    import_services_handler,
    view_bookings_handler,
)
from bot.handlers.common import (
    cancel_handler,
    help_handler,
    start_handler,
    view_appointments_handler,
)
from bot.handlers.user_booking import conversation_handler

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def on_startup(application) -> None:
    logger.info("Bot is starting up...")
    await init_db()
    logger.info("Database initialized.")

    if application.job_queue is not None:
        application.job_queue.run_daily(
            run_daily_retention_job,
            time=time(hour=0, minute=0),
            days=(0, 1, 2, 3, 4, 5, 6),
            tz=app_timezone(),
            name="retention_purge",
        )
        logger.info("Registered daily retention purge job.")


async def on_shutdown(application) -> None:
    logger.info("Bot is shutting down...")


def main() -> None:
    application = (
        ApplicationBuilder()
        .token(settings.bot_token)
        .post_init(on_startup)
        .post_shutdown(on_shutdown)
        .build()
    )

    # Conversation handler (FSM) - must be registered first
    application.add_handler(conversation_handler)

    # Admin handlers
    application.add_handler(admin_menu_handler)
    application.add_handler(view_bookings_handler)
    application.add_handler(cancel_booking_handler)
    application.add_handler(import_services_handler)

    # Core command handlers
    application.add_handler(start_handler)
    application.add_handler(help_handler)
    application.add_handler(cancel_handler)

    # Callback handlers
    application.add_handler(view_appointments_handler)

    logger.info("Bot is running...")

    try:
        application.run_polling()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
        raise


if __name__ == "__main__":
    main()

__all__ = [
    "main",
    "on_startup",
    "on_shutdown",
]
