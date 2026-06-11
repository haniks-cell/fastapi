from typing import List
from repositories.login import LoginRepository
from schemas.login import LoginCreate, LoginCreateResponse
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

class LoginService:
    def __init__(self, db: AsyncSession):
        self.rep = LoginRepository(db)

    async def create_user(self, user_data: LoginCreate) -> LoginCreateResponse:
        try:
            user = await self.rep.set_user(user_data)
            return LoginCreateResponse(ok=True)
        except IntegrityError:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User with this username already exists")

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