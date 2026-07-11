"""
Telegram MagicLink Bot
Listens to Kafka topic 'magiclink' and forwards links to users by TG ID.
"""

import asyncio
import json
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.types import Message
from aiogram.filters import Command
from aiokafka import AIOKafkaConsumer
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Config
BOT_TOKEN = os.getenv("BOT_TOKEN", "7831581649:AAG_zDN4211n6UR3GHC0sMZAN-Du7Pi6erQ")
KAFKA_BOOTSTRAP_SERVERS = os.getenv(
    "KAFKA_BOOTSTRAP_SERVERS", "kafka:29092"
).split(",")
PROXY_URL = os.getenv("PROXY_URL", "http://127.0.0.1:10808")
session = AiohttpSession(proxy="http://127.0.0.1:10808")
bot = Bot(token="7831581649:AAG_zDN4211n6UR3GHC0sMZAN-Du7Pi6erQ")
dp = Dispatcher()
# Global bot instance for Kafka consumer
# _bot: Bot = None


async def cmd_start(message: Message) -> None:
    """Handle /start command - sends greeting and user's TG ID."""
    await message.answer(
        f"Привет, {message.from_user.full_name}!\n\n"
        f"Ваш Telegram ID: <code>{message.from_user.id}</code>\n\n"
        f"Отправьте этот ID в Kafka topic, чтобы получить ссылку."
    )


async def consume_kafka(bot: Bot) -> None:
    """Consume messages from 'magiclink' Kafka topic and send links to TG users."""
    consumer = AIOKafkaConsumer(
        "magiclink",
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
    )
    
    await consumer.start()
    logger.info("Kafka consumer started for topic 'magiclink'")

    try:
        async for msg in consumer:
            try:
                payload = msg.value
                payload = json.loads(payload)
                tg_id = payload.get("email")  # 'email' field contains TG ID
                link = payload.get("link")    # 'link' field contains the link

                if tg_id is None or link is None:
                    logger.warning(
                        "Missing 'email' or 'link' field in Kafka message: %s",
                        payload,
                    )
                    continue

                tg_id_int = int(tg_id)
                await bot.send_message(tg_id_int, text=f"Ссылка: {link}")
                logger.info("Sent link to TG ID %s: %s", tg_id_int, link)

            except (ValueError, KeyError) as exc:
                logger.error("Error processing Kafka message: %s", exc)
            except Exception as exc:
                logger.error("Error sending message to TG: %s", exc)
    finally:
        await consumer.stop()
        logger.info("Kafka consumer stopped")


async def on_startup(bot: Bot) -> None:
    """Startup Kafka consumer."""
    asyncio.create_task(consume_kafka(bot))
    logger.info("Kafka consumer started")


async def on_shutdown(bot: Bot) -> None:
    """Shutdown bot."""
    await bot.session.close()
    logger.info("Bot shutdown complete")


async def run_bot() -> None:
    """Run the bot with polling."""
    
    # _bot = bot

    dp.message(cmd_start)(Command("start"))

    await on_startup(bot)

    logger.info("Bot is starting...")
    await bot.delete_webhook(drop_pending_updates=True)

    try:
        await dp.start_polling(bot)
    finally:
        await on_shutdown(bot)


def run() -> None:
    """Entry point."""
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as exc:
        logger.error("Fatal error: %s", exc)


if __name__ == "__main__":
    run()