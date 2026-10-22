import json
from app.repositories.base import Arg, llamar_escalar, llamar_tabla
from app.schemas.movimientos import MovimientoCreate
from datetime import date
from typing import List, dict

    def registrar_movimiento(self, movimiento: MovimientoCreate):
        detalle_json = json.dumps([detalle.model_dump() for detalle in movimiento.detalle])
        
        nuevo_id = self.db.llamar_escalar(
            "registrar_movimiento",
            [
                Arg("p_fecha", movimiento.fecha),
                Arg("p_descripcion", movimiento.descripcion),
                Arg("p_detalle", detalle_json)
            ],
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
