"""
JWT Authentication utilities.
"""

import jwt
from datetime import datetime, timedelta
from typing import Optional
from django.conf import settings
from ninja.security import HttpBearer
from django.http import HttpRequest


class JWTAuth(HttpBearer):
    """JWT Authentication scheme for Django Ninja."""
    
    def authenticate(self, request: HttpRequest, token: str) -> Optional[str]:
        """Authenticate the request using JWT token."""
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            return payload.get('user_id')
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None


def create_jwt_token(user_id: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT token for a user."""
    if expires_delta is None:
        expires_delta = timedelta(days=7)  # Tokens valid for 7 days
    
    expire = datetime.utcnow() + expires_delta
    
    payload = {
        'user_id': user_id,
        'exp': expire,
        'iat': datetime.utcnow()
    }
    
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token


# For testing purposes, create a test token generator
def get_test_token() -> str:
    """Generate a test JWT token. In production, this would come from a login endpoint."""
    return create_jwt_token("test_user")

