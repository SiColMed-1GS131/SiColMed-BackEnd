"""Acceso a funciones de BD asignadas a P1.

La firma de registrar_medico todavía NO está acordada con Base de Datos.
No enviar argumentos posicionales inventados a PostgreSQL.
"""
from sqlalchemy.orm import Session
from app.repositories.base import Arg, llamar_escalar
from app.schemas.medicos import MedicoRegistro


class ContratoBDPendiente(RuntimeError):
    pass


def registrar_medico(db: Session, medico: MedicoRegistro) -> int:
    raise ContratoBDPendiente(
        "Pendiente: BD debe confirmar la firma y el orden de argumentos de registrar_medico"
    )


def obtener_perfil_medico(db: Session, id_medico: int) -> dict | None:
    # Único parámetro documentado: id_medico INTEGER; retorno JSON.
    return llamar_escalar(
        db, "obtener_perfil_medico", {"id_medico": Arg(id_medico, "integer")}
    )
