from datetime import date
from typing import Any
from pydantic import BaseModel, ConfigDict, Field, RootModel

class DireccionRegistro(BaseModel):
    apartado_postal: str | None = None
    calle: str | None = None
    edificio: str | None = None
    numero_direccion: str | None = None
    id_corregimiento: int = Field(gt=0)

class MedicoRegistro(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    numero_idoneidad: str = Field(min_length=1)
    numero_registro_medico: str = Field(min_length=1)
    cedula: str = Field(min_length=1)
    primer_nombre: str = Field(min_length=1)
    segundo_nombre: str | None = None
    apellido_paterno: str = Field(min_length=1)
    apellido_materno: str | None = None
    foto: str | None = None
    fecha_nacimiento: date | None = None
    telefono_residencial: str | None = None
    celular: str | None = None
    email_personal: str | None = None
    direccion: DireccionRegistro

class MedicoCreado(BaseModel):
    id_medico: int = Field(gt=0)

class PerfilMedico(RootModel[dict[str, Any]]):
    """Estructura de secciones pendiente de la firma JSON del equipo BD."""
