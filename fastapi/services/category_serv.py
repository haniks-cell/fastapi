from typing import List
from repositories.category_rep import CategoryRepository
from schemas.category import CategoryResponse, CategoryCreate
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

class CategoryService:
    def __init__(self, db: AsyncSession):
        self.repository = CategoryRepository(db)

    async def get_all_categories(self, page: int) -> List[CategoryResponse]:
        limit = 10
        offset=(page-1)*limit
        categories = await self.repository.get_all(offset=offset,limit=limit)
        return [CategoryResponse.model_validate(cat) for cat in categories]

    async def get_category_by_id(self, category_id: int) -> CategoryResponse:
        category = await self.repository.get_by_id(category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f'Category with id {category_id} not found'
            )
        return CategoryResponse.model_validate(category)

    async def create_category(self, category_data: CategoryCreate) -> CategoryResponse:
        category = await self.repository.create(category_data)
        return CategoryResponse.model_validate(category)