from typing import List
from repositories.category_rep import CategoryRepository
from schemas.category import CategoryResponse, CategoryCreate
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from repositories.admin_rep import AdminRepository
from schemas.admin import GetAccountAnotherUser

class AdminService:
    def __init__(self, db: AsyncSession):
        self.rep = AdminRepository(db)
    async def change_lvl_access(self, user: GetAccountAnotherUser) -> bool:
        new_user = await self.rep.change_lvl_access(user.id_user)
        new_user.lvl_access = user.new_lvl_access
        self.rep.db.add(new_user)
        await self.rep.db.commit()
        await self.rep.db.refresh(new_user)
        return True