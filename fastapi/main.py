from fastapi import APIRouter, Depends, status, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
from typing import Annotated, Any, Awaitable, Callable, Dict
from sqlalchemy.ext.asyncio import async_sessionmaker
from database import session_maker
from sqlalchemy.ext.asyncio import AsyncSession
from routers.category_rt import router as cat_rt
from routers.login_rt import router as lg_rt
from routers.products_rt import router as pr_rt
from routers.admin_rt import router as admin_rt
import uvicorn
from contextlib import asynccontextmanager
from database import create_db
from starlette.middleware.base import BaseHTTPMiddleware
from clickhouse_manager import clickhouse_logger

from repositories.category_rep import CategoryRepository
from kafka_config import kafka_manager

import logging
import time
from fastapi import Request
from dependses import SesDep, get_session
from schemas.login import LoginCreate
from repositories.login import LoginRepository, LoginRepositoryHelp

from database import session_maker

lgrp = LoginRepositoryHelp()

async def create_admin():
    async with session_maker() as session:
        rep = LoginRepository(session)
        userGet = LoginCreate(username='admin', hash_password=str(lgrp.hash_password('admin'))[1::].strip("'"), lvl_access=5, email='example@example.com')
        user = await rep.set_user(userGet)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # await clickhouse_logger.connect()
    await kafka_manager.start()
    # await create_admin()
    yield  # В этой точке приложение начинает принимать запросы
    await clickhouse_logger.close()
    await kafka_manager.stop()


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)
app = FastAPI(docs_url='/api/dock', lifespan=lifespan)

@app.get('/start', status_code=status.HTTP_200_OK)
async def starting():
    await create_db()
    await create_admin()
    # await clickhouse_logger.connect()
    return {'start': 'ok'}

@app.get('/startl', status_code=status.HTTP_200_OK)
async def startingd():
    await clickhouse_logger.connect()
    return {'start': 'ok'}


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.perf_counter()
        status_code = 500  # По умолчанию, если произойдет необработанная ошибка
        try:
            # Выполняем запрос
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception as e:
            # В случае исключения, логируем его и снова выбрасываем,
            # чтобы FastAPI мог его обработать.
            logger.error(f"Request failed with exception: {e}")
            raise e
        finally:
            process_time = (time.perf_counter() - start_time) * 1000
            process_time = round(process_time, 1) # Округляем до одного знака

            if not request.url.path.startswith("/api/dock"):
            # Вывод в консоль
                logger.info(
                    f"Метод: {request.method} | "
                    f"Путь: {request.url.path} | "
                    f"Статус: {status_code} | "
                    f"Время: {process_time:.1f}ms"
                )

            # Пропускаем логирование для документации
            
                # Асинхронно отправляем лог в ClickHouse
                await clickhouse_logger.log_request(
                    method=request.method,
                    path=request.url.path,
                    client_ip=request.client.host,
                    status_code=status_code,
                    process_time=process_time
                )

# Добавляем middleware для обработки заголовков от прокси.
# trusted_hosts="*" разрешает все хосты, что удобно для разработки.
# В продакшене лучше указать IP-адрес вашего Nginx-контейнера.
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

app.add_middleware(LoggingMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['https://127.0.0.1/'],
    allow_methods=["*"],
    allow_headers=["*"]

)

# @app.on_event('startup')
# async def on_startup():
#     create_db()

# @app.get("/", status_code=status.HTTP_200_OK)
# async def get_categories():
#     return {'test': 'ok'}

app.include_router(cat_rt)
app.include_router(lg_rt)
app.include_router(pr_rt)
app.include_router(admin_rt)

if __name__ == '__main__':
    uvicorn.run('main:app', reload=True)