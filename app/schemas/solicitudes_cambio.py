"""Solicitud de cambio de un campo en la base de datos."""
import re
from datetime import datetime
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    PositiveInt,
    field_validator,
    model_validator,
)

# Espejo de las reglas de BD; BD es la autoridad. Mantener sincronizado.
TABLAS_CAMBIO_PERMITIDAS = frozenset({
    "medico",
    "direccion",
    "lugar_trabajo",
    "estudio_medico",
    "certificacion",
})
CAMPOS_PERSONALES_MEDICO = frozenset({
    "primer_nombre",
    "segundo_nombre",
    "apellido_paterno",
    "apellido_materno",
    "foto",
    "fecha_nacimiento",
    "telefono_residencial",
    "celular",
    "email_personal",
})

EstadoDecision = Literal['APROBADO', 'RECHAZADO']
EstadoSolicitud = Literal['PENDIENTE', 'PROCESADO']

class DecisionCambio(BaseModel):
    """Decisión del administrador sobre un campo."""
    model_config = ConfigDict(extra='forbid')
    estado: EstadoDecision


class CambioSolicitado(BaseModel):
    """Cambio solicitado por el médico."""
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    campo: str = Field(min_length=1)
    valor_nuevo: str

    @field_validator("campo")
    @classmethod
    def validar_campo(cls, campo: str) -> str:
        partes = campo.split(":")
        if len(partes) != 3:
            raise ValueError("El campo debe tener formato tabla:id_registro:campo.")

        tabla, id_registro, nombre_campo = partes
        if tabla not in TABLAS_CAMBIO_PERMITIDAS:
            raise ValueError("La tabla indicada no está permitida.")
        if not re.fullmatch(r"[0-9]+", id_registro) or int(id_registro) < 1:
            raise ValueError("El id_registro debe ser un entero positivo.")
        if not nombre_campo.strip():
            raise ValueError("El nombre del campo no puede estar vacío.")
        if tabla == "medico" and nombre_campo in CAMPOS_PERSONALES_MEDICO:
            raise ValueError("El campo personal debe actualizarse directamente.")
        return campo


class CambioRelacionSolicitado(BaseModel):
    """Operaciones para agregar o quitar una relación profesional."""
    model_config = ConfigDict(extra='forbid')
    campo: Literal['especialidades', 'subespecialidades', 'asociaciones']
    agregar: list[PositiveInt]
    quitar: list[PositiveInt]

    @model_validator(mode='after')
    def validar_operaciones(self):
        if not self.agregar and not self.quitar:
            raise ValueError('Debe indicar al menos un identificador para agregar o quitar.')
        if set(self.agregar) & set(self.quitar):
            raise ValueError('No se puede agregar y quitar el mismo identificador.')
        return self


class SolicitudCambioCrear(BaseModel):
    """Solicitud de cambio enviada por el médico."""
    model_config = ConfigDict(
        extra='forbid',
        json_schema_extra={
            'examples': [{
                'cambios': [
                    {'campo': 'medico:17:cedula', 'valor_nuevo': '8-123-456'}
                ]
            }]
        }
    )
    cambios: list[CambioSolicitado | CambioRelacionSolicitado] = Field(min_length=1)

    @model_validator(mode='after')
    def sin_campos_repetidos(self):
        campos = [c.campo for c in self.cambios]
        if len(campos) != len(set(campos)):
            raise ValueError('No se puede repetir un campo en la misma solicitud.')
        return self


class SolicitudCambioProcesar(BaseModel):
    """Decisiones del administrador sobre la solicitud de cambio."""
    model_config = ConfigDict(
        extra='forbid',
        json_schema_extra={
            'examples': [{
                'decisiones': {
                    'medico:17:cedula': {'estado': 'APROBADO'},
                },
                'comentario': 'Cambio revisado.',
            }]
        },
    )
    decisiones: dict[str, DecisionCambio] = Field(min_length=1)
    comentario: str | None = None


class SolicitudCambioItem(BaseModel):
    """Fila de la bandeja del administrador."""
    model_config = ConfigDict(
        json_schema_extra={
            'examples': [{
                'id_solicitud_cambio': 12,
                'id_medico': 5,
                'nombre_completo': 'Ana Pérez',
                'estado': 'PENDIENTE',
                'fecha_solicitud': '2026-10-18T09:30:00',
                'cambios': {
                    'medico:17:cedula': {
                        'valor_anterior': '8-123-456',
                        'valor_nuevo': '8-123-789',
                        'estado': 'PENDIENTE',
                    }
                },
            }]
        }
    )
    id_solicitud_cambio: int
    id_medico: int
    nombre_completo: str
    estado: str
    fecha_solicitud: datetime
    cambios: dict

class SolicitudCambioCreada(BaseModel):
    """Respuesta al crear una solicitud de cambio."""
    model_config = ConfigDict(
        json_schema_extra={
            'examples': [{
                'id_solicitud_cambio': 12,
            }]
        }
    )
    id_solicitud_cambio: int
