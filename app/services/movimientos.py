from datetime import date
from app.schemas.movimientos import MovimientoCreate, RangoFechasParams
from app.repositories import movimientos as movimientos_repo

def registrar_movimiento(movimiento: MovimientoCreate) -> int:
    return movimientos_repo.registrar_movimiento(movimiento)

def consultar_movimientos_diarios(fecha: date):
    return movimientos_repo.consultar_movimientos_diarios(fecha)

def consultar_movimientos_por_cuenta(id_cuenta: int, rango_fechas: RangoFechasParams):
    return movimientos_repo.consultar_movimientos_por_cuenta(
        id_cuenta=id_cuenta,
        fecha_inicio=rango_fechas.fecha_inicio,
        fecha_fin=rango_fechas.fecha_fin
    )