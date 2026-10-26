"""Acceso a las funciones de BD de Login.

PENDIENTE (Login y permisos): implementar cada método con llamar_escalar o
llamar_tabla de app.repositories.base (ver los ejemplos de su docstring).
Los argumentos van por POSICIÓN, en el orden de la firma de cada función.
"""

from typing import Any

from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import get_db


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
        raise NotImplementedError("Pendiente: crear_cuenta_medico")

    def obtener_credenciales_usuario(self, correo: str) -> dict[str, Any] | None:
        """obtener_credenciales_usuario(correo) → id_usuario, correo, password_hash, rol, activo.

        TODO: llamar_tabla y devolver la primera fila, o None si el correo no
        existe (confirmar con BD qué devuelve en ese caso, decisión 7).
        """
        raise NotImplementedError("Pendiente: obtener_credenciales_usuario")

    def obtener_usuario_por_id(self, id_usuario: int) -> dict[str, Any] | None:
        """obtener_usuario_por_id(id_usuario) → id_usuario, nombre, correo,
        numero_idoneidad, rol, activo; None si no existe.

        TODO: llamar_tabla con Arg(id_usuario, "integer").
        """
        raise NotImplementedError("Pendiente: obtener_usuario_por_id")


def get_auth_repository(db: Session = Depends(get_db)) -> AuthRepository:
    """Dependencia de FastAPI; las pruebas la reemplazan con un repositorio falso."""
    return AuthRepository(db)
