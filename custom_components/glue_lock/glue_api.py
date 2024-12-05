"""API Client for Glue Lock."""
import logging
import base64
import aiohttp
import json
import async_timeout

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

    async def authenticate(self, username: str, password: str) -> str:
        """Get API key using username and password."""
        _LOGGER.debug("Attempting authentication for user: %s", username)
        
        try:
            async with async_timeout.timeout(10):
                auth = aiohttp.BasicAuth(username, password)
                async with self._session.post(
                    f"{self.base_url}/api-keys",
                    auth=auth,
                    headers={"Content-Type": "application/json"},
                    json={
                        "name": "Home Assistant Integration",
                        "scopes": ["events.read", "locks.read", "locks.write"]
                    },
                ) as response:
                    _LOGGER.debug("Auth response status: %s", response.status)
                    text = await response.text()
                    _LOGGER.debug("Auth response text: %s", text)
                    
                    if response.status == 401:
                        raise GlueAuthError("Invalid username or password")
                    if response.status not in (200, 201):
                        raise GlueApiError(f"Failed to get API key: {response.status}")
                    
                    data = json.loads(text)
                    self._api_key = data.get("apiKey")
                    if not self._api_key:
                        raise GlueApiError("No API key in response")
                    return self._api_key

        except Exception as e:
            _LOGGER.error("Authentication error: %s", str(e))
            raise

    def set_api_key(self, api_key: str):
        """Set the API key directly."""
        self._api_key = api_key

    async def get_locks(self):
        """Get all locks."""
        if not self._api_key:
            raise GlueApiError("No API key set")

        _LOGGER.debug("Getting locks")
        try:
            async with async_timeout.timeout(10):
                async with self._session.get(
                    f"{self.base_url}/locks",
                    headers={
                        "Authorization": f"Api-Key {self._api_key}",
                        "Content-Type": "application/json"
                    },
                ) as response:
                    _LOGGER.debug("Get locks response status: %s", response.status)
                    text = await response.text()
                    _LOGGER.debug("Get locks response: %s", text)
                    
                    if response.status != 200:
                        raise GlueApiError(f"Failed to get locks: {response.status}")
                    
                    return json.loads(text)

        except Exception as e:
            _LOGGER.error("Get locks error: %s", str(e))
            raise

    async def get_lock_status(self, lock_id: str):
        """Get status of specific lock."""
        if not self._api_key:
            raise GlueApiError("No API key set")

        try:
            async with async_timeout.timeout(10):
                async with self._session.get(
                    f"{self.base_url}/locks/{lock_id}",
                    headers={
                        "Authorization": f"Api-Key {self._api_key}",
                        "Content-Type": "application/json"
                    },
                ) as response:
                    if response.status != 200:
                        raise GlueApiError(f"Failed to get lock status: {response.status}")
                    return await response.json()
        except Exception as e:
            _LOGGER.error("Get status error: %s", str(e))
            raise

    async def lock(self, lock_id: str):
        """Lock the door."""
        _LOGGER.debug("Locking door %s", lock_id)
        return await self._operate_lock(lock_id, "lock")

    async def unlock(self, lock_id: str):
        """Unlock the door."""
        _LOGGER.debug("Unlocking door %s", lock_id)
        return await self._operate_lock(lock_id, "unlock")

    async def _operate_lock(self, lock_id: str, operation: str):
        """Perform lock operation."""
        if not self._api_key:
            raise GlueApiError("No API key set")

        try:
            async with async_timeout.timeout(10):
                async with self._session.post(
                    f"{self.base_url}/locks/{lock_id}/operations",
                    headers={
                        "Authorization": f"Api-Key {self._api_key}",
                        "Content-Type": "application/json"
                    },
                    json={"type": operation},
                ) as response:
                    text = await response.text()
                    _LOGGER.debug("%s operation response: %s (status: %s)", 
                                operation, text, response.status)
                    
                    if response.status == 503:
                        raise GlueApiError("Hub is busy, please try again in a minute")
                    elif response.status not in (200, 201):
                        raise GlueApiError(f"Failed to {operation}: {response.status}")
                    
                    return json.loads(text)
        except Exception as e:
            _LOGGER.error("Operation error: %s", str(e))
            raise