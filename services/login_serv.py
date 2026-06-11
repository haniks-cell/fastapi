from typing import List
from repositories.login import LoginRepository, LoginRepositoryHelp
from schemas.login import LoginCreate, LoginCreateResponse, LoginGet, ResponseServiceLogin, RefreshTokensCreate
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import uuid


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