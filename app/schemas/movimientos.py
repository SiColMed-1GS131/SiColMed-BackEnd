from pydantic import BaseModel, Field, model_validator
from typing import Optional, List
from datetime import date
from enum import Enum

class TipoMovimiento(str, Enum):
    DEBITO = "DEBITO"
    CREDITO = "CREDITO"

class DetalleMovimiento(BaseModel):
    id_cuenta: int = Field(..., description="ID de la cuenta afectada")
    monto: float = Field(..., gt=0, description="Debe ser estrictamente mayor que cero")
    tipo: TipoMovimiento = Field(..., description="DEBITO o CREDITO")

class MovimientoCreate(BaseModel):
    fecha: Optional[date] = Field(default=None, description="Fecha del movimiento. Si es null, BD usa fecha actual")
    descripcion: str = Field(..., description="Descripción del movimiento")
    detalle: List[DetalleMovimiento] = Field(..., min_length=2, description="Debe contener al menos un débito y un crédito que cuadren")

    @model_validator(mode='after')
    def validar_partida_doble(self):
        debitos = sum(d.monto for d in self.detalle if d.tipo == TipoMovimiento.DEBITO)
        creditos = sum(d.monto for d in self.detalle if d.tipo == TipoMovimiento.CREDITO)
        if round(debitos, 2) != round(creditos, 2):
            raise ValueError(f"El movimiento no cuadra: débitos ({debitos}) != créditos ({creditos})")
        return self

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
