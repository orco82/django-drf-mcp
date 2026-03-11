import hmac

from rest_framework.permissions import BasePermission

from .tokens import HEADER_NAME, get_token


class IsMCPInternalRequest(BasePermission):
    """Allow access if the request carries a valid MCP internal token.

    The token is auto-generated per process and injected by the MCP
    httpx proxy client. External clients cannot guess it.

    Combine with other permissions using | (OR):

        from rest_framework.permissions import IsAuthenticated
        from django_drf_mcp.permissions import IsMCPInternalRequest

        class MyViewSet(viewsets.ModelViewSet):
            permission_classes = [IsAuthenticated | IsMCPInternalRequest]
    """

    def has_permission(self, request, view):
        meta_key = "HTTP_" + HEADER_NAME.upper().replace("-", "_")
        token = request.META.get(meta_key)
        if token is None:
            return False
        return hmac.compare_digest(token, get_token())
