from database import session_maker
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends

async def get_session():
    async with session_maker() as session:
        yield session

SesDep = Annotated[AsyncSession, Depends(get_session)]