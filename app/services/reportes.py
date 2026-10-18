from app.schemas.movimientos import RangoFechasParams
from app.repositories import reportes as reportes_repo

def calcular_balance_general(rango_fechas: RangoFechasParams):
    return reportes_repo.calcular_balance_general(
        fecha_inicio=rango_fechas.fecha_inicio,
        fecha_fin=rango_fechas.fecha_fin
    )