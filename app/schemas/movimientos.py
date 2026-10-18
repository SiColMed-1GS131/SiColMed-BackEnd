from pydantic import BaseModel, Field, model_validator
from typing import Optional
from datetime import date
from enum import Enum

class TipoMovimiento(str, Enum):
    DEBITO = "DEBITO"
    CREDITO = "CREDITO"

class MovimientoCreate(BaseModel):
    fecha: Optional[date] = Field(default=None, description="Fecha del movimiento. Si es null, BD usa fecha actual")
    descripcion: str = Field(..., description="Descripción del movimiento")
    id_cuenta: int = Field(..., description="ID de la cuenta afectada")
    tipo: TipoMovimiento = Field(..., description="DEBITO o CREDITO")
    monto: float = Field(..., gt=0, description="Debe ser estrictamente mayor que cero")

class FilaMovimientoDiario(BaseModel):
    id_movimiento: int
    fecha: date
    descripcion: str
    id_cuenta: int
    nombre_cuenta: str
    tipo: TipoMovimiento
    monto: float

class FilaMovimientoCuenta(BaseModel):
    id_movimiento: int
    fecha: date
    descripcion: str
    monto: float
    tipo: TipoMovimiento

class RangoFechasParams(BaseModel):
    fecha_inicio: date
    fecha_fin: date

    @model_validator(mode='after')
    def validar_rango(self):
        if self.fecha_inicio > self.fecha_fin:
            raise ValueError('La fecha de inicio no puede ser posterior a la fecha de fin')
        return self