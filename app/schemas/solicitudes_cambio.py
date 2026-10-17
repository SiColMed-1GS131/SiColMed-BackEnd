"""Solicitud de cambio de un campo en la base de datos."""
from typing import Literal
from pydantic import BaseModel

class DecisionCambio(BaseModel):
    """Decisión del administrador sobre un campo."""
    estado: Literal['aceptado', 'negado']
