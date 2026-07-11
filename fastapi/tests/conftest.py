import asyncio
from typing import AsyncGenerator, Generator

from unittest.mock import AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker

import pytest 
from httpx import AsyncClient, ASGITransport # Импортируем ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import redis.asyncio as aioredis

from main import app, kafka_manager, create_admin # Импортируем kafka_manager и create_admin из main
from models.base import Base # Убедитесь, что импорт Base корректен
from dependses import get_session, get_redis
from models.login import Users
from repositories.login import LoginRepositoryHelp # Предполагается, что модель пользователя находится здесь

# Используем SQLite в памяти для тестов
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(TEST_DATABASE_URL, echo=True)
TestingSessionLocal = async_sessionmaker(
    autocommit=False, autoflush=False, bind=engine, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture(scope="function", autouse=True)
async def setup_database():
    """Фикстура для создания и очистки таблиц в тестовой БД."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    """Переопределение зависимости для получения сессии тестовой БД."""
    async with TestingSessionLocal() as session:
        yield session

# async def override_get_redis():
#     return aioredis.from_url(f'redis://localhost:6379/0', decode_responses=True)

# Применяем переопределение зависимости get_db
app.dependency_overrides[get_session] = override_get_db
# app.dependency_overrides[get_redis] = override_get_redis


@pytest.fixture(scope="session", autouse=True)
def mock_lifespan_dependencies():
    """
    Фикстура для мокирования зависимостей, запускаемых в lifespan FastAPI приложения.
    Предотвращает реальное подключение к Kafka и создание администратора во время тестов.
    """
    with patch.object(kafka_manager, 'start', new_callable=AsyncMock), \
         patch.object(kafka_manager, 'stop', new_callable=AsyncMock), \
         patch.object(kafka_manager, 'send_message', new_callable=AsyncMock), \
         patch('main.create_admin', new_callable=AsyncMock) as mock_create_admin:
        yield
    mock_create_admin.reset_mock() # Сбрасываем мок после завершения сессии


@pytest.fixture(scope="function")
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Фикстура для создания асинхронного тестового клиента."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as ac:
        yield ac


@pytest.fixture(scope="function")
async def db() -> AsyncGenerator[AsyncSession, None]:
    """Фикстура, предоставляющая сессию тестовой БД для тестов."""
    async with TestingSessionLocal() as session:
        yield session

@pytest.fixture(scope="function")
async def redis() -> AsyncGenerator[aioredis.Redis, None]:
    """Фикстура, предоставляющая Redis для тестов."""
    return aioredis.from_url(f'redis://localhost:6379/0', decode_responses=True)

@pytest.fixture(scope="function")
async def admin_user(db: AsyncSession):
    """Фикстура для создания администратора в тестовой БД."""
    admin = Users(
        email="admin@example.com",
        username="admin_test",
        hash_password=LoginRepositoryHelp().hash_password("some_hashed_password").decode('utf-8'), # Хешируем пароль
        lvl_access=5, # Предполагаем, что 5 - это уровень доступа администратора
    )
    db.add(admin)
    await db.commit()
    await db.refresh(admin)
    return admin


@pytest.fixture(scope="function")
def admin_auth_headers() -> dict:
    """
    Фикстура для имитации заголовков аутентификации администратора.
    ПРИМЕЧАНИЕ: Здесь должна быть логика создания настоящего JWT токена.
    """
    # Для простоты мы пока не будем генерировать настоящий токен.
    # В реальном проекте здесь нужно создать токен для admin_user.
    # FastAPI позволяет "пропускать" зависимости в тестах.
    # Мы будем полагаться на переопределение зависимости `get_current_admin_user`.
    return {"Authorization": "Bearer admin_token"}