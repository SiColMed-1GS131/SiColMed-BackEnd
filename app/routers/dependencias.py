"""Dependencias compartidas por los routers."""

from datetime import date

from fastapi import HTTPException, Query

from app.schemas.movimientos import RangoFechasParams

MENSAJE_RANGO_INVERTIDO = "La fecha de inicio no puede ser posterior a la fecha de fin"


def rango_de_fechas(
    fecha_inicio: date = Query(..., description="Fecha inicial (YYYY-MM-DD)"),
    fecha_fin: date = Query(..., description="Fecha final (YYYY-MM-DD)"),
) -> RangoFechasParams:
    """Rango de fechas de movimientos por cuenta y del balance general (DEF-012).

    Con Depends(RangoFechasParams), el ValidationError del model_validator ocurría
    dentro de la dependencia y FastAPI respondía 500. Aquí se valida antes y un
    rango invertido responde 422.
    """
    if fecha_inicio > fecha_fin:
        raise HTTPException(status_code=422, detail=MENSAJE_RANGO_INVERTIDO)
    return RangoFechasParams(fecha_inicio=fecha_inicio, fecha_fin=fecha_fin)
