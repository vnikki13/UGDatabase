import jwt
import requests
from datetime import datetime, timedelta
from typing import Optional
from app.core.config import settings


class GhostAdminClient:
    """Client for interacting with Ghost Admin API"""

    def __init__(self, url: str, key: str):
        self.url = url.rstrip('/')
        self.api_url = f"{self.url}/ghost/api/admin"

        # Parse the key (format: id:secret)
        key_parts = key.split(':')
        if len(key_parts) != 2:
            raise ValueError(
                "Invalid Ghost Admin API key format. Expected 'id:secret'")

        self.key_id = key_parts[0]
        self.key_secret = key_parts[1]

    def _generate_token(self) -> str:
        """Generate a JWT token for Ghost Admin API authentication"""
        # Token expires in 5 minutes
        iat = int(datetime.utcnow().timestamp())
        exp = int((datetime.utcnow() + timedelta(minutes=5)).timestamp())

        payload = {
            'iat': iat,
            'exp': exp,
            'aud': '/admin/'
        }

        # The key_id goes in the header
        headers = {
            'kid': self.key_id,
            'alg': 'HS256'
        }

        token = jwt.encode(
            payload,
            bytes.fromhex(self.key_secret),
            algorithm='HS256',
            headers=headers
        )

        return token

    def _make_request(self, method: str, endpoint: str, data: Optional[dict] = None) -> dict:
        """Make an authenticated request to the Ghost Admin API"""
        token = self._generate_token()

        headers = {
            'Authorization': f'Ghost {token}',
            'Content-Type': 'application/json'
        }

        url = f"{self.api_url}/{endpoint}"

        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            json=data,
            timeout=30
        )

        response.raise_for_status()
        return response.json()

    def get_users(self) -> dict:
        """Get all users from Ghost"""
        return self._make_request('GET', 'users/')

    def get_user(self, user_id: str) -> dict:
        """Get a specific user by ID"""
        return self._make_request('GET', f'users/{user_id}/')

    def validate_user_by_email(self, email: str) -> dict:
        """Validate if a user with given email exists and is active"""
        # Get all users
        response = self._make_request('GET', 'users/')
        users = response.get('users', [])

        # Find user with matching email
        user = next((u for u in users if u.get('email') == email), None)

        if not user:
            raise ValueError(f"User with email '{email}' not authorized")

        if user.get('status') != 'active':
            raise ValueError(
                f"User with email '{email}' is not active (status: {user.get('status')})")

        return user


# Initialize the Ghost client with settings
def get_ghost_client() -> GhostAdminClient:
    """Get an initialized Ghost Admin API client"""
    return GhostAdminClient(
        url=settings.GHOST_URL,
        key=settings.GHOST_ADMIN_KEY
    )
