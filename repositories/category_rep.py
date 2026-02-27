from sqlalchemy.orm import Session
from typing import List, Optional
from models.product import Category
from schemas.category import CategoryCreate
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

class CategoryRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self) -> List[Category]:
        query = select(Category)
        res = await self.db.execute(query)
        return res.unique().scalars().all()
    
    async def get_by_id(self, tid: int) -> Optional[Category]:
        query = select(Category).where(Category.id == tid)
        res = await self.db.execute(query)
        return res.scalar()
    
    async def get_by_slug(self, slug:str) -> Optional[Category]:
        query = select(Category).where(Category.slug == slug)
        res = await self.db.execute(query)
        return res.scalar()
    
    async def create(self, category_data: CategoryCreate) -> Category:
        db_category = Category(**category_data.model_dump())
        self.db.add(db_category)
        await self.db.commit()
        await self.db.refresh(db_category)
        return db_category