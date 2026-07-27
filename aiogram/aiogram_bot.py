"""
Telegram MagicLink Bot
Listens to Kafka topic 'magiclink' and forwards links to users by TG ID.
"""

import asyncio
import json
import logging
from typing import Any
from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.types import Message
from aiogram.filters import Command
from faststream import FastStream
from faststream.kafka import KafkaBroker
from config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Config
BOT_TOKEN = settings.BOT_TOKEN
KAFKA_BOOTSTRAP_SERVERS = settings.KAFKA_BOOTSTRAP_SERVERS
PROXY_URL = settings.PROXY_URL

session = AiohttpSession(proxy=PROXY_URL)
bot = Bot(token=BOT_TOKEN, session=session)
dp = Dispatcher()

# FastStream Broker and App for Kafka
broker = KafkaBroker(KAFKA_BOOTSTRAP_SERVERS)
app = FastStream(broker)

@dp.message(Command("start"))
async def cmd_start(message: Message) -> None:
    """Handle /start command - sends greeting and user's TG ID."""
    await message.answer(
        f"Привет, {message.from_user.full_name}!\n\n"
        f"Ваш Telegram ID: <code>{message.from_user.id}</code>\n\n"
        f"Отправьте этот ID в Kafka topic, чтобы получить ссылку."
    )


@broker.subscriber("magiclink", group_id="aiogram_bot_group", auto_offset_reset="earliest")
async def handle_magiclink(payload_str: str) -> None:
    """Handles messages from the 'magiclink' topic using FastStream."""
    # FastStream получает строку. Мы должны вручную декодировать её из JSON,
    # так как продюсер отправляет уже закодированную строку.
    try:
        payload: dict = json.loads(payload_str)

        tg_id = payload.get("tg_id")  # 'email' field contains TG ID
        link = payload.get("link")  # 'link' field contains the link

        if tg_id is None or link is None:
            logger.warning("Missing 'email' or 'link' field in Kafka message: %s", payload)
            return

        tg_id_int = int(tg_id)
        await bot.send_message(tg_id_int, text=f"Ссылка: {link}")
        logger.info("Sent link to TG ID %s: %s", tg_id_int, link)

    except (ValueError, KeyError, TypeError) as exc:
        logger.error("Error processing Kafka message payload: %s. Payload: %s", exc, payload)
    except Exception as exc:
        logger.error("An unexpected error occurred while sending message to TG: %s", exc, exc_info=True)


async def run_kafka_consumer() -> None:
    """Starts the FastStream application."""
    logger.info("Starting FastStream Kafka consumer...")
    await app.run()

async def run_bot() -> None:
    """Run the bot with polling."""
    # Запускаем aiogram и FastStream параллельно
    await asyncio.gather(
        dp.start_polling(bot),
        run_kafka_consumer()
    )


def run() -> None:
    """Entry point."""
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as exc:
        logger.error("Fatal error: %s", exc)


if __name__ == "__main__":
    run()