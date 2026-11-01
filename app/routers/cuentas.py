"""Endpoints de cuentas contables (Módulo 5, requisito 5.1: crear, editar, eliminar)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, status

from app.schemas.cuentas import Cuenta, CuentaCrear, CuentaEditar, CuentaEliminada
from app.security import roles
from app.security.auth import requiere_rol
from app.services.cuentas import CuentasService, get_cuentas_service

_requiere_permiso_cuentas = requiere_rol(
    roles.ADMIN_CMP,
    roles.TESORERO,
    roles.ADMIN_ASOCIACION,
)

router = APIRouter(
    prefix="/cuentas",
    tags=["Cuentas contables"],
    dependencies=[Depends(_requiere_permiso_cuentas)],
)

Servicio = Annotated[CuentasService, Depends(get_cuentas_service)]
IdCuenta = Annotated[int, Path(gt=0, description="Identificador de la cuenta")]


def _error_bd(ejemplo: str) -> dict:
    return {
        "description": "La función de BD rechazó la operación (mensaje de PostgreSQL)",
        "content": {"application/json": {"example": {"detail": ejemplo}}},
    }


@router.get("", response_model=list[Cuenta], summary="Listar cuentas")
def listar_cuentas(
    servicio: Servicio,
    activa: Annotated[
        bool | None,
        Query(description="true: solo activas · false: solo desactivadas · vacío: todas"),
    ] = None,
):
    return servicio.listar(activa)


@router.post(
    "",
    response_model=Cuenta,
    status_code=status.HTTP_201_CREATED,
    summary="Crear cuenta",
    responses={400: _error_bd("El tipo de cuenta debe ser DEBITO o CREDITO")},
)
def crear_cuenta(datos: CuentaCrear, servicio: Servicio):
    return servicio.crear(datos)


@router.put(
    "/{id_cuenta}",
    response_model=Cuenta,
    summary="Editar cuenta",
    description=(
        "Reemplaza nombre, tipo y estado. Si la cuenta ya tiene movimientos, "
        "la BD no permite cambiar el tipo."
    ),
    responses={
        400: _error_bd("No se puede cambiar el tipo de una cuenta con movimientos"),
        404: {
            "description": "La cuenta no existe",
            "content": {"application/json": {"example": {"detail": "No existe la cuenta 99"}}},
        },
    },
)
def editar_cuenta(id_cuenta: IdCuenta, datos: CuentaEditar, servicio: Servicio):
    return servicio.editar(id_cuenta, datos)


@router.delete(
    "/{id_cuenta}",
    response_model=CuentaEliminada,
    summary="Eliminar o desactivar cuenta",
    description=(
        "Si la cuenta nunca tuvo movimientos se borra (ELIMINADA); si los tiene, "
        "se desactiva para conservar el historial (DESACTIVADA)."
    ),
    responses={400: _error_bd("La cuenta 99 no existe")},
)
def eliminar_cuenta(id_cuenta: IdCuenta, servicio: Servicio):
    return servicio.eliminar(id_cuenta)
