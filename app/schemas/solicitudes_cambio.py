"""Solicitud de cambio de un campo en la base de datos."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

EstadoDecision = Literal['APROBADO', 'RECHAZADO']


class DecisionCambio(BaseModel):
    """Decisión del administrador sobre un campo."""
    model_config = ConfigDict(extra='forbid')
    estado: EstadoDecision


class CambioSolicitado(BaseModel):
    """Cambio solicitado por el médico."""
    model_config = ConfigDict(extra='forbid')
    campo: str = Field(min_length=1)
    valor_nuevo: str


class SolicitudCambioCrear(BaseModel):
    """Solicitud de cambio enviada por el médico."""
    model_config = ConfigDict(extra='forbid')
    cambios: list[CambioSolicitado] = Field(min_length=1)