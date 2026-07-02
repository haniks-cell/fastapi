from time import time
from fastapi import APIRouter, Depends, status, HTTPException,  Header, Response, Cookie, Form
from typing import Annotated, Any, Awaitable, Callable, Dict, Union
from schemas.login import LoginCreate, LoginCreateResponse, LoginGet, TokenInfo, Login, RefreshTokensCreate, LoginCreateInp
from repositories.login import LoginRepository, LoginRepositoryHelp
from services.login_serv import LoginService


from dependses import SesDep, RedisDep, ServDep

from models.login import Users
router = APIRouter(
    prefix='/api/auth',
    tags=['autenthication']
)

lgrp = LoginRepositoryHelp()
 
@router.put('/registration/', response_model=LoginCreateResponse)
async def registration (userGet: LoginCreateInp, redis: RedisDep, service: ServDep):
    await redis.set('user', str(userGet.username), ex=600)
    return await service.create_user(LoginCreate(username=userGet.username,
                                                  hash_password=str(lgrp.hash_password(userGet.hash_password))[1::].strip("'"),
                                                  lvl_access=0, email=userGet.email))

@router.post('/login/', response_model=TokenInfo)
async def auth_jwt(userGet: LoginGet, rep: ServDep, response: Response):
    resp = await rep.login_user(userGet)
    response.set_cookie(key='access', value=resp.token, httponly=True)
    response.set_cookie(key='refresh', value=resp.refresh, httponly=True)
    return TokenInfo (access_token=resp.token, refresh_token=resp.refresh)

@router.get("/refresh/", response_model=TokenInfo)
async def get_refresh_token(
    rep: ServDep,
    response: Response,
    refresh: Annotated[str | None, Cookie()] = None
):
    # rep = LoginService(session)
    resp = await rep.refresh_user(refresh)
    response.set_cookie(key='access', value=resp.token, httponly=True)
    response.set_cookie(key='refresh', value=resp.refresh, httponly=True)
    return TokenInfo (access_token=resp.token, refresh_token=resp.refresh)
