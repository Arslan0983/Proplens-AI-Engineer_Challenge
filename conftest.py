"""
Pytest configuration and fixtures.
"""

import pytest
import os
from django.conf import settings
from django.test import Client
from api.auth import create_jwt_token


@pytest.fixture
def client():
    """Django test client."""
    return Client()


@pytest.fixture
def auth_headers():
    """Generate JWT token for authenticated requests."""
    token = create_jwt_token("test_user")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup test environment before all tests."""
    # Set test environment variables
    os.environ.setdefault('GEMINI_API_KEY', 'test_key')
    os.environ.setdefault('SECRET_KEY', 'test_secret_key')
    os.environ.setdefault('JWT_SECRET_KEY', 'test_jwt_secret')
    
    yield
    
    # Cleanup if needed

