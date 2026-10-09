import requests

from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed


class OIDCPrincipal:
    """
    Representa al usuario autenticado por OLIMPO.

    No es un usuario local de Django.
    """

    def __init__(self, claims):
        self.claims = claims

        self.id = claims.get("sub")
        self.username = (
            claims.get("preferred_username")
            or claims.get("username")
            or claims.get("sub")
        )
        self.full_name = (
            claims.get("name")
            or self.username
        )

        self.is_authenticated = True
        self.is_anonymous = False

    def __str__(self):
        return str(self.username)


class OIDCIntrospectionAuthentication(BaseAuthentication):
    """
    Valida el Bearer token consultando la introspección
    del proveedor OAuth/OIDC configurado.
    """

    def authenticate(self, request):
        header = request.headers.get("Authorization", "")

        if not header:
            return None

        parts = header.split()

        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise AuthenticationFailed(
                "El encabezado Authorization debe usar Bearer."
            )

        token = parts[1]

        try:
            response = requests.post(
                settings.OIDC_INTROSPECTION_URL,
                data={"token": token},
                auth=(
                    settings.OIDC_RESOURCE_CLIENT_ID,
                    settings.OIDC_RESOURCE_CLIENT_SECRET,
                ),
                timeout=5,
            )
            response.raise_for_status()
            claims = response.json()

        except (requests.RequestException, ValueError):
            raise AuthenticationFailed(
                "No fue posible validar la sesión con OLIMPO."
            )

        if not claims.get("active"):
            raise AuthenticationFailed(
                "El token no está activo o ha expirado."
            )

        subject = claims.get("sub")

        if not subject:
            raise AuthenticationFailed(
                "OLIMPO no devolvió el identificador sub del usuario."
            )

        expected_issuer = settings.OIDC_EXPECTED_ISSUER
        issuer = claims.get("iss")

        if issuer and issuer != expected_issuer:
            raise AuthenticationFailed(
                "El token pertenece a un emisor no autorizado."
            )

        principal = OIDCPrincipal(claims)

        return principal, claims

    def authenticate_header(self, request):
        return "Bearer"