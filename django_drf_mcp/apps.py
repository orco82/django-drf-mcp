import importlib

from django.apps import AppConfig
from django.conf import settings
from django.template import engines


class DjangoMcpConfig(AppConfig):
    name = "django_drf_mcp"
    verbose_name = "Django MCP"

    def ready(self):
        self._ensure_spectacular()

    def _ensure_spectacular(self):
        """Auto-inject drf-spectacular into the project if not already present."""
        installed = settings.INSTALLED_APPS

        if "drf_spectacular" not in installed:
            if isinstance(installed, list):
                installed.append("drf_spectacular")
            elif isinstance(installed, tuple):
                settings.INSTALLED_APPS = installed + ("drf_spectacular",)

            # Since we added drf_spectacular after Django initialized templates,
            # we need to register its template dirs with the template engine.
            self._register_template_dirs()

        rf = getattr(settings, "REST_FRAMEWORK", {})
        if "DEFAULT_SCHEMA_CLASS" not in rf:
            rf["DEFAULT_SCHEMA_CLASS"] = "drf_spectacular.openapi.AutoSchema"
            settings.REST_FRAMEWORK = rf

        # Also set the live DRF api_settings so views already loaded
        # pick up the correct schema class immediately.
        from rest_framework.settings import api_settings
        from drf_spectacular.openapi import AutoSchema
        api_settings.DEFAULT_SCHEMA_CLASS = AutoSchema

    def _register_template_dirs(self):
        """Add drf-spectacular template dirs to the Django template engine."""
        try:
            spectacular = importlib.import_module("drf_spectacular")
            from pathlib import Path
            spectacular_templates = Path(spectacular.__file__).parent / "templates"
            if spectacular_templates.is_dir():
                for engine in engines.all():
                    if hasattr(engine, "engine"):
                        engine.engine.dirs = list(engine.engine.dirs) + [str(spectacular_templates)]
        except (ImportError, Exception):
            pass
