"""Solicitud de cambio de un campo en la base de datos."""
from typing import Literal
from pydantic import BaseModel

EstadoDecision = Literal['APROBADO', 'RECHAZADO']

class DecisionCambio(BaseModel):
    """Decisión del administrador sobre un campo."""
    estado: EstadoDecision
