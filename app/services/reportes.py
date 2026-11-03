"""Reglas de negocio de los reportes contables (Módulo 5)."""

from fastapi import Depends

from app.repositories.reportes import ReportesRepository, get_reportes_repository
from app.schemas.movimientos import RangoFechasParams
from app.schemas.reportes import (
    BalanceGeneralResponse,
    FilaBalanceGeneral,
    TotalesBalanceGeneral,
)


def _centavos(monto: float) -> int:
    # Montos numeric(12,2) que llegan como float: se suman en centavos para no acumular errores
    return round(float(monto) * 100)


class ReportesService:
    def __init__(self, repositorio: ReportesRepository):
        self.repositorio = repositorio

    def balance_general(self, rango: RangoFechasParams) -> BalanceGeneralResponse:
        filas_bd = self.repositorio.balance_general(rango.fecha_inicio, rango.fecha_fin)
        tipos = self.repositorio.tipos_de_cuenta()
        filas = [FilaBalanceGeneral(**fila, tipo=tipos[fila["id_cuenta"]]) for fila in filas_bd]

        debito = sum(_centavos(f.total_debito) for f in filas)
        credito = sum(_centavos(f.total_credito) for f in filas)
        totales = TotalesBalanceGeneral(
            total_debito=debito / 100,
            total_credito=credito / 100,
            saldo_deudor=sum(_centavos(f.saldo) for f in filas if f.tipo == "DEBITO") / 100,
            saldo_acreedor=sum(_centavos(f.saldo) for f in filas if f.tipo == "CREDITO") / 100,
            cuadra=debito == credito,
        )
        return BalanceGeneralResponse(filas=filas, totales=totales)


def get_reportes_service(
    repositorio: ReportesRepository = Depends(get_reportes_repository),
) -> ReportesService:
    return ReportesService(repositorio)
