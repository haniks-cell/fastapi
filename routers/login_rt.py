from time import time
import uuid
from jwt.exceptions import InvalidTokenError
from fastapi import APIRouter, Depends, status, HTTPException,  Header, Response, Cookie, Form
from typing import Annotated, Any, Awaitable, Callable, Dict, Union
from sqlalchemy.ext.asyncio import async_sessionmaker
from database import session_maker
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import HTTPBasic, HTTPBasicCredentials, HTTPBearer, HTTPAuthorizationCredentials
import secrets
from schemas.login import LoginCreate, LoginCreateResponse, LoginGet, TokenInfo, Login, RefreshTokensCreate
from repositories.login import LoginRepository, LoginRepositoryHelp

from models.login import Users
router = APIRouter(
    prefix='/api/auth',
    tags=['autenthication']
)
async def get_session():
    async with session_maker() as session:
        yield session

SesDep = Annotated[AsyncSession, Depends(get_session)]

lgrp = LoginRepositoryHelp()

# http_bearer = HTTPBearer()

@router.put('/registration/', response_model=LoginCreateResponse)
async def registration (userGet: LoginCreate, session: SesDep):
    rep = LoginRepository(session)
    userGet.lvl_access=0
    userGet.hash_password = str(lgrp.hash_password(userGet.hash_password))[1::].strip("'")
    user = await rep.set_user(userGet)
    return LoginCreateResponse(ok=True)

@router.post('/login/', response_model=TokenInfo)
async def auth_jwt(userGet: LoginGet, session: SesDep, response: Response):
    rep = LoginRepository(session)
    user = await rep.get_by_username(userGet.username)
    if user == None or not lgrp.validate_password(password=userGet.hash_password, hash_password=user.hash_password.encode()):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='inalid username or password')
    jwt_token = {
        "sub": user.tid,
        "username": user.username,
        "lvl_access": user.lvl_access
    }
    token = lgrp.encode_jwt(jwt_token)
    response.set_cookie(key='access', value=token, httponly=True)
    refresh = uuid.uuid4().__str__()

    await rep.set_refresh(RefreshTokensCreate(user_id=user.tid, uuid=refresh))
    response.set_cookie(key='refresh', value=refresh, httponly=True)
    return TokenInfo (access_token=token, refresh_token=refresh)

@router.get("/refresh/", response_model=TokenInfo)
async def get_refresh_token(
    session: SesDep,
    response: Response,
    refresh: Annotated[str | None, Cookie()] = None
):
    rep = LoginRepository(session)
    token = await rep.is_exist(refresh)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='refresh not found')
    refresh_token = await rep.set_refresh(RefreshTokensCreate(user_id=token.user_id, uuid=uuid.uuid4().__str__()))
    jwt_token = {
        "sub": token.user_id,
        "username": token.user.username,
        "lvl_access": token.user.lvl_access
    }
    access = lgrp.encode_jwt(jwt_token)
    response.set_cookie(key='access', value=access, httponly=True)
    response.set_cookie(key='refresh', value=refresh_token.uuid, httponly=True)
    return TokenInfo (access_token=access, refresh_token=refresh_token.uuid)


# def get_user (
#         token: HTTPAuthorizationCredentials = Depends(http_bearer)
# ) -> LoginCreate:
#     # print(token.credentials)
#     try:
#         payload = lgrp.decode_jwt(jwts=token.credentials)
#     except InvalidTokenError as e:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='invalid token') #Signature has expired
#     # print(payload)
#     return LoginCreate(username=payload.username, password='qwerty')

# def get_current_user (user: LoginCreate = Depends(get_user)):
#     if not user.active:
#         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='user inactive')
#     return user

# @router.get("/user")
# async def auth_user_check(user: LoginCreate = Depends(get_current_user)):
#     return {
#         "username": user.username,
#         "email": user.email
#     }




