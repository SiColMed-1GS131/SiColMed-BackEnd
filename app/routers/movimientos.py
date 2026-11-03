"""Endpoints de movimientos contables (Módulo 5, requisito 5.2)."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, status

from app.schemas.movimientos import (
    FilaMovimientoCuenta,
    FilaMovimientoDiario,
    MovimientoCreate,
    RangoFechasParams,
)
from app.security import roles
from app.security.auth import requiere_rol
from app.services.movimientos import MovimientosService, get_movimientos_service

_requiere_permiso_movimientos = requiere_rol(roles.TESORERO, roles.ADMIN_CMP)

router = APIRouter(
    tags=["Movimientos Contables"],
    dependencies=[Depends(_requiere_permiso_movimientos)],
)

Servicio = Annotated[MovimientosService, Depends(get_movimientos_service)]


@router.post("/movimientos", status_code=status.HTTP_201_CREATED, summary="Registrar movimiento")
def registrar_movimiento(movimiento: MovimientoCreate, servicio: Servicio):
    return {
        "mensaje": "Movimiento registrado exitosamente",
        "id_movimiento": servicio.registrar(movimiento),
    }


@router.get(
    "/movimientos",
    response_model=list[FilaMovimientoDiario],
    summary="Movimientos de un día",
)
def consultar_movimientos_diarios(
    servicio: Servicio,
    fecha: date = Query(..., description="Fecha obligatoria en formato YYYY-MM-DD"),
):
    return servicio.consultar_diarios(fecha)


@router.get(
    "/cuentas/{id_cuenta}/movimientos",
    response_model=list[FilaMovimientoCuenta],
    summary="Movimientos de una cuenta en un rango de fechas",
)
def consultar_movimientos_por_cuenta(
    servicio: Servicio,
    id_cuenta: int = Path(gt=0, description="Identificador de la cuenta"),
    rango: RangoFechasParams = Depends(),
):
    return servicio.consultar_por_cuenta(id_cuenta, rango)
