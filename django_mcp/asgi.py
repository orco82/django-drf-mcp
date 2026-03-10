"""
ASGI helper for django-mcp.

Provides get_asgi_application() that mounts both the Django app and the
FastMCP docs Starlette app under a single ASGI entry point.

Usage in your project's asgi.py:

    from django_mcp.asgi import get_asgi_application
    application = get_asgi_application()

Routes (when MCP_DOCS_ENABLED=True):
- /mcp/docs, /mcp/api/*, /mcp/openapi.json -> FastMCP docs (Starlette)
- /mcp/                                     -> Django McpView (MCP protocol)
- /*                                        -> Django (DRF, admin, etc.)

When MCP_DOCS_ENABLED=False, all routes go to Django.
"""

from django.contrib.staticfiles.handlers import ASGIStaticFilesHandler
from django.core.asgi import get_asgi_application as _django_get_asgi_application

from .server import get_config

_config = get_config()
_MCP_PREFIX = _config["MCP_PATH"].rstrip("/")  # e.g. "/mcp"
_MCP_DOCS_ENABLED = _config["MCP_DOCS_ENABLED"]

# Docs sub-paths handled by Starlette (everything else under /mcp goes to Django)
_MCP_DOCS_PATHS = (
    f"{_MCP_PREFIX}/docs",
    f"{_MCP_PREFIX}/api/",
    f"{_MCP_PREFIX}/openapi.json",
    f"{_MCP_PREFIX}/favicon",
)


_mcp_app = None


async def _get_mcp_app():
    global _mcp_app
    if _mcp_app is None:
        from .server import create_mcp_server, setup_docs, generate_openapi_schema

        server = create_mcp_server()
        schema = generate_openapi_schema()
        await setup_docs(
            server,
            schema=schema,
            prefix=_MCP_PREFIX,
        )
        _mcp_app = server.http_app()
    return _mcp_app


def get_asgi_application():
    """Return an ASGI application that serves both Django and MCP docs.

    Wraps Django with ASGIStaticFilesHandler for static file serving.
    If MCP_DOCS_ENABLED is True, routes /mcp/docs, /mcp/api/*, /mcp/openapi.json
    to the FastMCP Starlette app for interactive documentation.
    If MCP_DOCS_ENABLED is False, all routes go to Django.
    """
    django_app = ASGIStaticFilesHandler(_django_get_asgi_application())

    if not _MCP_DOCS_ENABLED:
        return django_app

    async def application(scope, receive, send):
        path = scope.get("path", "")

        if any(path.startswith(p) for p in _MCP_DOCS_PATHS):
            mcp_app = await _get_mcp_app()
            await mcp_app(scope, receive, send)
        else:
            await django_app(scope, receive, send)

    return application
