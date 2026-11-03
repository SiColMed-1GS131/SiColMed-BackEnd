"""Endpoints de reportes contables (Módulo 5, requisito 5.3)."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.schemas.movimientos import RangoFechasParams
from app.schemas.reportes import BalanceGeneralResponse
from app.security import roles
from app.security.auth import requiere_rol
from app.services.reportes import ReportesService, get_reportes_service

_requiere_permiso_reportes = requiere_rol(roles.ADMIN_ASOCIACION, roles.ADMIN_CMP)

router = APIRouter(
    prefix="/reportes",
    tags=["Reportes Contables"],
    dependencies=[Depends(_requiere_permiso_reportes)],
)

Servicio = Annotated[ReportesService, Depends(get_reportes_service)]


@router.get(
    "/balance-general",
    response_model=BalanceGeneralResponse,
    summary="Balance general en un rango de fechas",
)
def calcular_balance_general(servicio: Servicio, rango: RangoFechasParams = Depends()):
    return servicio.balance_general(rango)
