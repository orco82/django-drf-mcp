from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from .views import McpView
from .server import get_config


# Exclude these views from schema generation to avoid AutoSchema conflicts
class _SchemaView(SpectacularAPIView):
    schema = None


class _SwaggerView(SpectacularSwaggerView):
    schema = None


_config = get_config()

urlpatterns = [
    path(_config["MCP_PATH"].strip("/") + "/", McpView.as_view(), name="django-drf-mcp"),
]

if _config["SWAGGER_ENABLED"]:
    urlpatterns += [
        path(_config["SCHEMA_PATH"].lstrip("/"), _SchemaView.as_view(), name="schema"),
        path(
            _config["SWAGGER_PATH"].lstrip("/"),
            _SwaggerView.as_view(url_name="schema"),
            name="swagger-ui",
        ),
    ]
