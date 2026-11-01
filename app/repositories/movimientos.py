import json
from app.repositories.base import Arg, llamar_escalar, llamar_tabla
from app.schemas.movimientos import MovimientoCreate
from datetime import date
from typing import List, dict

def registrar_movimiento(movimiento: MovimientoCreate):
    detalle_json = json.dumps([detalle.model_dump() for detalle in movimiento.detalle])
    
    query = "SELECT registrar_movimiento(:p_fecha, :p_descripcion, :p_detalle)"
    
    nuevo_id = llamar_escalar(
        query,
        Arg(movimiento.fecha, "date"),
        Arg(movimiento.descripcion, "text"),
        Arg(detalle_json, "jsonb"),
        commit=True
    )
    return nuevo_id

def consultar_movimientos_diarios(fecha: date) -> List[dict]:
    query = "SELECT * FROM consultar_movimientos_diarios(:p_fecha)"
    return llamar_tabla(query, Arg(fecha, "date"))

def consultar_movimientos_por_cuenta(id_cuenta: int, fecha_inicio: date, fecha_fin: date) -> List[dict]:
    query = "SELECT * FROM consultar_movimientos_por_cuenta(:p_id_cuenta, :p_inicio, :p_fin)"
    return llamar_tabla(
        query,
        Arg(id_cuenta, "integer"),
        Arg(fecha_inicio, "date"),
        Arg(fecha_fin, "date")
    )
    
