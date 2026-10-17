"""Esquemas de las cuentas contables (Módulo 5, requisito 5.1)."""

from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, StringConstraints

# El documento de BD define `nombre` como text sin límite; 100 es un tope
# provisional para evitar textos excesivos. Confirmar con Base de datos.
NombreCuenta = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=100),
]


class TipoCuenta(StrEnum):
    """Naturaleza de la cuenta, según el diagrama del Módulo 5."""

    DEBITO = "DEBITO"
    CREDITO = "CREDITO"


class CuentaCrear(BaseModel):
    """Datos para crear una cuenta contable."""

    nombre: NombreCuenta
    tipo: TipoCuenta

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"examples": [{"nombre": "Caja general", "tipo": "DEBITO"}]},
    )


class CuentaEditar(BaseModel):
    """Datos completos de una cuenta; PUT reemplaza todos los campos."""

    nombre: NombreCuenta
    tipo: TipoCuenta
    activa: bool

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [{"nombre": "Caja general", "tipo": "DEBITO", "activa": True}]
        },
    )


class Cuenta(BaseModel):
    """Cuenta contable tal como la devuelve la API."""

    id_cuenta: int
    nombre: str
    tipo: TipoCuenta
    activa: bool

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"id_cuenta": 1, "nombre": "Caja general", "tipo": "DEBITO", "activa": True}
            ]
        },
    )


class CuentaEliminada(BaseModel):
    """Resultado de eliminar_cuenta: se borra si no tiene movimientos, si no se desactiva."""

    id_cuenta: int
    resultado: Literal["ELIMINADA", "DESACTIVADA"]

    model_config = ConfigDict(
        json_schema_extra={"examples": [{"id_cuenta": 1, "resultado": "DESACTIVADA"}]},
    )
