from typing import Any

import pytest
from httpx import AsyncClient

from core.config import settings
from src import models
from src.auth.security_guards import get_current_user, verify_api_key
from src.main import app


@pytest.mark.asyncio
class TestUserRoutes:
    @pytest.fixture(autouse=True)
    def setup_auth_override(self):
        # 1. Nest the mock functions inside the fixture
        # 2. Add type hints to satisfy Pylance
        def override_verify_api_key() -> models.User:
            return models.User(
                uid=settings.GUEST_UID,
                role="guest",
                email="guest@example.com",
            )

        def override_get_current_user() -> dict[str, Any]:
            return {"id": "some-id", "email": "admin@example.com"}

        # Apply the overrides
        app.dependency_overrides[verify_api_key] = override_verify_api_key
        app.dependency_overrides[get_current_user] = override_get_current_user

        yield
        # Cleanup after each test
        app.dependency_overrides = {}

    async def test_register_success(self, client: AsyncClient):
        payload = {
            "firstName": "Juan",
            "lastName": "Dela Cruz",
            "email": "juan@example.com",
            "password": "strongpassword123",
        }
        headers = {
            "Authorization": "Bearer mock-token",
            "x-api-key": str(settings.GUEST_UID),
        }

        response = await client.post("/v1/register", json=payload, headers=headers)
        if response.status_code == 422:
            print("\nPYDANTIC ERROR DETAILS:", response.json())

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "juan@example.com"
        assert "uid" in data

    async def test_register_duplicate_email(self, client: AsyncClient):
        payload = {
            "firstName": "Juan",
            "lastName": "Dela Cruz",
            "email": "duplicate@example.com",
            "password": "password",
        }
        headers = {"Authorization": "Bearer mock-token"}

        await client.post("/v1/register", json=payload, headers=headers)
        response = await client.post("/v1/register", json=payload, headers=headers)

        assert response.status_code == 404
        assert response.json()["detail"]["error"]["code"] == "ERR_EMAIL_ALREADY_EXISTS"

    async def test_login_success(self, client: AsyncClient):
        reg_payload = {
            "firstName": "Test",
            "lastName": "User",
            "email": "login@example.com",
            "password": "mypassword",
        }
        await client.post(
            "/v1/register", json=reg_payload, headers={"Authorization": "Bearer token"}
        )

        login_data = {"username": "login@example.com", "password": "mypassword"}
        response = await client.post("/v1/authenticate", data=login_data)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data["token"]
        assert "id_token" in data["token"]

    async def test_login_invalid_password(self, client: AsyncClient):
        login_data = {"username": "login@example.com", "password": "wrongpassword"}
        response = await client.post("/v1/authenticate", data=login_data)

        assert response.status_code == 401
        assert response.json()["detail"] == "Incorrect email or password"
