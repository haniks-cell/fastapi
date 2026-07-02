from fastapi import APIRouter, Depends, status
from typing import Annotated, Any, Awaitable, Callable, Dict
from sqlalchemy.ext.asyncio import async_sessionmaker
from database import session_maker
from sqlalchemy.ext.asyncio import AsyncSession

from services.category_serv import CategoryService
from typing import List

from repositories.category_rep import CategoryRepository
from repositories.product_rep import ProductRepository
from schemas.category import CategoryCreate, CategoryResponse
from schemas.product import ProductCreate

from dependses import SesDep

router = APIRouter(
    prefix='/api/categories',
    tags=['categories']
)

async def get_category_service(session: SesDep) -> CategoryService:
    return CategoryService(session)

catrepDep = Annotated[CategoryService, Depends(get_category_service)]


@router.get("/", response_model=List[CategoryResponse], status_code=status.HTTP_200_OK)
async def get_categories(service: catrepDep):
    # service = CategoryService(session)
    return await service.get_all_categories()

@router.get('/{category_id}', response_model=CategoryResponse, status_code=status.HTTP_200_OK)
async def get_category(category_id: int, service: catrepDep):
    # service = CategoryService(session)
    return await service.get_category_by_id(category_id)