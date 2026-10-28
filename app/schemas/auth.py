"""Esquemas de /auth/register, /auth/login y /auth/me.

PENDIENTE (Login y permisos): completar los campos marcados con TODO según
Propuesta_modulo_Login.pdf. Los modelos de entrada ya usan extra="forbid".
"""

import re

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class RegistroSolicitud(BaseModel):
    """Entrada de POST /auth/register.

    TODO:
    - numero_idoneidad: texto requerido y no vacío.
    - correo: EmailStr (email-validator ya está en requirements.txt).
    - password: longitud mínima y complejidad que defina Login (decisión 1).
    """

    model_config = ConfigDict(extra="forbid")

    numero_idoneidad: str = Field(min_length=1, max_length=100)
    correo: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("numero_idoneidad")
    @classmethod
    def idoneidad_no_vacia(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("El número de idoneidad es obligatorio.")
        return value

    @field_validator("password")
    @classmethod
    def password_segura(cls, value: str) -> str:
        if not re.search(r"[^\w\s]", value, flags=re.UNICODE):
            raise ValueError(
                "La contraseña debe contener al menos un carácter especial."
            )
        return value


class LoginSolicitud(BaseModel):
    """Entrada de POST /auth/login: {"username": "<correo>", "password": "..."}.

    TODO:
    - username: el correo (EmailStr si siempre será el correo, decisión 8).
    - password: texto no vacío. Aquí no se validan reglas de complejidad.
    """

    model_config = ConfigDict(extra="forbid")

    username: EmailStr
    password: str = Field(min_length=1, max_length=128)


class TokenRespuesta(BaseModel):
    """Salida de register y login."""

    access_token: str
    token_type: str = "bearer"


class UsuarioRespuesta(BaseModel):
    """Salida de GET /auth/me.

    id: int
    username: EmailStr
    nombre: str | None
    email: EmailStr
    idoneidad: str | None
    role: str
    is_active: bool
    lo que devuelve obtener_usuario_por_id:
        id_usuario → id, correo → email y username, numero_idoneidad → idoneidad,
        rol → role, activo → is_active.
    """

    id: int
    username: EmailStr
    nombre: str | None
    email: EmailStr
    idoneidad: str | None
    role: str
    is_active: bool
