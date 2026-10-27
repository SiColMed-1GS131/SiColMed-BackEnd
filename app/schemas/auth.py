"""Contratos de autenticación basados en las funciones existentes de PostgreSQL."""
from pydantic import BaseModel, ConfigDict, EmailStr, Field

class RegistroSolicitud(BaseModel):
    model_config = ConfigDict(extra="forbid")
    numero_idoneidad: str = Field(min_length=1, max_length=50)
    correo: EmailStr
    password: str = Field(min_length=8, max_length=128)

class LoginSolicitud(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)

class TokenRespuesta(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UsuarioRespuesta(BaseModel):
    id: int
    username: str
    nombre: str | None = None
    email: str
    idoneidad: str | None = None
    role: str
    is_active: bool
