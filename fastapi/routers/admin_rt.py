from time import time
import uuid
# from jwt.exceptions import InvalidTokenError
from fastapi import APIRouter, Depends, status, HTTPException, Header, Response, Cookie, Form
from typing import Annotated, Any, Awaitable, Callable, Dict, Union
from sqlalchemy.ext.asyncio import async_sessionmaker
from database import session_maker
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import HTTPBasic, HTTPBasicCredentials, HTTPBearer, HTTPAuthorizationCredentials
import secrets

from routers.products_rt import AccDep
from schemas.admin import GetAccountAnotherUser, ResponseId, AdminStatusResponse, GetAccountAnotherUserEmail
from repositories.admin_rep import AdminRepository
from services.admin_serv import AdminService

from dependses import SesDep

from models.login import Users


# GetLvlDep = Annotated[int, Depends(get_lvl_access)]

async def admin_required(lvl_access: AccDep):
    """Зависимость для проверки прав администратора."""
    if lvl_access < 5:  # Предполагаем, что уровень доступа админа >= 3
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Требуются права администратора")


router = APIRouter(
    prefix='/api/admin',
    tags=['admin'],
    dependencies=[Depends(admin_required)]
)

async def get_admin_service(session: SesDep) -> AdminService:
    return AdminService(session)

adminservDep = Annotated[AdminService, Depends(get_admin_service)]

@router.post('/change_lvl_access/', response_model=AdminStatusResponse, status_code=status.HTTP_200_OK)
async def change_lvl_access (user: GetAccountAnotherUser, serv: adminservDep, lvl: AccDep):
    if user.new_lvl_access >= lvl:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Your level access less than or equal to the level you want to change")
    # serv = AdminService(session)
    if not await serv.change_lvl_access(GetAccountAnotherUser(id_user=user.id_user, new_lvl_access=user.new_lvl_access)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='user not found')
    return AdminStatusResponse(ok=True)

@router.get('/get_id_by_username/', response_model=ResponseId, status_code=status.HTTP_200_OK)
async def get_id_by_username (username: str, session: SesDep):
    rep = AdminRepository(session)
    return ResponseId(id_user=await rep.get_by_username(username))

@router.post('/change_email/', response_model=AdminStatusResponse, status_code=status.HTTP_200_OK)
async def change_email (email: GetAccountAnotherUserEmail, serv: adminservDep, lvl: AccDep):
    # serv = AdminService(session)
    if not await serv.change_email(email):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='user not found')
    return AdminStatusResponse(ok=True)