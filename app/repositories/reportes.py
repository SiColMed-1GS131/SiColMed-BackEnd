"""Acceso a las funciones de BD de los reportes contables (Módulo 5)."""

from datetime import date
from typing import Any

from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories.base import Arg, llamar_tabla


class ReportesRepository:
    """Llama calcular_balance_general."""

    def __init__(self, db: Session):
        self.db = db

    def balance_general(self, fecha_inicio: date, fecha_fin: date) -> list[dict[str, Any]]:
        """calcular_balance_general(fecha_inicio, fecha_fin): una fila por cuenta."""
        return llamar_tabla(
            self.db,
            "calcular_balance_general",
            {
                "fecha_inicio": Arg(fecha_inicio, "date"),
                "fecha_fin": Arg(fecha_fin, "date"),
            },
        )

    def tipos_de_cuenta(self) -> dict[int, str]:
        """listar_cuentas(NULL): tipo (DEBITO o CREDITO) de cada cuenta, activa o no.

        calcular_balance_general no devuelve el tipo; se toma de aquí para no cambiar
        la firma de esa función de BD.
        """
        filas = llamar_tabla(self.db, "listar_cuentas", {"activa": Arg(None, "boolean")})
        return {int(fila["id_cuenta"]): str(fila["tipo"]) for fila in filas}


def get_reportes_repository(db: Session = Depends(get_db)) -> ReportesRepository:
    """Dependencia de FastAPI; las pruebas la reemplazan con un repositorio falso."""
    return ReportesRepository(db)
