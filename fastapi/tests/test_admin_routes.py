import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from models.login import Users
from repositories.login import LoginRepository, LoginRepositoryHelp
pytestmark = pytest.mark.asyncio

lgrp = LoginRepositoryHelp()

async def test_change_lvl_access_success(client: AsyncClient, db: AsyncSession, admin_user: Users):
    # Создаем JWT токен для нашего тестового администратора
    jwt_payload = {
        "sub": str(admin_user.tid),
        "username": admin_user.username,
        "lvl_access": admin_user.lvl_access
    }
    admin_token = lgrp.encode_jwt(jwt_payload)

    # Устанавливаем токен в cookie для клиента
    client.cookies.set("access", admin_token)

    # Создаем пользователя, которого будем изменять
    user_to_change = Users(username="testuser", email="test@user.com", hash_password=lgrp.hash_password("password").decode('utf-8'), lvl_access=1)
    db.add(user_to_change) # Добавляем пользователя в тестовую БД
    await db.commit()
    await db.refresh(user_to_change)

    response = await client.post(
        "/api/admin/change_lvl_access/", # Используем POST вместо PATCH
        json={"id_user": user_to_change.tid, "new_lvl_access": 2},
    )

    assert response.status_code == 200
    assert response.json() == {"ok": True} # Исправленный ожидаемый ответ

    await db.refresh(user_to_change)
    assert user_to_change.lvl_access == 2


async def test_change_lvl_access_user_not_found(client: AsyncClient, admin_user: Users):
    jwt_payload = {
        "sub": str(admin_user.tid),
        "username": admin_user.username,
        "lvl_access": admin_user.lvl_access
    }
    admin_token = lgrp.encode_jwt(jwt_payload)
    client.cookies.set("access", admin_token)

    response = await client.post(
        "/api/admin/change_lvl_access/", # Используем POST вместо PATCH
        json={"id_user": 999, "new_lvl_access": 2},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "user not found"}


async def test_change_email_success(client: AsyncClient, db: AsyncSession, admin_user: Users):
    jwt_payload = {
        "sub": str(admin_user.tid),
        "username": admin_user.username,
        "lvl_access": admin_user.lvl_access
    }
    admin_token = lgrp.encode_jwt(jwt_payload)
    client.cookies.set("access", admin_token)

    user_to_change = Users(username="testuser2", email="test2@user.com", hash_password=lgrp.hash_password("password").decode('utf-8'), lvl_access=1)
    db.add(user_to_change)
    await db.commit()
    await db.refresh(user_to_change)

    new_email = "new.email@example.com"
    response = await client.post(
        "/api/admin/change_email/",
        json={"id_user": user_to_change.tid, "new_email": new_email},
    )

    assert response.status_code == 200
    assert response.json() == {"ok": True}

    await db.refresh(user_to_change)
    assert user_to_change.email == new_email

async def test_change_email_user_not_found(client: AsyncClient, admin_user: Users):
    jwt_payload = {
        "sub": str(admin_user.tid),
        "username": admin_user.username,
        "lvl_access": admin_user.lvl_access
    }
    admin_token = lgrp.encode_jwt(jwt_payload)
    client.cookies.set("access", admin_token)

    response = await client.post(
        "/api/admin/change_email/", # Используем POST вместо PATCH
        json={"id_user": 999, "new_email": "new@email.com"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "user not found"}


async def test_get_id_by_username_success(client: AsyncClient, db: AsyncSession, admin_user: Users):
    jwt_payload = {
        "sub": str(admin_user.tid),
        "username": admin_user.username,
        "lvl_access": admin_user.lvl_access
    }
    admin_token = lgrp.encode_jwt(jwt_payload)
    client.cookies.set("access", admin_token)

    # Создаем пользователя, которого будем искать
    target_username = "find_me"
    user_to_find = Users(username=target_username, email="findme@example.com", hash_password=lgrp.hash_password("password").decode('utf-8'), lvl_access=1)
    db.add(user_to_find)
    await db.commit()
    await db.refresh(user_to_find)

    response = await client.get(f"/api/admin/get_id_by_username/?username={target_username}")

    assert response.status_code == 200
    assert response.json() == {"id_user": user_to_find.tid}