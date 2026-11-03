"""Acceso a las funciones de BD de los movimientos contables (Módulo 5).

Los argumentos se envían por POSICIÓN, así que el orden de cada diccionario debe
coincidir con la firma de la función.
"""

from datetime import date
from typing import Any

from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories.base import Arg, llamar_escalar, llamar_tabla


class MovimientosRepository:
    """Llama registrar_movimiento, consultar_movimientos_diarios y consultar_movimientos_por_cuenta."""

    def __init__(self, db: Session):
        self.db = db

    def registrar(
        self, fecha: date | None, descripcion: str, detalle: list[dict[str, Any]]
    ) -> int:
        """registrar_movimiento(fecha, descripcion, detalle jsonb) devuelve el id_movimiento.

        detalle = [{"id_cuenta": 1, "monto": 50.0, "tipo": "DEBITO"}, ...]
        """
        return llamar_escalar(
            self.db,
            "registrar_movimiento",
            {
                "fecha": Arg(fecha, "date"),
                "descripcion": Arg(descripcion, "text"),
                "detalle": Arg(detalle, "jsonb"),
            },
            commit=True,
        )

    def consultar_diarios(self, fecha: date) -> list[dict[str, Any]]:
        """consultar_movimientos_diarios(fecha): una fila por línea de cada movimiento."""
        return llamar_tabla(
            self.db,
            "consultar_movimientos_diarios",
            {"fecha": Arg(fecha, "date")},
        )

    def consultar_por_cuenta(
        self, id_cuenta: int, fecha_inicio: date, fecha_fin: date
    ) -> list[dict[str, Any]]:
        """consultar_movimientos_por_cuenta(id_cuenta, fecha_inicio, fecha_fin)."""
        return llamar_tabla(
            self.db,
            "consultar_movimientos_por_cuenta",
            {
                "id_cuenta": Arg(id_cuenta, "integer"),
                "fecha_inicio": Arg(fecha_inicio, "date"),
                "fecha_fin": Arg(fecha_fin, "date"),
            },
        )


def get_movimientos_repository(db: Session = Depends(get_db)) -> MovimientosRepository:
    """Dependencia de FastAPI; las pruebas la reemplazan con un repositorio falso."""
    return MovimientosRepository(db)
