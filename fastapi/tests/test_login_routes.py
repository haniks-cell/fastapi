import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from models.login import Users
from repositories.login import LoginRepositoryHelp

pytestmark = pytest.mark.asyncio

lgrp = LoginRepositoryHelp()

async def test_registration_success(client: AsyncClient):
    user_data = {
        "username": "newuser",
        "hash_password": "securepassword",
        "email": "another@example.com"
    }
    response = await client.put("/api/auth/registration/", json=user_data)

    assert response.status_code == 200
    assert response.json() == {"ok": True}

async def test_registration_duplicate_username(client: AsyncClient, db: AsyncSession):
    # Создаем пользователя напрямую в БД
    existing_user = Users(username="existinguser", hash_password=lgrp.hash_password("password").decode('utf-8'), email="existing@example.com", lvl_access=0)
    db.add(existing_user)
    await db.commit()

    user_data = {
        "username": "existinguser",
        "hash_password": "anotherpassword",
        "email": "another@example.com"
    }
    response = await client.put("/api/auth/registration/", json=user_data)

    assert response.status_code == 409
    assert response.json() == {"detail": "User with this username already exists"}

async def test_login_success(client: AsyncClient, db: AsyncSession):
    # Создаем пользователя для логина
    user_password = "testpassword"
    user = Users(username="loginuser", hash_password=lgrp.hash_password(user_password).decode('utf-8'), email="login@example.com", lvl_access=0)
    db.add(user)
    await db.commit()

    login_data = {
        "username": "loginuser",
        "hash_password": user_password
    }
    response = await client.post("/api/auth/login/", json=login_data)

    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "refresh_token" in response.json()
    assert "access" in response.cookies
    assert "refresh" in response.cookies

async def test_login_invalid_credentials(client: AsyncClient):
    login_data = {
        "username": "nonexistent",
        "hash_password": "wrongpassword"
    }
    response = await client.post("/api/auth/login/", json=login_data)

    assert response.status_code == 401
    assert response.json() == {"detail": "inalid username or password"}

async def test_refresh_token_success(client: AsyncClient, db: AsyncSession):
    # Создаем пользователя и логинимся, чтобы получить refresh токен
    user_password = "refreshpassword"
    user = Users(username="refreshuser", hash_password=lgrp.hash_password(user_password).decode('utf-8'), email="refresh@example.com", lvl_access=0)
    db.add(user)
    await db.commit()

    login_data = {
        "username": "refreshuser",
        "hash_password": user_password
    }
    login_response = await client.post("/api/auth/login/", json=login_data)
    
    refresh_cookie = login_response.cookies.get("refresh")
    assert refresh_cookie is not None

    # Используем refresh токен для получения нового access токена
    client.cookies.set("refresh", refresh_cookie)
    response = await client.get("/api/auth/refresh/")

    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "refresh_token" in response.json()
    assert "access" in response.cookies
    assert "refresh" in response.cookies
    assert response.cookies["refresh"] != refresh_cookie # Убедимся, что refresh токен обновился

async def test_refresh_token_invalid(client: AsyncClient):
    # Пытаемся обновить с невалидным refresh токеном
    client.cookies.set("refresh", "invalid_refresh_token")
    response = await client.get("/api/auth/refresh/")

    assert response.status_code == 401
    assert response.json() == {"detail": "refresh not found"}