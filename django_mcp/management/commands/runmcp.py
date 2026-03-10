from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Run the MCP server (auto-discovered from DRF endpoints)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--transport",
            choices=["stdio", "sse", "streamable-http"],
            default="stdio",
            help="MCP transport type (default: stdio)",
        )
        parser.add_argument(
            "--host",
            default="0.0.0.0",
            help="Host to bind (for sse/streamable-http, default: 0.0.0.0)",
        )
        parser.add_argument(
            "--port",
            type=int,
            default=8001,
            help="Port to bind (for sse/streamable-http, default: 8001)",
        )
        parser.add_argument(
            "--base-url",
            default=None,
            help="Base URL of the Django server for proxying (default: from settings)",
        )

    def handle(self, *args, **options):
        transport = options["transport"]
        host = options["host"]
        port = options["port"]
        base_url = options["base_url"]

        from django_mcp.server import create_mcp_server

        kwargs = {}
        if base_url:
            kwargs["base_url"] = base_url

        server = create_mcp_server(**kwargs)

        self.stdout.write(
            self.style.SUCCESS(
                f"Starting MCP server '{server.name}' with transport={transport}"
            )
        )

        if transport == "stdio":
            server.run(transport="stdio")
        elif transport == "sse":
            server.run(transport="sse", host=host, port=port)
        elif transport == "streamable-http":
            server.run(transport="streamable-http", host=host, port=port)
