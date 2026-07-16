from typing import List
# from dependses import RedisDep
from repositories.login import LoginRepository, LoginRepositoryHelp
from schemas.login import LoginCreate, LoginCreateResponse, LoginGet, ResponseServiceLogin, RefreshTokensCreate, LoginCreateInp
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import uuid, asyncio, pyotp, io, qrcode
from config import settings
from models.login import TOTPTokens
import redis.asyncio as aioredis
class LoginService:
    def __init__(self, db: AsyncSession):
        self.rep = LoginRepository(db)
        self.lgrp = LoginRepositoryHelp()

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
            "lvl_access": user.lvl_access
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
            "lvl_access": token.user.lvl_access
        }
        access = self.lgrp.encode_jwt(jwt_token)
        return ResponseServiceLogin(token=access, refresh=refresh_token.uuid)

    async def isExistUser (self, user: LoginCreateInp) -> bool:
        redis = aioredis.from_url(settings.get_redis_url(), decode_responses=True)
        if await redis.get(f"confirm_username:{user.username}") or await self.rep.get_by_username(user.username):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="username already exists")
        
        if len(await self.rep.get_by_email(user.email)) >3:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="email already exists")
        return True
    async def set_one_time_token(self, userGet: LoginCreateInp, token: str) -> bool:
        redis = aioredis.from_url(settings.get_redis_url(), decode_responses=True)
        await asyncio.gather(redis.set(f"confirm_username:{userGet.username}", token, ex=600), redis.set(f"confirm_token:{token}", userGet.model_dump_json(), ex=600))
    
    async def get_totp (self, tid: int) -> str:
        redis = aioredis.from_url(settings.get_redis_url(), decode_responses=True)
        key = pyotp.random_base32()
        await redis.set(f"totp_key:{tid}", key, ex=480)
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
        redis = aioredis.from_url(settings.get_redis_url(), decode_responses=True)
        # user = await self.rep.get_by_id(tid)
        # key = await redis.get(f"totp_key:{tid}")
        user, key = await asyncio.gather(self.rep.get_by_id(tid), redis.get(f"totp_key:{tid}"))
        await self.rep.add_totp(user.tid, key)
        await redis.delete(f"totp_key:{tid}")
        return True
        # user.potptoken = TOTPTokens(user_id=tid,token=key)

    async def check_totp_redis (self, totp: int, tid: int) -> bool:
        redis = aioredis.from_url(settings.get_redis_url(), decode_responses=True)
        key = await redis.get(f"totp_key:{tid}")
        if not key:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="you need '/get_totp/' first")
        return pyotp.totp.TOTP(key).verify(totp)

    async def check_totp (self, totp: int, tid: int) -> bool:
        user = await self.rep.get_by_id_totp(tid)
        if not user.potptoken:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="you need '/get_totp/' first")
        return pyotp.totp.TOTP(user.potptoken.token).verify(totp)
    
    async def isExistTOTP (self, tid: int) -> bool:
        redis = aioredis.from_url(settings.get_redis_url(), decode_responses=True)
        user_redis, user_db = await asyncio.gather(redis.get(f"totp_key:{tid}"), self.rep.get_by_id_totp(tid))
        if user_redis or user_db.potptoken:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="TOTP already exists")
        return True


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