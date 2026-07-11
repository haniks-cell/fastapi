import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from models.login import Users
from models.product import Category, Product
from repositories.login import LoginRepositoryHelp

pytestmark = pytest.mark.asyncio

lgrp = LoginRepositoryHelp()

async def test_add_category_success(client: AsyncClient, db: AsyncSession, admin_user: Users):
    jwt_payload = {
        "sub": str(admin_user.tid),
        "username": admin_user.username,
        "lvl_access": admin_user.lvl_access
    }
    admin_token = lgrp.encode_jwt(jwt_payload)
    client.cookies.set("access", admin_token)

    response = await client.put("/api/products/add_cat/", params={"name": "New Category"})

    assert response.status_code == 200
    assert response.json() == {"ok": admin_user.lvl_access}

    # Проверяем, что категория действительно добавлена в БД
    category = await db.get(Category, 1) # Предполагаем, что это будет первая категория
    assert category is not None
    assert category.name == "New Category"

async def test_add_category_forbidden(client: AsyncClient, db: AsyncSession):
    # Создаем обычного пользователя (lvl_access < 3)
    user = Users(username="regular_user", email="user@example.com", hash_password=lgrp.hash_password("password").decode('utf-8'), lvl_access=1)
    db.add(user)
    await db.commit()
    await db.refresh(user)

    jwt_payload = {
        "sub": str(user.tid),
        "username": user.username,
        "lvl_access": user.lvl_access
    }
    user_token = lgrp.encode_jwt(jwt_payload)
    client.cookies.set("access", user_token)

    response = await client.put("/api/products/add_cat/", params={"name": "Forbidden Category"})

    assert response.status_code == 403
    assert response.json() == {"detail": "not roule"}

async def test_add_product_success(client: AsyncClient, db: AsyncSession, admin_user: Users):
    jwt_payload = {
        "sub": str(admin_user.tid),
        "username": admin_user.username,
        "lvl_access": admin_user.lvl_access
    }
    admin_token = lgrp.encode_jwt(jwt_payload)
    client.cookies.set("access", admin_token)

    # Сначала создаем категорию, так как продукт на нее ссылается
    category = Category(name="Electronics", slug="electronics")
    db.add(category)
    await db.commit()
    await db.refresh(category)

    product_data = {
        "name": "Laptop",
        "description": "Powerful laptop",
        "price": 1200.0,
        "category_id": category.id,
        "image_url": "http://example.com/laptop.jpg"
    }
    response = await client.put("/api/products/add_prod/", json=product_data)

    assert response.status_code == 200
    assert response.json() == {"ok": True}

    # Проверяем, что продукт действительно добавлен в БД
    product = await db.get(Product, 1)
    assert product is not None
    assert product.name == "Laptop"

async def test_get_all_products(client: AsyncClient, db: AsyncSession):
    # Создаем категорию
    category = Category(name="Books", slug="books")
    db.add(category)
    await db.commit()
    await db.refresh(category)

    # Создаем несколько тестовых продуктов
    prod1 = Product(name="Book 1", description="Desc 1", price=10.0, category_id=category.id, image_url="url1")
    prod2 = Product(name="Book 2", description="Desc 2", price=15.0, category_id=category.id, image_url="url2")
    db.add_all([prod1, prod2])
    await db.commit()
    await db.refresh(prod1)
    await db.refresh(prod2)

    response = await client.get("/api/products/products/")

    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.json()[0]["name"] == "Book 1"
    assert response.json()[1]["name"] == "Book 2"