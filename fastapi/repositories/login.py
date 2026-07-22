from datetime import timedelta, datetime, timezone
from models.login import Users, RefreshTokens, TOTPTokens, RefreshGoogle, AccessGoogle
from schemas.login import LoginCreate, TokenJwt, RefreshTokensCreate
import jwt
import bcrypt
from schemas.login import setting
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from aiohttp import ClientSession
# from decorator import complited_time

class LoginRepositoryHelp:
    def encode_jwt(
            self,
            payload: dict,
            key: str = setting.auth_jwt.private.read_text(),
            alhoritm: str = setting.auth_jwt.algorithm,
            expire_min: int = setting.auth_jwt.access_token_min,
            expire_timedelta: timedelta | None = None
                         ):
        now = datetime.now(timezone.utc).replace(microsecond=0)
        to_enc = payload.copy()
        if expire_timedelta:
            expire = now + expire_timedelta
        else:
            expire = now + timedelta(minutes=expire_min)
        to_enc.update(exp=expire, iat=now)
        encoded = jwt.encode(to_enc, key, algorithm=alhoritm)
        return encoded
    def decode_jwt(self,
            jwts: str,
            key: str = setting.auth_jwt.public.read_text(),
            alhoritm: str = setting.auth_jwt.algorithm) -> TokenJwt:
        # print('do')
        decoded = jwt.decode(jwts, key, algorithms=[alhoritm], leeway=10)
        # return decoded
        # print('posle')
        return TokenJwt(sub=int(decoded['sub']), username=decoded['username'], lvl_access=int(decoded['lvl_access']), access_google_id =int(decoded['access_google_id']), exp=int(decoded['exp']), iat=int(decoded['iat']))
        # return TokenJwt(sub=1, username='fff', email=)
    
    def decode_jwt_google(self,
            jwts: str,
            audience: str,
            alhoritm: str = setting.auth_jwt.algorithm) -> TokenJwt:
        # print('do')
        jwks_client = jwt.PyJWKClient("https://www.googleapis.com/oauth2/v3/certs")
        keys = jwks_client.get_signing_key_from_jwt(jwts)
        return jwt.decode(jwts, keys.key, algorithms=[alhoritm], audience=audience, leeway=10)

    def hash_password(self,password:str) -> bytes:
        salt = bcrypt.gensalt()
        pwd_bytes: bytes = password.encode()
        return bcrypt.hashpw(pwd_bytes, salt)
    def validate_password (self, password: str, hash_password: bytes) -> bool:
        return bcrypt.checkpw(password.encode(), hash_password)
    
class LoginRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def set_user (self, user: LoginCreate) -> Users:
        db_user = Users(**user.model_dump())
        self.db.add(db_user)
        await self.db.commit()
        await self.db.refresh(db_user)
        return db_user 

    async def get_by_username(self, username: str) -> Optional[Users]:
        query = select(Users).where(Users.username == username)
        res = await self.db.execute(query)
        return res.scalar()
    
    async def get_by_username_google(self, username: str) -> Optional[Users]:
        query = select(Users).where(Users.username == username).options(joinedload(Users.refresh_google))
        res = await self.db.execute(query)
        return res.scalar()
    
    async def delete_refresh(self, user_id:str) -> None:
        query = delete(RefreshTokens).where(RefreshTokens.user_id == user_id)
        res = await self.db.execute(query)

    async def set_refresh(self, refresh: RefreshTokensCreate, expire_days: int = setting.auth_jwt.refresh_token_days) -> RefreshTokens:
        await self.delete_refresh(refresh.user_id)
        now = datetime.now(timezone.utc).replace(microsecond=0)
        expire = now + timedelta(days=expire_days)
        db_refresh = RefreshTokens(user_id=refresh.user_id, uuid=refresh.uuid, expires_at=int(expire.timestamp()))
        self.db.add(db_refresh)
        await self.db.commit()
        await self.db.refresh(db_refresh)
        return db_refresh
    
    async def set_refresh_google(self, user_id: int, token: str, expire_s: int) -> None:
        now = datetime.now(timezone.utc).replace(microsecond=0)
        expire = now + timedelta(seconds=expire_s)
        db_refresh = RefreshGoogle(user_id=user_id, token=token, expires_at=int(expire.timestamp()))
        self.db.add(db_refresh)
        # await self.db.commit()
        # await self.db.refresh(db_refresh)
        # return db_refresh
    async def delete_refresh_google(self, user_id:int) -> None:
        query = delete(RefreshGoogle).where(RefreshGoogle.user_id == user_id)
        res = await self.db.execute(query)

    async def is_exist (self, uuid: str) -> Optional[RefreshTokens]:
        query = select(RefreshTokens).where(RefreshTokens.uuid == uuid, RefreshTokens.expires_at > int(datetime.now(timezone.utc).timestamp())).options(joinedload(RefreshTokens.user))
        res = await self.db.execute(query)
        return res.scalar()
    
    async def get_by_email (self, email: str) -> Optional[List[Users]]:
        query = select(Users).where(Users.email == email)
        res = await self.db.execute(query)
        return res.unique().scalars().all()
    
    async def get_by_id(self, Id: int) -> Users:
        query = select(Users).where(Users.tid == Id)
        res = await self.db.execute(query)
        return res.scalar() 
    async def add_totp (self, tid: int, key: str) -> None:
        db_refresh = TOTPTokens(user_id=tid,token=key)
        self.db.add(db_refresh)
        await self.db.commit()
        await self.db.refresh(db_refresh)
    async def get_by_id_totp(self, tid: int) -> Optional[Users]:
        query = select(Users).where(Users.tid == tid).options(joinedload(Users.potptoken))
        res = await self.db.execute(query)
        return res.scalar() 
    async def get_by_id_google(self, tid: int) -> Optional[Users]:
        query = select(Users).where(Users.tid == tid).options(joinedload(Users.refresh_google))
        res = await self.db.execute(query)
        return res.scalar() 
    async def set_access_google(self, user_id: int, token: str, expire_s: int) -> Optional[AccessGoogle]:
        now = datetime.now(timezone.utc).replace(microsecond=0)
        expire = now + timedelta(seconds=expire_s)
        db_refresh = AccessGoogle(user_id=user_id, token=token, expires_at=int(expire.timestamp()))
        self.db.add(db_refresh)
        await self.db.commit()
        await self.db.refresh(db_refresh)
        return db_refresh
    async def get_by_id_google_access(self, tid: int) -> Optional[AccessGoogle]:
        query = select(AccessGoogle).where(AccessGoogle.tid == tid)
        res = await self.db.execute(query)
        return res.scalar()  
    
    async def update_access_google(self, user_id: int, new_token: str, expire_s: int) -> Optional[AccessGoogle]:
        """Обновляет access_token для Google по tid записи в таблице AccessGoogle."""
        record_to_update = await self.db.get(AccessGoogle, user_id)
        if record_to_update:
            now = datetime.now(timezone.utc).replace(microsecond=0)
            expire = now + timedelta(seconds=expire_s)
            record_to_update.token = new_token
            record_to_update.expires_at = int(expire.timestamp())
            await self.db.commit()
            await self.db.refresh(record_to_update)
        return record_to_update
class LoginRepositoryHTTP ():
    async def google_Callback(self, params):
        async with ClientSession() as sessionhttp, sessionhttp.post('https://oauth2.googleapis.com/token', data=params) as response:
            return await response.json()
    
    async def google_refresh(self, params):
        async with ClientSession() as sessionhttp, sessionhttp.post('https://oauth2.googleapis.com/token', data=params) as response:
            return await response.json()
        
    async def revoke_google (self, token:str):
        async with ClientSession() as sessionhttp, sessionhttp.post(f'https://oauth2.googleapis.com/revoke?token={token}', headers={'Content-Type': 'application/x-www-form-urlencoded'}) as response:
            return await response.json()

    async def get_google_file (self, access_token: str):
        async with ClientSession() as sessionhttp, sessionhttp.get('https://www.googleapis.com/drive/v3/files', headers={'Authorization': f'Bearer {access_token}'}) as response:
            return await response.json()
        # return db_refresh
    # async def add_totp (self, tid: int):
    #     pass