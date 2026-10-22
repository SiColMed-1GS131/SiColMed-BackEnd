"""Schemas para filtros y actualización administrativa de médicos."""

from datetime import date
from typing import Final

from pydantic import BaseModel, ConfigDict, EmailStr, Field


CamposActualizablesMedico: Final[frozenset[str]] = frozenset(
    {
        "numero_idoneidad",
        "numero_registro_medico",
        "cedula",
        "primer_nombre",
        "segundo_nombre",
        "apellido_paterno",
        "apellido_materno",
        "foto",
        "fecha_nacimiento",
        "telefono_residencial",
        "celular",
        "email_personal",
    }
)

# Endpoint 1: GET /medicos
class FiltroMedicos(BaseModel):
    apellido: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )
    id_especialidad: int | None = Field(
        default=None,
        ge=1,
    )
    id_asociacion: int | None = Field(
        default=None,
        ge=1,
    )
    id_subespecialidad: int | None = Field(
        default=None,
        ge=1,
    )
    certificacion_vigente: bool | None = None
    id_provincia: int | None = Field(
        default=None,
        ge=1,
    )
    lugar_trabajo: str | None = Field(
        default=None,
        min_length=1,
        max_length=150,
    )
    pagina: int = Field(
        default=1,
        ge=1,
    )
    tamano_pagina: int = Field(
        default=20,
        ge=1,
        le=100,
    )


# Resumen de medico devuelto por la función de filtrado
class MedicoResumen(BaseModel):
    id_medico: int
    nombre_completo: str
    numero_idoneidad: str
    especialidades: str | None = None
    asociaciones: str | None = None
    certificacion_vigente: bool | None = None
    provincia: str | None = None
    lugar_trabajo: str | None = None

class ListaMedicosRespuesta(BaseModel):
    medicos: list[MedicoResumen]
    total: int
    pagina: int
    tamano_pagina: int
    total_paginas: int


# Endpoint 2: patch /medicos/{id_medico}
class ActualizarMedicoSolicitud(BaseModel):
    """Campos que la API puede recibir para actualizar un médico."""

    model_config = ConfigDict(extra="forbid")

    numero_idoneidad: str | None = Field(default=None, min_length=1)
    numero_registro_medico: str | None = Field(default=None, min_length=1)
    cedula: str | None = Field(default=None, min_length=1)
    primer_nombre: str | None = Field(default=None, min_length=1)
    segundo_nombre: str | None = Field(default=None, min_length=1)
    apellido_paterno: str | None = Field(default=None, min_length=1)
    apellido_materno: str | None = Field(default=None, min_length=1)
    foto: str | None = Field(default=None, min_length=1)
    fecha_nacimiento: date | None = None
    telefono_residencial: str | None = Field(default=None, min_length=1)
    celular: str | None = Field(default=None, min_length=1)
    email_personal: EmailStr | None = None

# Resultado de la actualización devuelto por la función de BD
class ActualizarMedicoRespuesta(BaseModel):
    """Resultado de la actualización devuelto por la función de BD."""

    actualizado: bool
