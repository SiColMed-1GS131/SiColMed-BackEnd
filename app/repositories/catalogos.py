"""Consultas de solo lectura; IDs siempre parametrizados por SQLAlchemy."""
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.provincia import Provincia
from app.models.distrito import Distrito
from app.models.corregimiento import Corregimiento
from app.models.especialidad import Especialidad
from app.models.subespecialidad import Subespecialidad
from app.models.asociacion import Asociacion


def provincias(db: Session):
    return db.scalars(select(Provincia).order_by(Provincia.nombre, Provincia.id_provincia)).all()


def distritos(db: Session, id_provincia: int):
    return db.scalars(select(Distrito).where(Distrito.id_provincia == id_provincia).order_by(Distrito.nombre, Distrito.id_distrito)).all()


def corregimientos(db: Session, id_distrito: int):
    return db.scalars(select(Corregimiento).where(Corregimiento.id_distrito == id_distrito).order_by(Corregimiento.nombre, Corregimiento.id_corregimiento)).all()


def especialidades(db: Session):
    return db.scalars(select(Especialidad).order_by(Especialidad.nombre, Especialidad.id_especialidad)).all()


def subespecialidades(db: Session):
    return db.scalars(select(Subespecialidad).order_by(Subespecialidad.nombre, Subespecialidad.id_subespecialidad)).all()


def asociaciones(db: Session):
    return db.scalars(select(Asociacion).order_by(Asociacion.nombre, Asociacion.id_asociacion)).all()
