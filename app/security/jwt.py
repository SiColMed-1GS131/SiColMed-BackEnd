"""Creación y validación de los JWT de acceso (Login y permisos).

Claims del token: sub (id_usuario como texto, según la convención de JWT),
role, iat y exp. El token nunca lleva la contraseña ni su hash.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import jwt

from app.config import settings

# Con HS256, una clave más corta que esto se puede adivinar por fuerza bruta.
LONGITUD_MINIMA_CLAVE = 32
CLAIMS_REQUERIDOS = ["sub", "role", "exp"]


class ConfiguracionJWTError(RuntimeError):
    """JWT_SECRET_KEY falta o es demasiado corta."""


class TokenInvalido(Exception):
    """Firma incorrecta, formato inválido o claims faltantes."""


class TokenExpirado(TokenInvalido):
    """El token tenía firma válida, pero ya pasó su exp."""


@dataclass(frozen=True)
class UsuarioAutenticado:
    """Lo que se sabe del usuario a partir de un token válido.

    Los routers usan id_usuario como id_administrador al llamar a la BD.
    """

    id_usuario: int
    rol: str
    id_medico: int | None = None


def _clave_secreta() -> str:
    clave = settings.jwt_secret_key
    if len(clave) < LONGITUD_MINIMA_CLAVE:
        raise ConfiguracionJWTError(
            f"JWT_SECRET_KEY debe tener al menos {LONGITUD_MINIMA_CLAVE} caracteres. "
            "Revisa el .env (hay un ejemplo en SiColMed-Infrastructure/.env.example)."
        )
    return clave


def crear_token_acceso(
    id_usuario: int,
    rol: str,
    id_medico: int | None = None,
) -> str:
    """Firma un token de acceso que vence en JWT_ACCESS_TOKEN_EXPIRE_MINUTES."""
    ahora = datetime.now(timezone.utc)
    claims = {
        "sub": str(id_usuario),
        "role": rol,
        "iat": ahora,
        "exp": ahora + timedelta(minutes=settings.jwt_access_token_expire_minutes),
    }
    if id_medico is not None:
        if id_medico < 1:
            raise ValueError("id_medico debe ser mayor que cero.")
        claims["id_medico"] = id_medico
    return jwt.encode(claims, _clave_secreta(), algorithm=settings.jwt_algorithm)


def decodificar_token(token: str) -> UsuarioAutenticado:
    """Valida firma, algoritmo y vencimiento, y devuelve el usuario del token."""
    try:
        claims = jwt.decode(
            token,
            _clave_secreta(),
            algorithms=[settings.jwt_algorithm],
            options={"require": CLAIMS_REQUERIDOS},
        )
    except jwt.ExpiredSignatureError as error:
        raise TokenExpirado("El token expiró.") from error
    except jwt.InvalidTokenError as error:
        raise TokenInvalido("Token inválido.") from error

    sub, rol = claims["sub"], claims["role"]
    if not (isinstance(sub, str) and sub.isascii() and sub.isdigit() and int(sub) > 0):
        raise TokenInvalido("Token inválido.")
    if not isinstance(rol, str) or not rol:
        raise TokenInvalido("Token inválido.")
    id_medico = claims.get("id_medico")
    if id_medico is not None and (
        not isinstance(id_medico, int) or id_medico < 1
    ):
        raise TokenInvalido("Token inválido.")
    return UsuarioAutenticado(
        id_usuario=int(sub),
        rol=rol,
        id_medico=id_medico,
    )
