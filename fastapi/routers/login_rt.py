import uuid, pyotp
import json, asyncio
from time import time
from fastapi import APIRouter, Depends, status, HTTPException,  Header, Response, Cookie, Form, Body
from fastapi.responses import StreamingResponse
from typing import Annotated, Any, Awaitable, Callable, Dict, Union
from schemas.login import LoginCreate, LoginCreateResponse, LoginGet, TokenInfo, Login, RefreshTokensCreate, LoginCreateInp, confirmEmail, TOTPCreateResponse
from repositories.login import LoginRepository, LoginRepositoryHelp
from services.login_serv import LoginService
from schemas.admin import AdminStatusResponse

from dependses import SesDep, RedisDep, ServDep, exist_access
from kafka_config import kafka_manager
from config import settings

from models.login import Users
router = APIRouter(
    prefix='/api/auth',
    tags=['autenthication']
)

lgrp = LoginRepositoryHelp()
 
@router.put('/registration/', response_model=LoginCreateResponse) #
async def registration (userGet: LoginCreateInp, redis: RedisDep, service: ServDep): 
    await service.isExistUser(userGet)
    token = str(uuid.uuid4())
    data = {'email': 5125774016, 'link': f'{settings.APPLICATION_URL}api/auth/email_confirm/?token={token}'}
    await asyncio.gather(service.set_one_time_token(userGet, token), kafka_manager.send_message("magiclink", value=json.dumps(data)))
    return LoginCreateResponse(ok=True)

@router.post('/login/', response_model=TokenInfo)
async def auth_jwt(userGet: LoginGet, rep: ServDep, response: Response):
    resp = await rep.login_user(userGet)
    response.set_cookie(key='access', value=resp.token, httponly=True, secure=True)
    response.set_cookie(key='refresh', value=resp.refresh, httponly=True, secure=True)
    return TokenInfo (access_token=resp.token, refresh_token=resp.refresh)

@router.get("/refresh/", response_model=TokenInfo)
async def get_refresh_token(
    rep: ServDep,
    response: Response,
    refresh: Annotated[str | None, Cookie()] = None
):
    if not refresh:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='отсутствует рефреш токен')
    resp = await rep.refresh_user(refresh)
    response.set_cookie(key='access', value=resp.token, httponly=True, secure=True)
    response.set_cookie(key='refresh', value=resp.refresh, httponly=True, secure=True)
    return TokenInfo (access_token=resp.token, refresh_token=resp.refresh)

@router.get("/email_confirm/", response_model=LoginCreateResponse)
async def email_confirm(token: str, redis: RedisDep, service: ServDep):
    user = await redis.get(f'confirm_token:{token}')
    if user:
        await redis.delete(f'confirm_token:{token}')
        user=json.loads(user)
        userGet = LoginCreateInp(**user)
        return await service.create_user(LoginCreate(username=userGet.username,
                                                  hash_password=str(lgrp.hash_password(userGet.hash_password))[1::].strip("'"),
                                                  lvl_access=0, email=userGet.email))
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Ссылка недействительна, истекла или уже была использована')

@router.get("/get_totp/", dependencies=[Depends(exist_access)])
async def get_totp (
    rep: ServDep,
    access: Annotated[str | None, Cookie()] = None
): 
    tid = lgrp.decode_jwt(access)
    await rep.isExistTOTP(tid.sub) 
    uri = await rep.get_totp(tid.sub)
    return TOTPCreateResponse(uri=uri)

@router.post("/create_qr/")
async def create_qr (
    rep: ServDep,
    uri: str = Body(..., embed=True),
):
    qr = rep.create_qr(uri)
    return StreamingResponse(qr, media_type="image/png")
    
@router.post('/check_totp/', dependencies=[Depends(exist_access)])
async def check_totp (
    rep: ServDep,
    totp: int = Body(..., embed=True),
    access: Annotated[str | None, Cookie()] = None,
):
    tid = lgrp.decode_jwt(access)
    if not await rep.check_totp(totp, tid.sub):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid TOTP code")
    return AdminStatusResponse(ok=True)

@router.post("/turn_on_totp/", dependencies=[Depends(exist_access)])
async def turn_on_totp (
    rep: ServDep,
    totp: int = Body(..., embed=True),
    access: Annotated[str | None, Cookie()] = None
):
    tid = lgrp.decode_jwt(access)
    if not await rep.check_totp_redis(totp, tid.sub):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid TOTP code")
    await rep.add_totp(tid.sub)
    return AdminStatusResponse(ok=True)


