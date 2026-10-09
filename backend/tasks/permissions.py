from django.conf import settings


def get_role_codes(claims):
    """
    Extrae los códigos de rol de las claims devueltas
    por el servidor de identidad.

    Ajustaremos el nombre de la claim a la respuesta
    real de OLIMPO.
    """
    roles = claims.get(
        settings.TASKFLOW_ROLES_CLAIM,
        [],
    )

    if isinstance(roles, str):
        return {roles}

    if isinstance(roles, list):
        return {
            role if isinstance(role, str) else role.get("code")
            for role in roles
            if isinstance(role, str)
            or (
                isinstance(role, dict)
                and role.get("code")
            )
        }

    return set()


def is_task_admin(claims):
    return (
        settings.TASKFLOW_ADMIN_ROLE_CODE
        in get_role_codes(claims)
    )