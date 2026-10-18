from fastapi import APIRouter, Depends, Query
from typing import List
from datetime import date

from app.schemas.movimientos import MovimientoCreate, FilaMovimientoDiario, FilaMovimientoCuenta, RangoFechasParams
from app.services import movimientos as movimientos_service

router = APIRouter(tags=["Movimientos Contables"])

@router.post("/movimientos", status_code=201)
def registrar_movimiento(movimiento: MovimientoCreate):
    id_mov = movimientos_service.registrar_movimiento(movimiento)
    return {
        "mensaje": "Movimiento registrado exitosamente",
        "id_movimiento": id_mov
    }

@router.get("/movimientos", response_model=List[FilaMovimientoDiario])
def consultar_movimientos_diarios(
    fecha: date = Query(..., description="Fecha obligatoria en formato YYYY-MM-DD")
):
    return movimientos_service.consultar_movimientos_diarios(fecha)

@router.get("/cuentas/{id_cuenta}/movimientos", response_model=List[FilaMovimientoCuenta])
def consultar_movimientos_por_cuenta(
    id_cuenta: int, 
    rango: RangoFechasParams = Depends()
):
    return movimientos_service.consultar_movimientos_por_cuenta(id_cuenta, rango)