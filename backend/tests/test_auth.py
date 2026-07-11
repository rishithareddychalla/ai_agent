"""
Integration tests for Authentication API endpoints
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.core.database import get_db
from app.models.user import User


@pytest.fixture
def mock_db():
    db = MagicMock(spec=AsyncSession)
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    return db


def test_register_success(mock_db):
    # Mock that email doesn't exist
    mock_execute_result = MagicMock()
    mock_execute_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_execute_result
    
    # Overwrite get_db dependency
    app.dependency_overrides[get_db] = lambda: mock_db
    
    client = TestClient(app)
    response = client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "password": "securepassword123",
            "full_name": "Test User"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["email"] == "test@example.com"
    assert data["full_name"] == "Test User"
    
    # Clean up overrides
    app.dependency_overrides.clear()


def test_register_duplicate_email(mock_db):
    # Mock that email already exists
    mock_user = User(email="test@example.com")
    mock_execute_result = MagicMock()
    mock_execute_result.scalar_one_or_none.return_value = mock_user
    mock_db.execute.return_value = mock_execute_result
    
    app.dependency_overrides[get_db] = lambda: mock_db
    
    client = TestClient(app)
    response = client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "password": "securepassword123",
            "full_name": "Test User"
        }
    )
    
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"
    
    app.dependency_overrides.clear()


def test_login_success(mock_db):
    from app.core.security import get_password_hash
    
    # Mock that user exists with hashed password
    hashed = get_password_hash("securepassword123")
    mock_user = User(
        id=42,
        email="test@example.com",
        hashed_password=hashed,
        full_name="Test User",
        is_active=True
    )
    
    mock_execute_result = MagicMock()
    mock_execute_result.scalar_one_or_none.return_value = mock_user
    mock_db.execute.return_value = mock_execute_result
    
    app.dependency_overrides[get_db] = lambda: mock_db
    
    client = TestClient(app)
    response = client.post(
        "/auth/login",
        data={
            "username": "test@example.com",
            "password": "securepassword123"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user_id"] == 42
    
    app.dependency_overrides.clear()


def test_login_invalid_credentials(mock_db):
    # Mock that user doesn't exist
    mock_execute_result = MagicMock()
    mock_execute_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_execute_result
    
    app.dependency_overrides[get_db] = lambda: mock_db
    
    client = TestClient(app)
    response = client.post(
        "/auth/login",
        data={
            "username": "nonexistent@example.com",
            "password": "wrongpassword"
        }
    )
    
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"
    
    app.dependency_overrides.clear()
