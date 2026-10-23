"""Solicitud de cambio de un campo en la base de datos."""
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

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


class SolicitudCambioCrear(BaseModel):
    """Solicitud de cambio enviada por el médico."""
    model_config = ConfigDict(
        extra='forbid',
        json_schema_extra={
            'examples': [{
                'cambios': [
                    {'campo': 'celular', 'valor_nuevo': '6000-2222'},
                    {'campo': 'email_personal', 'valor_nuevo': 'ana.perez@example.com'}
                ]
            }]
        }
    )
    cambios: list[CambioSolicitado] = Field(min_length=1)

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
                    'celular': {'estado': 'APROBADO'},
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
                    'celular': {
                        'valor_anterior': '6000-1111',
                        'valor_nuevo': '6000-2222',
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
