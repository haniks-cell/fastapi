from time import time
import uuid
from jwt.exceptions import InvalidTokenError
from fastapi import APIRouter, Depends, status, HTTPException,  Header, Response, Cookie, Form
from typing import Annotated, Any, Awaitable, Callable, Dict
from sqlalchemy.ext.asyncio import async_sessionmaker
from database import session_maker
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import HTTPBasic, HTTPBasicCredentials, HTTPBearer, HTTPAuthorizationCredentials
import secrets
from schemas.login import LoginCreate, TokenInfo
from repositories.login import LoginRepository, LoginRepositoryHelp
router = APIRouter(
    prefix='/api/login',
    tags=['login']
)
lgrp = LoginRepositoryHelp()

http_bearer = HTTPBearer()

john = LoginCreate (username='john', password=lgrp.hash_password('qwerty'))
sam = LoginCreate (username='sam', password=lgrp.hash_password('qwerty12345'))

udb: dict[str, LoginCreate] = {
    john.username: john,
    sam.username: sam
}

def validate_auth (
        username: str = Form(),
        password: str = Form()
):
    unauth = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='invalid username or password'
    )
    if not (user := udb.get(username)):
        raise unauth
    if not lgrp.validate_password(password=password, hash_password=user.password.encode()):
        raise unauth
    if not user.active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='user inactive')
    return user

@router.post('/login/', response_model=TokenInfo)
async def auth_jwt(user: LoginCreate = Depends(validate_auth)):
    jwt_token = {
        "sub": '1',
        "username": user.username,
        "email": user.email
    }
    token = lgrp.encode_jwt(jwt_token)
    return TokenInfo (
        access_token=token,
        token_type='Bearer' 
    )

def get_user (
        token: HTTPAuthorizationCredentials = Depends(http_bearer)
) -> LoginCreate:
    # print(token.credentials)
    try:
        payload = lgrp.decode_jwt(jwts=token.credentials)
    except InvalidTokenError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='invalid token') #Signature has expired
    # print(payload)
    return LoginCreate(username=payload.username, password='qwerty')

def get_current_user (user: LoginCreate = Depends(get_user)):
    if not user.active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='user inactive')
    return user

@router.get("/user")
async def auth_user_check(user: LoginCreate = Depends(get_current_user)):
    return {
        "username": user.username,
        "email": user.email
    }



















# async def get_session():
#     async with session_maker() as session:
#         yield session

# # SesDep = Annotated[AsyncSession, Depends(get_session)]
# security = HTTPBasic()

# @router.get("/", status_code=status.HTTP_200_OK)
# async def get_categories(credentials:Annotated[HTTPBasicCredentials, Depends(security)]):
#     return {'username': credentials.username, 'pass': credentials.password}

# def get_auth_user_username(
#     credentials: Annotated[HTTPBasicCredentials, Depends(security)],
# ) -> str:
#     unauthed_exc = HTTPException(
#         status_code=status.HTTP_401_UNAUTHORIZED,
#         detail="Invalid username or password",
#         headers={"WWW-Authenticate": "Basic"},
#     )
#     correct_password = 'admin'
#     if correct_password is None:
#         raise unauthed_exc

#     # secrets
#     if not secrets.compare_digest(
#         credentials.password.encode("utf-8"),
#         correct_password.encode("utf-8"),
#     ):
#         raise unauthed_exc

#     return credentials.username

# @router.get("/auth/")
# def demo_basic_auth_username(
#     auth_username: str = Depends(get_auth_user_username),
# ):
#     return {
#         "message": f"Hi, {auth_username}!",
#         "username": auth_username,
#     }


# def get_username_by_static_auth_token(
#     static_token: str = Header(alias="x-auth-token"),
# ) -> str:
#     if static_token == "addssagjb4f":
#         return static_token

#     raise HTTPException(
#         status_code=status.HTTP_401_UNAUTHORIZED,
#         detail="token invalid",
#     )

# @router.get("/some-http-header-auth/")
# def demo_auth_some_http_header(
#     username: str = Depends(get_username_by_static_auth_token),
# ):
#     return {
#         "message": f"Hi, {username}!",
#         "username": username,
#     }

# COOKIES: dict[str, dict[str, Any]] = {}
# COOKIE_SESSION_ID_KEY = "web-app-session-id"


# def generate_session_id() -> str:
#     return uuid.uuid4().hex


# def get_session_data(
#     session_id: str = Cookie(alias=COOKIE_SESSION_ID_KEY),
# ) -> dict:
#     if session_id not in COOKIES:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="not authenticated",
#         )

#     return COOKIES[session_id]


# @router.post("/login-cookie/")
# def demo_auth_login_set_cookie(
#     response: Response,
#     # auth_username: str = Depends(get_auth_user_username),
#     username: str = Depends(get_username_by_static_auth_token),
# ):
#     session_id = generate_session_id()
#     COOKIES[session_id] = {
#         "username": username,
#         "login_at": int(time()),
#     }
#     response.set_cookie(COOKIE_SESSION_ID_KEY, session_id)
#     return {"result": "ok"}


# @router.get("/check-cookie/")
# def demo_auth_check_cookie(
#     user_session_data: dict = Depends(get_session_data),
# ):
#     username = user_session_data["username"]
#     return {
#         "message": f"Hello, {username}!",
#         **user_session_data,
#     }