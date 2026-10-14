import requests

from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied


class OIDCPrincipal:
    """Usuario autenticado por OLIMPO (no es un usuario local de Django)."""

    def __init__(self, context):
        self.context = context
        self.id = context["sub"]
        self.username = context.get("external_id") or context["sub"]
        self.full_name = context.get("full_name") or self.username
        self.is_authenticated = True
        self.is_anonymous = False

    def __str__(self):
        return str(self.username)


class OIDCIntrospectionAuthentication(BaseAuthentication):
    """
    Valida el Bearer del usuario llamando a /api/v1/apps/me/ de OLIMPO,
    que devuelve identidad, roles y permisos para esta aplicación.
    """

    def authenticate(self, request):
        header = request.headers.get("Authorization", "")
        if not header:
            return None

        parts = header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise AuthenticationFailed("El encabezado Authorization debe usar Bearer.")

        try:
            response = requests.get(
                settings.OLIMPO_APP_CONTEXT_URL,
                headers={"Authorization": f"Bearer {parts[1]}"},
                timeout=5,
            )
        except requests.RequestException:
            raise AuthenticationFailed("No fue posible conectar con OLIMPO.")

        if response.status_code == 401:
            raise AuthenticationFailed("El token no es válido o ha expirado.")
        if response.status_code == 403:
            raise PermissionDenied("No tienes acceso a TaskFlow.")
        if not response.ok:
            raise AuthenticationFailed("OLIMPO no pudo validar la sesión.")

        try:
            context = response.json()
        except ValueError:
            raise AuthenticationFailed("OLIMPO devolvió una respuesta inválida.")

        if context.get("application") != settings.TASKFLOW_APPLICATION_CODE:
            raise PermissionDenied("El token no pertenece a TaskFlow.")

        return OIDCPrincipal(context), context

    def authenticate_header(self, request):
        return "Bearer"