"""Reglas de negocio de los movimientos contables (Módulo 5).

La partida doble se valida dos veces: en MovimientoCreate (422) y en la
función registrar_movimiento de BD (400 por app.errors).
"""

from datetime import date

from fastapi import Depends

from app.repositories.movimientos import MovimientosRepository, get_movimientos_repository
from app.schemas.movimientos import (
    FilaMovimientoCuenta,
    FilaMovimientoDiario,
    MovimientoCreate,
    RangoFechasParams,
)


class MovimientosService:
    def __init__(self, repositorio: MovimientosRepository):
        self.repositorio = repositorio

    def registrar(self, movimiento: MovimientoCreate) -> int:
        detalle = [linea.model_dump(mode="json") for linea in movimiento.detalle]
        return self.repositorio.registrar(movimiento.fecha, movimiento.descripcion, detalle)

    def consultar_diarios(self, fecha: date) -> list[FilaMovimientoDiario]:
        return [FilaMovimientoDiario(**fila) for fila in self.repositorio.consultar_diarios(fecha)]

    def consultar_por_cuenta(
        self, id_cuenta: int, rango: RangoFechasParams
    ) -> list[FilaMovimientoCuenta]:
        filas = self.repositorio.consultar_por_cuenta(
            id_cuenta, rango.fecha_inicio, rango.fecha_fin
        )
        return [FilaMovimientoCuenta(**fila) for fila in filas]


def get_movimientos_service(
    repositorio: MovimientosRepository = Depends(get_movimientos_repository),
) -> MovimientosService:
    return MovimientosService(repositorio)
