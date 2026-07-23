from typing import List

from pydantic import EmailStr
from schemas.main import AddErrors
from repositories.main_rep import MainRepository
# from dependses import RedisDep
# from repositories.login import LoginRepository, LoginRepositoryHelp, LoginRepositoryHTTP
# from schemas.login import LoginCreate, LoginCreateResponse, LoginGet, ResponseServiceLogin, RefreshTokensCreate, LoginCreateInp,  GoogleIdTokenPayload, GoogleOAUTHResponse
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
    def __init__(self, db: AsyncSession):
        self.rep = MainRepository(db)

    async def addErrors(self, AddErrors: AddErrors) -> bool:
        await self.rep.add_errors(AddErrors)
        return True