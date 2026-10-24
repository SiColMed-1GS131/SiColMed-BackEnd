"""Respuestas de los catálogos utilizados por el Frontend."""
from pydantic import BaseModel, ConfigDict

class ProvinciaItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id_provincia: int
    nombre: str

class DistritoItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id_distrito: int
    id_provincia: int
    nombre: str

class CorregimientoItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id_corregimiento: int
    id_distrito: int
    nombre: str

class EspecialidadItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id_especialidad: int
    nombre: str

class SubespecialidadItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id_subespecialidad: int
    id_especialidad: int
    nombre: str

class AsociacionItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id_asociacion: int
    nombre: str
