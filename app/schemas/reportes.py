from typing import List, Literal

from pydantic import BaseModel


class FilaBalanceGeneral(BaseModel):
    id_cuenta: int
    nombre_cuenta: str
    # Naturaleza de la cuenta: indica cómo se calculó su saldo (DEBITO: débitos - créditos;
    # CREDITO: créditos - débitos) y en qué total se suma.
    tipo: Literal["DEBITO", "CREDITO"]
    total_debito: float
    total_credito: float
    saldo: float


class TotalesBalanceGeneral(BaseModel):
    """Totales del rango. Los saldos se separan por naturaleza: sumar un saldo deudor
    con uno acreedor no tiene sentido contable."""

    total_debito: float
    total_credito: float
    saldo_deudor: float     # suma de los saldos de las cuentas DEBITO
    saldo_acreedor: float   # suma de los saldos de las cuentas CREDITO
    cuadra: bool            # partida doble: total_debito == total_credito


class BalanceGeneralResponse(BaseModel):
    filas: List[FilaBalanceGeneral]
    totales: TotalesBalanceGeneral
