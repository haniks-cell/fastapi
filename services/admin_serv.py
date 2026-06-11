from typing import List
from repositories.category_rep import CategoryRepository
from schemas.category import CategoryResponse, CategoryCreate
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from repositories.admin_rep import AdminRepository
from schemas.admin import GetAccountAnotherUser, GetAccountAnotherUserEmail

class AdminService:
    def __init__(self, db: AsyncSession):
        self.rep = AdminRepository(db)
    async def change_lvl_access(self, user: GetAccountAnotherUser) -> bool:
        user_to_update = await self.rep.get_by_id(user.id_user)
        if not user_to_update:
            return False # Пользователь не найден
        user_to_update.lvl_access = user.new_lvl_access
        await self.rep.update_user(user_to_update)
        return True
    async def change_email(self, user: GetAccountAnotherUserEmail) -> bool:
        user_to_update = await self.rep.get_by_id(user.id_user)
        if not user_to_update:
            return False # Пользователь не найден
        user_to_update.email = user.new_email
        await self.rep.update_user(user_to_update)
        return True