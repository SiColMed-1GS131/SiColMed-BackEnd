"""Capa de servicios de catálogos (consultas de solo lectura)."""
from app.repositories import catalogos as repository

def listar_provincias(db): return repository.provincias(db)
def listar_distritos(db, id_provincia): return repository.distritos(db, id_provincia)
def listar_corregimientos(db, id_distrito): return repository.corregimientos(db, id_distrito)
def listar_especialidades(db): return repository.especialidades(db)
def listar_subespecialidades(db): return repository.subespecialidades(db)
def listar_asociaciones(db): return repository.asociaciones(db)
