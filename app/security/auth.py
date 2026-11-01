"""Dependencias de autenticación y autorización para los routers.

get_usuario_actual lee el header `Authorization: Bearer <token>`, valida el
JWT y devuelve un UsuarioAutenticado (id_usuario y rol). No consulta la BD:
GET /auth/me es quien confirma en BD que el usuario existe y sigue activo.

Uso en un router:

    usuario: UsuarioAutenticado = Depends(requiere_rol(roles.ADMIN_CMP))
"""

from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, HTTPException, status  # pyright: ignore[reportMissingImports]
from fastapi.security import (  # pyright: ignore[reportMissingImports]
    HTTPAuthorizationCredentials,
    HTTPBearer,
)

from app.security.jwt import (
    TokenExpirado,
    TokenInvalido,
    UsuarioAutenticado,
    decodificar_token,
)

__all__ = ["UsuarioAutenticado", "get_usuario_actual", "requiere_rol"]

# auto_error=False para que los 401 lleven mensajes propios. También agrega el
# botón "Authorize" de Swagger, donde se pega el access_token.
_esquema_bearer = HTTPBearer(
    auto_error=False,
    description="access_token devuelto por POST /auth/login",
)


def _no_autenticado(detalle: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detalle,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_usuario_actual(
    credenciales: Annotated[
        HTTPAuthorizationCredentials | None, Depends(_esquema_bearer)
    ],
) -> UsuarioAutenticado:
    """401 si no hay token Bearer, si es inválido o si expiró."""
    if credenciales is None:
        raise _no_autenticado("No autenticado.")
    try:
        return decodificar_token(credenciales.credentials)
    except TokenExpirado:
        raise _no_autenticado("El token expiró.") from None
    except TokenInvalido:
        raise _no_autenticado("Token inválido.") from None


def requiere_rol(*roles: str) -> Callable[..., UsuarioAutenticado]:
    """Deja pasar solo a los roles indicados; a los demás responde 403.

    Acepta varios roles, por ejemplo requiere_rol(roles.TESORERO, roles.ADMIN_ASOCIACION).
    """
    if not roles:
        raise ValueError("requiere_rol necesita al menos un rol.")
    permitidos = frozenset(roles)

    def dependencia(
        usuario: Annotated[UsuarioAutenticado, Depends(get_usuario_actual)],
    ) -> UsuarioAutenticado:
        if usuario.rol not in permitidos:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para esta acción.",
            )
        return usuario

    return dependencia
