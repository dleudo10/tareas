
import logging

import requests

from django.conf import settings
from django.core.cache import cache
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed


logger = logging.getLogger(__name__)


class OIDCPrincipal:
    """Representa al usuario autenticado por OLIMPO."""

    def __init__(self, claims):
        self.claims = claims
        self.id = claims.get("sub")
        self.username = (
            claims.get("preferred_username")
            or claims.get("username")
            or claims.get("sub")
        )
        self.full_name = claims.get("name") or self.username
        self.email = claims.get("email")

        self.is_authenticated = True
        self.is_anonymous = False

    def __str__(self):
        return str(self.username)


class OIDCIntrospectionAuthentication(BaseAuthentication):
    """
    Valida el token del usuario mediante OLIMPO.

    Utiliza un token de servicio con scope 'introspection'
    para consultar el endpoint de introspección.
    """

    SERVICE_TOKEN_CACHE_KEY = "olimpo_introspection_service_token"

    def _get_service_token(self):
        """
        Obtiene un token client_credentials para autorizar
        las peticiones al endpoint de introspección.
        """

        cached_token = cache.get(self.SERVICE_TOKEN_CACHE_KEY)
        if cached_token:
            return cached_token

        try:
            response = requests.post(
                settings.OIDC_TOKEN_URL,
                data={
                    "grant_type": "client_credentials",
                    "scope": "introspection",
                },
                auth=(
                    settings.OIDC_RESOURCE_CLIENT_ID,
                    settings.OIDC_RESOURCE_CLIENT_SECRET,
                ),
                timeout=5,
            )
            response.raise_for_status()
            data = response.json()

        except requests.RequestException:
            logger.exception("No fue posible obtener el token de servicio de OLIMPO.")
            raise AuthenticationFailed(
                "No fue posible autorizar la validación con OLIMPO."
            )

        except ValueError:
            logger.exception("OLIMPO devolvió una respuesta inválida al solicitar el token.")
            raise AuthenticationFailed(
                "OLIMPO devolvió una respuesta inválida."
            )

        service_token = data.get("access_token")
        if not service_token:
            logger.error("OLIMPO no devolvió access_token para el servicio.")
            raise AuthenticationFailed(
                "OLIMPO no autorizó el servicio de validación."
            )

        expires_in = int(data.get("expires_in", 60))
        cache.set(
            self.SERVICE_TOKEN_CACHE_KEY,
            service_token,
            timeout=max(expires_in - 30, 1),
        )

        return service_token

    def authenticate(self, request):
        header = request.headers.get("Authorization", "")

        if not header:
            return None

        parts = header.split()

        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise AuthenticationFailed(
                "El encabezado Authorization debe usar Bearer."
            )

        user_token = parts[1]

        # 1. Obtener el token de servicio autorizado para introspección.
        service_token = self._get_service_token()

        # 2. Validar el token presentado por el usuario.
        try:
            response = requests.post(
                settings.OIDC_INTROSPECTION_URL,
                data={"token": user_token},
                headers={
                    "Authorization": f"Bearer {service_token}",
                },
                timeout=5,
            )

            logger.info(
                "OLIMPO introspection: status=%s",
                response.status_code,
            )

            response.raise_for_status()
            introspection = response.json()

        except requests.Timeout:
            logger.warning("Timeout consultando la introspección de OLIMPO.")
            raise AuthenticationFailed(
                "OLIMPO no respondió a tiempo al validar la sesión."
            )

        except requests.HTTPError:
            logger.warning(
                "OLIMPO rechazó la introspección: status=%s",
                response.status_code,
            )
            raise AuthenticationFailed(
                "OLIMPO rechazó la validación de la sesión."
            )

        except requests.RequestException:
            logger.exception("Error de conexión con la introspección de OLIMPO.")
            raise AuthenticationFailed(
                "No fue posible conectar con OLIMPO."
            )

        except ValueError:
            logger.exception("La introspección de OLIMPO no devolvió JSON válido.")
            raise AuthenticationFailed(
                "OLIMPO devolvió una respuesta inválida."
            )

        if introspection.get("active") is not True:
            raise AuthenticationFailed(
                "El token no está activo o ha expirado."
            )

        # 3. Obtener los datos OIDC del usuario con SU token,
        # no con el token de servicio.
        try:
            response = requests.get(
                settings.OIDC_USERINFO_URL,
                headers={
                    "Authorization": f"Bearer {user_token}",
                },
                timeout=5,
            )
            response.raise_for_status()
            claims = response.json()

        except requests.Timeout:
            logger.warning("Timeout consultando el userinfo de OLIMPO.")
            raise AuthenticationFailed(
                "OLIMPO no respondió al consultar los datos del usuario."
            )

        except requests.HTTPError:
            logger.warning(
                "OLIMPO rechazó userinfo: status=%s",
                response.status_code,
            )
            raise AuthenticationFailed(
                "No fue posible obtener la identidad del usuario."
            )

        except requests.RequestException:
            logger.exception("Error de conexión con userinfo de OLIMPO.")
            raise AuthenticationFailed(
                "No fue posible conectar con OLIMPO."
            )

        except ValueError:
            logger.exception("El userinfo de OLIMPO no devolvió JSON válido.")
            raise AuthenticationFailed(
                "OLIMPO devolvió datos de usuario inválidos."
            )

        subject = claims.get("sub")
        if not subject:
            raise AuthenticationFailed(
                "OLIMPO no devolvió el identificador sub del usuario."
            )

        # Conservar información útil de la introspección.
        claims["active"] = introspection.get("active")
        claims["scope"] = introspection.get("scope", "")
        claims["exp"] = introspection.get("exp")

        principal = OIDCPrincipal(claims)
        return principal, claims

    def authenticate_header(self, request):
        return "Bearer"
