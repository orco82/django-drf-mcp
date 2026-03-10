import asyncio
import json

from rest_framework.views import APIView
from rest_framework.response import Response


class McpView(APIView):
    """Serve MCP Streamable HTTP protocol as a DRF API view.

    Stateless mode: POST with JSON-RPC -> respond with JSON.
    Inherits authentication and permissions from REST_FRAMEWORK settings.
    """

    def get(self, request):
        """Health check / info endpoint."""
        from .server import get_config

        config = get_config()
        return Response({
            "name": config["NAME"],
            "protocol": "mcp",
            "transport": "streamable-http",
            "status": "ok",
        })

    def post(self, request):
        """Handle MCP JSON-RPC requests."""
        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return Response({"error": "Invalid JSON"}, status=400)

        result = asyncio.run(self._handle_rpc(body))
        return Response(result)

    async def _handle_rpc(self, body: dict) -> dict:
        """Process a single JSON-RPC request through the MCP server."""
        from .server import create_mcp_server

        server = create_mcp_server()
        method = body.get("method", "")
        params = body.get("params", {})
        request_id = body.get("id")

        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {"listChanged": False}},
                    "serverInfo": {"name": server.name, "version": "1.0.0"},
                },
            }

        if method == "tools/list":
            tools = await server.list_tools()
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "tools": [
                        {
                            "name": t.name,
                            "description": t.description or "",
                            "inputSchema": t.parameters if hasattr(t, "parameters") else {},
                        }
                        for t in tools
                    ]
                },
            }

        if method == "tools/call":
            tool_name = params.get("name", "")
            arguments = params.get("arguments", {})
            result = await server.call_tool(tool_name, arguments)
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [
                        {"type": "text", "text": str(c.text) if hasattr(c, "text") else str(c)}
                        for c in result
                    ]
                },
            }

        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": -32601, "message": f"Method not found: {method}"},
        }
