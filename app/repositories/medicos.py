"""Repositorio para registrar un médico mediante un único documento JSONB.

La función PostgreSQL registrar_medico debe recibir ese documento completo y
ser responsable de la transacción y de las tablas relacionadas.
"""
from sqlalchemy.orm import Session
from app.repositories.base import Arg, llamar_escalar
from app.schemas.medicos import MedicoRegistro

class ContratoBDPendiente(RuntimeError):
    pass

def registrar_medico(db: Session, medico: MedicoRegistro) -> int:
    resultado = llamar_escalar(
        db,
        "registrar_medico",
        {"p_datos": Arg(medico.model_dump(mode="json"), "jsonb")},
        commit=True,
    )
    if not isinstance(resultado, int) or resultado <= 0:
        raise RuntimeError("registrar_medico no devolvió un id_medico válido")
    return resultado

def obtener_perfil_medico(db: Session, id_medico: int) -> dict | None:
    return llamar_escalar(db, "obtener_perfil_medico", {"id_medico": Arg(id_medico, "integer")})
