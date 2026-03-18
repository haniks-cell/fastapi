from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.product import Product
from schemas.product import ProductCreate
from models.product import Category
from schemas.category import CategoryCreate

class ProductRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self) -> List[Product]:
        query = select(Product).options(joinedload(Product.category))
        res = await self.db.execute(query)
        return res.unique().scalars().all()
    
    async def get_by_id(self, tid: int) -> Optional[Product]:
        query = select(Product).where(Product.id == tid).options(joinedload(Product.category))
        res = await self.db.execute(query)
        return res.scalar()
    
    async def get_by_category(self, category_id: int) -> List[Product]:
        query = select(Product).where(Product.category_id == category_id).options(joinedload(Product.category))
        res = await self.db.execute(query)
        return res.unique().scalars().all()
    
    async def create(self, category_data: ProductCreate) -> Product:
        db_category = Product(**category_data.model_dump())
        self.db.add(db_category)
        await self.db.commit()
        await self.db.refresh(db_category)
        return db_category
    
    async def get_multiple_by_ids(self, product_ids: List[int]) -> List[Product]:
        query = select(Product).where(Product.id.in_(product_ids)).options(joinedload(Product.category))
        res = await self.db.execute(query)
        return res.unique().scalars().all()
    
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