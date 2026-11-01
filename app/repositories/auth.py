"""Acceso a las funciones de BD de Login.

PENDIENTE (Login y permisos): implementar cada método con llamar_escalar o
llamar_tabla de app.repositories.base (ver los ejemplos de su docstring).
Los argumentos van por POSICIÓN, en el orden de la firma de cada función.
"""

from typing import Any

from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories.base import Arg, llamar_escalar, llamar_tabla


class AuthRepository:
    def __init__(self, db: Session):
        self.db = db

    def crear_cuenta_medico(
        self, numero_idoneidad: str, correo: str, password_hash: str
    ) -> int:
        """crear_cuenta_medico(numero_idoneidad, correo, password_hash) → id_usuario.

        TODO: llamar_escalar con Arg(..., "text") en ese orden y commit=True.
        Recibe el HASH, nunca la contraseña original.
        """
        return int(
            llamar_escalar(
                self.db,
                "crear_cuenta_medico",
                {
                    "numero_idoneidad": Arg(numero_idoneidad, "text"),
                    "correo": Arg(correo, "text"),
                    "password_hash": Arg(password_hash, "text"),
                },
                commit=True,
            )
        )

    def obtener_credenciales_usuario(self, correo: str) -> dict[str, Any] | None:
        """obtener_credenciales_usuario(correo) → id_usuario, correo, password_hash, rol, activo.

        TODO: llamar_tabla y devolver la primera fila, o None si el correo no
        existe (confirmar con BD qué devuelve en ese caso, decisión 7).
        """
        filas = llamar_tabla(
            self.db,
            "obtener_credenciales_usuario",
            {"correo": Arg(correo, "text")},
        )
        return filas[0] if filas else None

    def obtener_usuario_por_id(self, id_usuario: int) -> dict[str, Any] | None:
        """obtener_usuario_por_id(id_usuario) → id_usuario, nombre, correo,
        numero_idoneidad, rol, activo; None si no existe.

        TODO: llamar_tabla con Arg(id_usuario, "integer").
        """
        filas = llamar_tabla(
            self.db,
            "obtener_usuario_por_id",
            {"id_usuario": Arg(id_usuario, "integer")},
        )
        return filas[0] if filas else None


def get_auth_repository(db: Session = Depends(get_db)) -> AuthRepository:
    """Dependencia de FastAPI; las pruebas la reemplazan con un repositorio falso."""
    return AuthRepository(db)
