from datetime import timedelta, datetime, timezone
from models.login import Users, RefreshTokens
from schemas.login import LoginCreate, TokenJwt, RefreshTokensCreate
import jwt
import bcrypt
from schemas.login import setting
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

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
        decoded = jwt.decode(jwts, key, algorithms=[alhoritm])
        # return decoded
        # print('posle')
        return TokenJwt(sub=int(decoded['sub']), username=decoded['username'], lvl_access=int(decoded['lvl_access']), exp=int(decoded['exp']), iat=int(decoded['iat']))
        # return TokenJwt(sub=1, username='fff', email=)
    
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
    
    async def is_exist (self, uuid: str) -> Optional[RefreshTokens]:
        query = select(RefreshTokens).where(RefreshTokens.uuid == uuid, RefreshTokens.expires_at > int(datetime.now(timezone.utc).timestamp())).options(joinedload(RefreshTokens.user))
        res = await self.db.execute(query)
        return res.scalar()