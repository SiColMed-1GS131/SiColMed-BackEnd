"""Acceso exclusivo a funciones de BD existentes, sin DDL ni migraciones."""
from typing import Any
from fastapi import Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.repositories.base import Arg, llamar_escalar, llamar_tabla

class AuthRepository:
    def __init__(self, db: Session):
        self.db = db

    def crear_cuenta_medico(self, numero_idoneidad: str, correo: str, password_hash: str) -> int:
        return int(llamar_escalar(self.db, "crear_cuenta_medico", {
            "numero_idoneidad": Arg(numero_idoneidad, "text"),
            "correo": Arg(correo, "text"),
            "password_hash": Arg(password_hash, "text"),
        }, commit=True))

    def obtener_credenciales_usuario(self, correo: str) -> dict[str, Any] | None:
        filas = llamar_tabla(self.db, "obtener_credenciales_usuario", {"correo": Arg(correo, "text")})
        return filas[0] if filas else None

    def obtener_usuario_por_id(self, id_usuario: int) -> dict[str, Any] | None:
        filas = llamar_tabla(self.db, "obtener_usuario_por_id", {"id_usuario": Arg(id_usuario, "integer")})
        return filas[0] if filas else None

def get_auth_repository(db: Session = Depends(get_db)) -> AuthRepository:
    return AuthRepository(db)
