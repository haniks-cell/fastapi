from datetime import timedelta, datetime, timezone
import json
# from models.login import Users, RefreshTokens, TOTPTokens, RefreshGoogle, AccessGoogle
from models.main import Errors
from schemas.main import AddErrors
# from schemas.login import LoginCreate, TokenJwt, RefreshTokensCreate, AccessGoogleCreate
import jwt
import bcrypt
from schemas.login import setting
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete


class MainRepository():
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_errors (self, user: AddErrors) -> Errors:
        db_user = Errors(**user.model_dump())
        self.db.add(db_user)
        await self.db.commit()
        await self.db.refresh(db_user)
        return db_user