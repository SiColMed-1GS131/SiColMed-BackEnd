"""Esquemas de /auth/register, /auth/login y /auth/me.

PENDIENTE (Login y permisos): completar los campos marcados con TODO según
Propuesta_modulo_Login.pdf. Los modelos de entrada ya usan extra="forbid".
"""

from pydantic import BaseModel, ConfigDict


class RegistroSolicitud(BaseModel):
    """Entrada de POST /auth/register.

    TODO:
    - numero_idoneidad: texto requerido y no vacío.
    - correo: EmailStr (email-validator ya está en requirements.txt).
    - password: longitud mínima y complejidad que defina Login (decisión 1).
    """

    model_config = ConfigDict(extra="forbid")


class LoginSolicitud(BaseModel):
    """Entrada de POST /auth/login: {"username": "<correo>", "password": "..."}.

    TODO:
    - username: el correo (EmailStr si siempre será el correo, decisión 8).
    - password: texto no vacío. Aquí no se validan reglas de complejidad.
    """

    model_config = ConfigDict(extra="forbid")


class TokenRespuesta(BaseModel):
    """Salida de register y login."""

    access_token: str
    token_type: str = "bearer"


class UsuarioRespuesta(BaseModel):
    """Salida de GET /auth/me.

    TODO: id, username, nombre, email, idoneidad, role e is_active, mapeando
    lo que devuelve obtener_usuario_por_id:
        id_usuario → id, correo → email y username, numero_idoneidad → idoneidad,
        rol → role, activo → is_active.
    """
