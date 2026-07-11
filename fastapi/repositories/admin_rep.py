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

from schemas.admin import GetAccountAnotherUser
# from decorator import complited_time

class AdminRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    # async def upd_jwt(self, Id: int) -> bool:
    #     query = delete(RefreshTokens).where(RefreshTokens.user_id == Id)
    #     res = await self.db.execute(query)
    async def get_by_id(self, Id: int) -> Users:
        query = select(Users).where(Users.tid == Id)
        res = await self.db.execute(query)
        return res.scalar()
    async def get_by_username(self, username: str) -> Optional[int]:
        query = select(Users).where(Users.username == username)
        res = await self.db.execute(query)
        return res.scalar().tid
    
    async def update_user(self, user_to_update: Users) -> Users:
        """Сохраняет изменения для существующего пользователя."""
        self.db.add(user_to_update)
        await self.db.commit()
        await self.db.refresh(user_to_update)
        return user_to_update
    # async def set_user (self, user: LoginCreate) -> Users:
    #     db_user = Users(**user.model_dump())
    #     self.db.add(db_user)
    #     await self.db.commit()
    #     await self.db.refresh(db_user)
    #     return db_user

    # async def get_by_username(self, username: str) -> Optional[Users]:
    #     query = select(Users).where(Users.username == username)
    #     res = await self.db.execute(query)
    #     return res.scalar()
    
    # async def delete_refresh(self, user_id:str) -> None:
    #     query = delete(RefreshTokens).where(RefreshTokens.user_id == user_id)
    #     res = await self.db.execute(query)

    # async def set_refresh(self, refresh: RefreshTokensCreate, expire_days: int = setting.auth_jwt.refresh_token_days) -> RefreshTokens:
    #     await self.delete_refresh(refresh.user_id)
    #     now = datetime.now(timezone.utc).replace(microsecond=0)
    #     expire = now + timedelta(days=expire_days)
    #     db_refresh = RefreshTokens(user_id=refresh.user_id, uuid=refresh.uuid, expires_at=int(expire.timestamp()))
    #     self.db.add(db_refresh)
    #     await self.db.commit()
    #     await self.db.refresh(db_refresh)
    #     return db_refresh
    
    # async def is_exist (self, uuid: str) -> Optional[RefreshTokens]:
    #     query = select(RefreshTokens).where(RefreshTokens.uuid == uuid, RefreshTokens.expires_at > int(datetime.now(timezone.utc).timestamp())).options(joinedload(RefreshTokens.user))
    #     res = await self.db.execute(query)
    #     return res.scalar()