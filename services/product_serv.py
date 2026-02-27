from sqlalchemy.orm import Session
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from repositories.product_rep import ProductRepository
from repositories.category_rep import CategoryRepository
from ..schemas.product import ProductResponse, ProductListResponse, ProductCreate
from fastapi import HTTPException, status

class ProductService:
    def __init__(self, db: AsyncSession):
        self.product_repository = ProductRepository(db)
        self.category_repository = CategoryRepository(db)

    async def get_all_products(self) -> ProductListResponse:
        products = await self.product_repository.get_all()
        products_response = [ProductResponse.model_validate(prod) for prod in products]
        return ProductListResponse(products=products_response, total=len(products_response))

    async def get_product_by_id(self, product_id: int) -> ProductResponse:
        product = await self.product_repository.get_by_id(product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with id {product_id} not found"
            )
        return ProductResponse.model_validate(product)

    async def get_products_by_category(self, category_id: int) -> ProductListResponse:
        category = await self.category_repository.get_by_id(category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category with id {category_id} not found"
            )
        # category.products
        products = await self.product_repository.get_by_category(category_id)
        products_response = [ProductResponse.model_validate(prod) for prod in products]
        return ProductListResponse(products=products_response, total=len(products_response))

    async def create_product(self, product_data: ProductCreate) -> ProductResponse:
        category = await self.category_repository.get_by_id(product_data.category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category with id {product_data.category_id} does not exist"
            )

        product = await self.product_repository.create(product_data)
        return ProductResponse.model_validate(product)