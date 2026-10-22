from sqlalchemy.orm import Session
from app.repositories import medicos as repository
from app.schemas.medicos import MedicoRegistro

def registrar_medico(db: Session, datos: MedicoRegistro) -> int:
    return repository.registrar_medico(db, datos)

def obtener_perfil_medico(db: Session, id_medico: int) -> dict | None:
    return repository.obtener_perfil_medico(db, id_medico)
