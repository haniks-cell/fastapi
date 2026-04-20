import json
from time import time
import uuid
import asyncio
from aiokafka import AIOKafkaProducer
from aiokafka import AIOKafkaProducer
from jwt.exceptions import InvalidTokenError
from fastapi import APIRouter, Depends, status, HTTPException,  Header, Response, Cookie, Form
from typing import Annotated, Any, Awaitable, Callable, Dict, List, Union
from sqlalchemy.ext.asyncio import async_sessionmaker
from database import session_maker
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import HTTPBasic, HTTPBasicCredentials, HTTPBearer, HTTPAuthorizationCredentials
import secrets
from slugify import slugify

from repositories.login import LoginRepositoryHelp
from schemas.category import CategoryCreate, CategoryResponse
from models.login import Users
from repositories.product_rep import ProductRepository, CategoryRepository
from schemas.product import ProductCreate, ProductResponse, ProductResponseArrEl
from kafka_config import kafka_manager

from dependses import SesDep

from pydantic import BaseModel, Field
router = APIRouter(
    prefix='/api/products',
    tags=['products']
)

lgpr = LoginRepositoryHelp()



async def get_kafka():
    return
# async def get_kafka():
#     serializer = lambda v: json.dumps(v).encode('utf-8')
#     async with AIOKafkaProducer(
#             bootstrap_servers='localhost:9092',
#             value_serializer=serializer  # <--- Вот здесь магия
#         ) as producer:
#             yield producer

async def get_lvl_access(access: Annotated[str | None, Cookie()] = None) -> int:
    if access:
        return lgpr.decode_jwt(str(access)).lvl_access
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='user not auth')


AccDep = Annotated[int, Depends(get_lvl_access)]
# KafkaDep = Annotated[AIOKafkaProducer, Depends(get_kafka)]

@router.put('/add_cat/')
async def add_categories(name: str, session: SesDep, lvl_access: AccDep):
    if lvl_access >= 3:
        rep = CategoryRepository(session)
        await rep.create(CategoryCreate(name=name, slug=slugify(name)))
        return {'ok': lvl_access}
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='not roule')

@router.put('/add_prod/')
async def add_products(name: ProductCreate, session: SesDep, lvl_access: AccDep):
    if lvl_access >= 3:
        rep = ProductRepository(session)
        await rep.create(name)
        return {'ok': True}
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='not roule')
    
@router.get('/products/', response_model=List[ProductResponseArrEl])
async def get_products(session: SesDep):
    rep = ProductRepository(session)
    prodcts = await rep.get_all()
    resp = []
    for el in prodcts:
        resp.append(ProductResponseArrEl(id=el.id, name=el.name, description=el.description, price=el.price, category_id=el.category_id, image_url=el.image_url, created_at=el.created_at))
    return resp

class UserAction(BaseModel):
    user_id: int
    status: str
    payload: str

@router.get('/hello/')
async def test (): #producer: KafkaDep
    data = UserAction(user_id=1, status='ok', payload='fdf')
    # print("Отправка словаря...")
    await kafka_manager.send_message("my_test_topic", value=data.model_dump())
    # print("Данные успешно отправлены в формате JSON!")
    return {"status": "message sent to kafka"}

@router.get('/{product_id}/', response_model=ProductResponse)
async def get_poduct(product_id: int, session: SesDep):
    rep = ProductRepository(session)
    product = await rep.get_by_id(product_id)
    return ProductResponse(id=product.id, name=product.name, description=product.description, price=product.price, category_id=product.category_id, image_url=product.image_url, created_at=product.created_at, category=CategoryResponse(id=product.category.id, slug=product.category.slug, name=product.category.name))
