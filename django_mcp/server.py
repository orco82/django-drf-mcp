import json

import httpx
from django.conf import settings
from drf_spectacular.generators import SchemaGenerator
from fastmcp import FastMCP
from fastmcp.server.providers.openapi import OpenAPIProvider


def get_config() -> dict:
    """Return django-mcp configuration with defaults."""
    defaults = {
        # Server
        "NAME": "django-mcp",
        "BASE_URL": "http://localhost:8000",
        "MCP_PATH": "/mcp/",
        # MCP Docs (fastmcp-docs)
        "MCP_DOCS_ENABLED": True,
        "MCP_DOCS_TITLE": None,
        "MCP_DOCS_DESCRIPTION": None,
        "MCP_DOCS_VERSION": None,
        "MCP_DOCS_EMOJI": None,
        "MCP_DOCS_LINKS": [],
        "MCP_DOCS_ENABLE_CORS": True,
        "MCP_DOCS_VERBOSE": True,
        # Authentication
        "HEADERS": {},
        # DRF Swagger / Schema
        "SWAGGER_ENABLED": False,
        "SCHEMA_PATH": "/api/schema/",
        "SWAGGER_PATH": "/api/docs/",
    }
    user_config = getattr(settings, "DJANGO_MCP", {})
    return {**defaults, **user_config}


def generate_openapi_schema() -> dict:
    """Generate OpenAPI schema from DRF views using drf-spectacular."""
    from rest_framework.settings import api_settings
    from drf_spectacular.openapi import AutoSchema

    # Ensure DRF uses drf-spectacular's AutoSchema for schema generation
    api_settings.DEFAULT_SCHEMA_CLASS = AutoSchema

    generator = SchemaGenerator()
    schema = generator.get_schema(request=None, public=True)
    # drf-spectacular returns an OrderedDict; FastMCP needs a plain dict
    return json.loads(json.dumps(schema))


def create_mcp_server(base_url: str | None = None, name: str | None = None) -> FastMCP:
    """Create an MCP server from the DRF OpenAPI schema.

    Args:
        base_url: Base URL of the running Django server (for proxying tool calls).
        name: MCP server name.
    """
    config = get_config()
    base_url = base_url or config["BASE_URL"]
    name = name or config["NAME"]

    schema = generate_openapi_schema()

    # Add server URL to schema so OpenAPIProvider knows where to send requests
    schema.setdefault("servers", [])
    if not schema["servers"]:
        schema["servers"].append({"url": base_url})

    client = httpx.AsyncClient(
        base_url=base_url,
        headers=config.get("HEADERS", {}),
        timeout=30.0,
    )

    provider = OpenAPIProvider(openapi_spec=schema, client=client)
    server = FastMCP(name, providers=[provider])

    return server


async def setup_docs(
    server: FastMCP,
    schema: dict,
    prefix: str = "",
):
    """Setup FastMCPDocs on the server using DJANGO_MCP settings.

    Args:
        server: The FastMCP server instance.
        schema: OpenAPI schema dict.
        prefix: URL prefix for docs routes (e.g. "/mcp").
    """
    from fastmcp_docs import FastMCPDocs, FastMCPDocsConfig

    cfg = get_config()
    info = schema.get("info", {})

    docs_config = FastMCPDocsConfig(
        title=cfg["MCP_DOCS_TITLE"] or cfg["NAME"],
        version=cfg["MCP_DOCS_VERSION"] or info.get("version", "1.0.0"),
        description=cfg["MCP_DOCS_DESCRIPTION"] or info.get("description", f"MCP tools documentation for {cfg['NAME']}"),
        base_url=cfg["BASE_URL"],
        docs_links=cfg["MCP_DOCS_LINKS"],
        page_title_emoji=cfg["MCP_DOCS_EMOJI"],
        enable_cors=cfg["MCP_DOCS_ENABLE_CORS"],
        verbose=cfg["MCP_DOCS_VERBOSE"],
        docs_ui_route=f"{prefix}/docs",
        openapi_route=f"{prefix}/openapi.json",
        api_tools_route=f"{prefix}/api/tools",
        api_tool_detail_route=f"{prefix}/api/tools/{{tool_name}}",
    )
    docs = FastMCPDocs(mcp=server, config=docs_config)
    await docs.setup()
    return docs
