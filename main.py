from fastapi import APIRouter, Depends, status, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Annotated, Any, Awaitable, Callable, Dict
from sqlalchemy.ext.asyncio import async_sessionmaker
from database import session_maker
from sqlalchemy.ext.asyncio import AsyncSession
from routers.category_rt import router as cat_rt
from routers.login_rt import router as lg_rt
from routers.products_rt import router as pr_rt
import uvicorn
from contextlib import asynccontextmanager
from database import create_db

from repositories.category_rep import CategoryRepository

@asynccontextmanager
async def lifespan(app: FastAPI):
    # await create_db_and_tables() 
    await create_db()

    yield  # В этой точке приложение начинает принимать запросы
    

app = FastAPI(docs_url='/api/dock', lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://127.0.0.1:8000/'],
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
if __name__ == '__main__':
    uvicorn.run('main:app', reload=True)
