from database import session_maker
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException, status, HTTPException, Header, Response, Cookie
from repositories.login import LoginRepositoryHelp

lgpr = LoginRepositoryHelp()

async def get_lvl_access(access: Annotated[str | None, Cookie()] = None) -> int:
    if access:
        return lgpr.decode_jwt(str(access)).lvl_access
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='user not auth')

async def get_session():
    async with session_maker() as session:
        yield session

SesDep = Annotated[AsyncSession, Depends(get_session)]
AccDep = Annotated[int, Depends(get_lvl_access)]