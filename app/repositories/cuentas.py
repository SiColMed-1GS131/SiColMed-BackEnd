"""Acceso a las funciones de BD de las cuentas contables (Módulo 5).

Las firmas siguen el documento de BD (Documentacion_BD_ISA3, Módulo 5). Los
argumentos se envían por POSICIÓN, así que el orden de cada diccionario debe
coincidir con la firma de la función.
"""

from typing import Any

from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories.base import Arg, llamar_escalar, llamar_tabla


class CuentasRepository:
    """Llama crear_cuenta, editar_cuenta, eliminar_cuenta y listar_cuentas."""

    def __init__(self, db: Session):
        self.db = db

    def crear(self, nombre: str, tipo: str) -> int:
        """crear_cuenta(nombre, tipo) devuelve el id_cuenta creado."""
        return llamar_escalar(
            self.db,
            "crear_cuenta",
            {"nombre": Arg(nombre, "text"), "tipo": Arg(tipo, "text")},
            commit=True,
        )

    def editar(self, id_cuenta: int, nombre: str, tipo: str, activa: bool) -> bool:
        """editar_cuenta(id_cuenta, nombre, tipo, activa) devuelve si se editó."""
        return llamar_escalar(
            self.db,
            "editar_cuenta",
            {
                "id_cuenta": Arg(id_cuenta, "integer"),
                "nombre": Arg(nombre, "text"),
                "tipo": Arg(tipo, "text"),
                "activa": Arg(activa, "boolean"),
            },
            commit=True,
        )

    def eliminar(self, id_cuenta: int) -> str:
        """eliminar_cuenta(id_cuenta) devuelve 'ELIMINADA' o 'DESACTIVADA'."""
        return llamar_escalar(
            self.db,
            "eliminar_cuenta",
            {"id_cuenta": Arg(id_cuenta, "integer")},
            commit=True,
        )

    def listar(self, activa: bool | None) -> list[dict[str, Any]]:
        """listar_cuentas(activa) devuelve id_cuenta, nombre, tipo y activa.

        Esta función NO está en el documento de BD: es la firma que se propone
        a Base de datos. Con activa = NULL devuelve todas las cuentas.
        """
        return llamar_tabla(
            self.db,
            "listar_cuentas",
            {"activa": Arg(activa, "boolean")},
        )


def get_cuentas_repository(db: Session = Depends(get_db)) -> CuentasRepository:
    """Dependencia de FastAPI; las pruebas la reemplazan con un repositorio falso."""
    return CuentasRepository(db)
