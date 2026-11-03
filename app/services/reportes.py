"""Reglas de negocio de los reportes contables (Módulo 5)."""

from fastapi import Depends

from app.repositories.reportes import ReportesRepository, get_reportes_repository
from app.schemas.movimientos import RangoFechasParams
from app.schemas.reportes import BalanceGeneralResponse, FilaBalanceGeneral


class ReportesService:
    def __init__(self, repositorio: ReportesRepository):
        self.repositorio = repositorio

    def balance_general(self, rango: RangoFechasParams) -> BalanceGeneralResponse:
        filas = self.repositorio.balance_general(rango.fecha_inicio, rango.fecha_fin)
        return BalanceGeneralResponse(filas=[FilaBalanceGeneral(**fila) for fila in filas])


def get_reportes_service(
    repositorio: ReportesRepository = Depends(get_reportes_repository),
) -> ReportesService:
    return ReportesService(repositorio)
