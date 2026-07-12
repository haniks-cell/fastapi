from aiochclient import ChClient
from aiohttp import ClientSession
from config import settings
from typing import Optional
import logging, asyncio

logger = logging.getLogger(__name__)

class ClickHouseManager:
    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.client: Optional[ChClient] = None
        self.flag: bool = False

    async def connect(self):
        """Создает сессию и клиент для асинхронной работы с ClickHouse."""
        try:
            self.session = ClientSession()
            self.client = ChClient(
                self.session,
                url=f"http://{settings.CLICKHOUSE_HOST}:{settings.CLICKHOUSE_PORT}",
                user=settings.CLICKHOUSE_USER,
                password=settings.CLICKHOUSE_PASSWORD,
                database=settings.CLICKHOUSE_DB,
            )
            if not await self.client.is_alive():
                raise ConnectionError("ClickHouse is not alive.")

            logger.info("Successfully connected to ClickHouse.")
            await self.create_log_table()
        except Exception as e:
            logger.error(f"Failed to connect or setup ClickHouse: {e}")
            self.client = None
            if self.session and not self.session.closed:
                await self.session.close()
        finally:
            self.flag = False


    async def close(self):
        """Закрывает соединение с ClickHouse."""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.info("ClickHouse connection closed.")

    async def create_log_table(self):
        """Создает таблицу для логов, если она не существует."""
        if not self.client:
            logger.warning("Cannot create log table, client is not available.")
            return

        create_table_query = """
        CREATE TABLE IF NOT EXISTS request_logs (
            timestamp DateTime('UTC') DEFAULT now('UTC'),
            method String,
            path String,
            client_ip String,
            status_code UInt16,
            process_time_ms Decimal(10, 1)
        ) ENGINE = MergeTree()
        ORDER BY (timestamp);
        """
        try:
            await self.client.execute(create_table_query) # Используем execute для DDL
            logger.info("Table 'request_logs' is ready.")
        except Exception as e:
            logger.error(f"Failed to create 'request_logs' table: {e}") # Не обнуляем self.client

    async def log_request(self, method: str, path: str, client_ip: str, status_code: int, process_time: float):
        """Асинхронно записывает данные о запросе в ClickHouse."""
        if not self.client:
            logger.warning("ClickHouse client not available. Log skipped.")
            if not self.flag:
                self.flag = True
                asyncio.create_task(self.connect())
            return
        try:
            await self.client.execute(
                "INSERT INTO request_logs (method, path, client_ip, status_code, process_time_ms) VALUES",
                (method, path, client_ip, status_code, process_time)
            )
        except Exception as e:
            logger.error(f"Failed to insert log into ClickHouse: {e}")

clickhouse_logger = ClickHouseManager()