from pydantic import BaseModel, Field, PlainSerializer, field_validator, model_validator
from typing import Annotated, Optional, List
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from enum import Enum

# Panamá está en UTC-5 todo el año (sin horario de verano). El contenedor de la API
# corre en UTC: después de las 19:00 de Panamá, su fecha ya es la del día siguiente.
_ZONA_PANAMA = timezone(timedelta(hours=-5), "America/Panama")


def hoy_en_panama() -> date:
    return datetime.now(_ZONA_PANAMA).date()

class TipoMovimiento(str, Enum):
    DEBITO = "DEBITO"
    CREDITO = "CREDITO"

# DEF-019: el monto se valida como Decimal con 2 decimales exactos y el tamaño de la
# columna movimiento_cuenta.monto (numeric(12,2)). A la BD se sigue enviando como
# número JSON, igual que antes.
Monto = Annotated[
    Decimal,
    Field(gt=0, max_digits=12, decimal_places=2),
    PlainSerializer(float, return_type=float, when_used="json"),
]

class DetalleMovimiento(BaseModel):
    id_cuenta: int = Field(..., description="ID de la cuenta afectada")
    monto: Monto = Field(..., description="Mayor que cero, con 2 decimales como máximo")
    tipo: TipoMovimiento = Field(..., description="DEBITO o CREDITO")

class MovimientoCreate(BaseModel):
    # DEF-007: la fecha es obligatoria (RQ-5.2); sin ella o en null responde 422.
    fecha: date = Field(..., description="Fecha del movimiento (obligatoria, no puede ser futura)")
    descripcion: str = Field(..., description="Descripción del movimiento")
    detalle: List[DetalleMovimiento] = Field(..., min_length=2, description="Debe contener al menos un débito y un crédito que cuadren")

    @field_validator("fecha")
    @classmethod
    def fecha_no_futura(cls, valor: date) -> date:
        # DEF-019. "Hoy" es la fecha de Panamá, no la del servidor (UTC).
        if valor > hoy_en_panama():
            raise ValueError("La fecha del movimiento no puede ser futura.")
        return valor

    @field_validator("descripcion")
    @classmethod
    def descripcion_no_vacia(cls, valor: str) -> str:
        # DEF-019: una descripción de solo espacios se trataba como válida.
        valor = valor.strip()
        if not valor:
            raise ValueError("La descripción es obligatoria.")
        return valor

    @model_validator(mode='after')
    def validar_partida_doble(self):
        debitos = sum((d.monto for d in self.detalle if d.tipo == TipoMovimiento.DEBITO), Decimal("0"))
        creditos = sum((d.monto for d in self.detalle if d.tipo == TipoMovimiento.CREDITO), Decimal("0"))
        if debitos != creditos:
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
