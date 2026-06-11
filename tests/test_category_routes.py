import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from models.login import Users
from models.product import Category
from repositories.login import LoginRepositoryHelp

pytestmark = pytest.mark.asyncio

lgrp = LoginRepositoryHelp()

async def test_get_all_categories(client: AsyncClient, db: AsyncSession):
    # Создаем несколько тестовых категорий
    cat1 = Category(name="Category 1", slug="category-1")
    cat2 = Category(name="Category 2", slug="category-2")
    db.add_all([cat1, cat2])
    await db.commit()
    await db.refresh(cat1)
    await db.refresh(cat2)

    response = await client.get("/api/categories/")

    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.json()[0]["name"] == "Category 1"
    assert response.json()[1]["name"] == "Category 2"

async def test_get_category_by_id(client: AsyncClient, db: AsyncSession):
    # Создаем тестовую категорию
    cat = Category(name="Test Category", slug="test-category")
    db.add(cat)
    await db.commit()
    await db.refresh(cat)

    response = await client.get(f"/api/categories/{cat.id}")

    assert response.status_code == 200
    assert response.json()["id"] == cat.id
    assert response.json()["name"] == "Test Category"
    assert response.json()["slug"] == "test-category"