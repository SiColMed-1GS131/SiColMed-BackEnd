from app.repositories.base import Arg, llamar_tabla
from datetime import date
from typing import List, dict

def calcular_balance_general(fecha_inicio: date, fecha_fin: date) -> List[dict]:
    query = "SELECT * FROM calcular_balance_general(:p_inicio, :p_fin)"
    return llamar_tabla(
        query,
        Arg(fecha_inicio, "date"),
        Arg(fecha_fin, "date")
    )