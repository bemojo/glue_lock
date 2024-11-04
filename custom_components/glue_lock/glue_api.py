"""API Client for Glue Lock."""
import logging
import base64
import aiohttp

_LOGGER = logging.getLogger(__name__)

class GlueApiError(Exception):
    """Exception for API errors."""

class GlueAuthError(GlueApiError):
    """Authentication error."""

class GlueApi:
    """API Client for Glue Lock."""

    def __init__(self, session: aiohttp.ClientSession = None):
        """Initialize the API client."""
        self._api_key = None
        self._session = session or aiohttp.ClientSession()
        self.base_url = "https://user-api.gluehome.com/v1"

    @property
    def _headers(self):
        """Get headers with current auth."""
        return {
            "Authorization": f"Api-Key {self._api_key}" if self._api_key else None,
            "Content-Type": "application/json",
        }

    async def authenticate(self, username: str, password: str) -> str:
        """Get API key using username and password."""
        auth_string = base64.b64encode(
            f"{username}:{password}".encode()
        ).decode()

        headers = {
            "Authorization": f"Basic {auth_string}",
            "Content-Type": "application/json",
        }

        async with self._session.post(
            f"{self.base_url}/api-keys",
            headers=headers,
            json={
                "name": "Home Assistant Integration",
                "scopes": ["events.read", "locks.read", "locks.write"]
            },
        ) as response:
            if response.status == 401:
                raise GlueAuthError("Invalid username or password")
            if response.status != 201:
                raise GlueApiError(f"Failed to get API key: {response.status}")
            
            data = await response.json()
            self._api_key = data.get("key")
            return self._api_key

    def set_api_key(self, api_key: str):
        """Set the API key directly."""
        self._api_key = api_key

    # ... rest of the API methods remain the same ... 