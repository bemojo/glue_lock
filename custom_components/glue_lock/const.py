"""Constants for the Glue Lock integration."""
from homeassistant.const import Platform

DOMAIN = "glue_lock"
PLATFORMS = [Platform.LOCK]

CONF_AUTH_METHOD = "auth_method"
AUTH_CREDENTIALS = "credentials"
AUTH_API_KEY = "api_key"
