import secrets

from django.conf import settings

HEADER_NAME = "X-MCP-Internal-Token"

# 256-bit random token, generated once per process at import time.
_auto_token: str = secrets.token_hex(32)


def get_token() -> str:
    """Return the MCP internal token.

    Uses DJANGO_MCP["INTERNAL_TOKEN"] if configured, otherwise
    falls back to the auto-generated per-process token.
    """
    config = getattr(settings, "DJANGO_MCP", {})
    user_token = config.get("INTERNAL_TOKEN")
    if user_token:
        return user_token
    return _auto_token
