from typing import List

from pydantic import EmailStr
# from dependses import RedisDep
from repositories.login import LoginRepository, LoginRepositoryHelp, LoginRepositoryHTTP
from schemas.login import LoginCreate, LoginCreateResponse, LoginGet, ResponseServiceLogin, RefreshTokensCreate, LoginCreateInp,  GoogleIdTokenPayload, GoogleOAUTHResponse
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import uuid, asyncio, pyotp, io, qrcode, urllib.parse
from config import settings
from models.login import TOTPTokens
import redis.asyncio as aioredis
import logging
from kafka_config import kafka_manager
log = logging.getLogger(__name__)


class LoginService:
    def __init__(self, db: AsyncSession, redis: aioredis.Redis):
        self.rep = LoginRepository(db)
        self.redis = redis
        self.lgrp = LoginRepositoryHelp()
        self.rephttp = LoginRepositoryHTTP()

    async def create_user(self, user_data: LoginCreate) -> LoginCreateResponse:
        try:
            user = await self.rep.set_user(user_data)
            return LoginCreateResponse(ok=True)
        except IntegrityError:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User with this username already exists")
    
    async def login_user (self, userGet: LoginGet) -> ResponseServiceLogin:
        user = await self.rep.get_by_username(userGet.username)
        if user == None or not self.lgrp.validate_password(password=userGet.hash_password, hash_password=user.hash_password.encode()):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='inalid username or password')
        jwt_token = {
            "sub": str(user.tid),
            "username": user.username,
            "lvl_access": user.lvl_access,
            "access_google_id": 0
        }
        token = self.lgrp.encode_jwt(jwt_token)
        refresh = uuid.uuid4().__str__()
        await self.rep.set_refresh(RefreshTokensCreate(user_id=user.tid, uuid=refresh))
        return ResponseServiceLogin(token=token, refresh=refresh)
    
    async def refresh_user (self, refresh: str) -> ResponseServiceLogin:
        token = await self.rep.is_exist(refresh)
        if not token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='refresh not found')
        refresh_token = await self.rep.set_refresh(RefreshTokensCreate(user_id=token.user_id, uuid=uuid.uuid4().__str__()))
        jwt_token = {
            "sub": str(token.user_id),
            "username": token.user.username,
            "lvl_access": token.user.lvl_access,
            "access_google_id": 0
        }
        access = self.lgrp.encode_jwt(jwt_token)
        return ResponseServiceLogin(token=access, refresh=refresh_token.uuid)

    async def isExistUser (self, user: LoginCreateInp) -> bool:
        await self.isExistUsername(user.username)
        if not user.email:
            return True
        await self.isExistEmail(user.email)
        return True
    def userNotOnlyNumbers (self, username: str) -> None:
        if username.isdigit():
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Username cannot be only numbers")
    async def isExistEmail (self, email: EmailStr) -> bool:
        # redis = aioredis.from_url(settings.get_redis_url(), decode_responses=True)
        if not email:
            return True
        if await self.rep.get_by_email(email) or await self.redis.get(f"confirm_email:{email}"):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="email already exists")
        return True
    async def isExistUsername (self, username: str) -> bool:
        # redis = aioredis.from_url(settings.get_redis_url(), decode_responses=True)
        if await self.redis.get(f"confirm_username:{username}") or await self.rep.get_by_username(username):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="username already exists")

    async def set_one_time_token(self, userGet: LoginCreateInp, token: str) -> bool:
        # redis = aioredis.from_url(settings.get_redis_url(), decode_responses=True)
        await asyncio.gather(self.redis.set(f"confirm_username:{userGet.username}", token, ex=600), self.redis.set(f"confirm_token:{token}", userGet.model_dump_json(), ex=600), self.redis.set(f"confirm_email:{userGet.email}", token, ex=600))
    
    async def get_totp (self, tid: int) -> str:
        # redis = aioredis.from_url(settings.get_redis_url(), decode_responses=True)
        key = pyotp.random_base32()
        await self.redis.set(f"totp_key:{tid}", key, ex=480)
        provisioning_uri = pyotp.totp.TOTP(key).provisioning_uri(
            # name="", 
            issuer_name="APP"
        )
        return provisioning_uri
    
    def create_qr(self, uri: str) -> io.BytesIO:
        qr_image = qrcode.make(uri)
        buffered = io.BytesIO()
        qr_image.save(buffered, format="PNG")
        buffered.seek(0)
        return buffered
    async def add_totp (self, tid: int) -> bool:
        # redis = aioredis.from_url(settings.get_redis_url(), decode_responses=True)
        # user = await self.rep.get_by_id(tid)
        # key = await redis.get(f"totp_key:{tid}")
        user, key = await asyncio.gather(self.rep.get_by_id(tid), self.redis.get(f"totp_key:{tid}"))
        await self.rep.add_totp(user.tid, key)
        await self.redis.delete(f"totp_key:{tid}")
        return True
        # user.potptoken = TOTPTokens(user_id=tid,token=key)

    async def check_totp_redis (self, totp: str, tid: int) -> bool:
        # redis = aioredis.from_url(settings.get_redis_url(), decode_responses=True)
        key = await self.redis.get(f"totp_key:{tid}")
        if not key:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="you need '/get_totp/' first")
        return pyotp.totp.TOTP(key).verify(totp)

    async def check_totp (self, totp: int, tid: int) -> bool:
        user = await self.rep.get_by_id_totp(tid)
        if not user.potptoken:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="you need '/get_totp/' first")
        return pyotp.totp.TOTP(user.potptoken.token).verify(totp)
    
    async def isExistTOTP (self, tid: int) -> bool:
        # redis = aioredis.from_url(settings.get_redis_url(), decode_responses=True)
        user_redis, user_db = await asyncio.gather(self.redis.get(f"totp_key:{tid}"), self.rep.get_by_id_totp(tid))
        if user_redis or user_db.potptoken:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="TOTP already exists")
        return True
    def create_googlelink (self, scope: str) -> str:
        params = {
        'client_id': settings.GOOGLE_CLIENT_ID,
        'redirect_uri': 'https://127.0.0.1/api/auth/google',
        'response_type': 'code',
        'scope': scope,
        'access_type': 'offline' 
        }
        return f'https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params, quote_via=urllib.parse.quote)}'
    async def callback_google (self, code: str) -> GoogleOAUTHResponse:
        params = {
        'client_id': settings.GOOGLE_CLIENT_ID,
        'client_secret': settings.GOOGLE_CLIENT_SECRET,
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': 'https://127.0.0.1/api/auth/google'
    }
        res = await self.rephttp.google_Callback(params)
        res['id_token'] = self.lgrp.decode_jwt_google(res['id_token'], audience=settings.GOOGLE_CLIENT_ID)
        return GoogleOAUTHResponse(**res)

    async def processing_google_callback (self, response: GoogleOAUTHResponse) -> ResponseServiceLogin:
        # redis = aioredis.from_url(settings.get_redis_url(), decode_responses=True)
        # if await self.rep.get_by_email(response.id_token.email) or await self.redis.get(f"confirm_email:{response.id_token.email}"):
        #     pass
        # await self.isExistUsername(response.id_token.sub)
        user = await self.rep.get_by_username(response.id_token.sub)
        if user:
            access=await self.rep.set_access_google(user.tid, response.access_token, response.expires_in)
            jwt_token = {
                "sub": str(user.tid),
                "username": user.username,
                "lvl_access": user.lvl_access,
                "access_google_id": access.user_id
            }
            token = self.lgrp.encode_jwt(jwt_token)
            refresh = uuid.uuid4().__str__()
            await self.rep.set_refresh(RefreshTokensCreate(user_id=user.tid, uuid=refresh))
            return ResponseServiceLogin(token=token, refresh=refresh)

        await self.isExistEmail(response.id_token.email)
        log.warning(response.id_token.sub)
        user=await self.rep.set_user(LoginCreate(username=response.id_token.sub, hash_password='0', email=response.id_token.email, lvl_access=6))
        await self.rep.set_refresh_google(user.tid, response.refresh_token, response.expires_in)
        access=await self.rep.set_access_google(user.tid, response.access_token, response.expires_in)
        # await self.redis.set(f'google_access:{access.user_id}', access.model_dump_json(), ex=response.expires_in)
        jwt_token = {
            "sub": str(user.tid),
            "username": user.username,
            "lvl_access": user.lvl_access,
            "access_google_id": access.user_id
        }
        token = self.lgrp.encode_jwt(jwt_token)
        refresh = uuid.uuid4().__str__()
        await self.rep.set_refresh(RefreshTokensCreate(user_id=user.tid, uuid=refresh))
        return ResponseServiceLogin(token=token, refresh=refresh)

    async def refresh_google(self, user_id: int):
        user=await self.rep.get_by_id_google(user_id)
        refresh = user.refresh_google.token
        params = {
        'client_id': settings.GOOGLE_CLIENT_ID,
        'client_secret': settings.GOOGLE_CLIENT_SECRET,
        'grant_type': 'refresh_token',
        'refresh_token': refresh
        }
        res = await self.rephttp.google_refresh(params)
        log.warning(res)
        await self.rep.update_access_google(user.refresh_google.user_id, res['access_token'], res['expires_in'])
        return res

    async def revoke_google (self, tid: int):
        user=await self.rep.get_by_id_google(tid)
        resp= await self.rephttp.revoke_google(user.refresh_google.token)
        await self.rep.delete_refresh_google(tid)
        return resp
    
    async def get_google_files(self, id_access: int):
        token=await self.rep.get_by_id_google_access(id_access)
        return await self.rephttp.get_google_file(token.token)
    # async def get_all_categories(self) -> List[CategoryResponse]:
    #     categories = await self.repository.get_all()
    #     return [CategoryResponse.model_validate(cat) for cat in categories]

    # async def get_category_by_id(self, category_id: int) -> CategoryResponse:
    #     category = await self.repository.get_by_id(category_id)
    #     if not category:
    #         raise HTTPException(
    #             status_code=status.HTTP_404_NOT_FOUND,
    #             detail=f'Category with id {category_id} not found'
    #         )
    #     return CategoryResponse.model_validate(category)

    # async def create_category(self, category_data: CategoryCreate) -> CategoryResponse:
    #     category = await self.repository.create(category_data)
    #     return CategoryResponse.model_validate(category)