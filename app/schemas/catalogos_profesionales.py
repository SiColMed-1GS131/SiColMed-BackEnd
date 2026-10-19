"""Schemas de los catálogos profesionales."""
from pydantic import BaseModel, ConfigDict


class EspecialidadItem(BaseModel):
    """Especialidad médica del catálogo."""
    model_config = ConfigDict(
        json_schema_extra={
            'examples': [{'id_especialidad': 1, 'nombre': 'Cardiología'}]
        }
    )
    id_especialidad: int
    nombre: str


class SubespecialidadItem(BaseModel):
    """Subespecialidad médica, ligada a una especialidad."""
    model_config = ConfigDict(
        json_schema_extra={
            'examples': [{
                'id_subespecialidad': 3,
                'id_especialidad': 1,
                'nombre': 'Electrofisiología',
            }]
        }
    )
    id_subespecialidad: int
    id_especialidad: int
    nombre: str


class AsociacionItem(BaseModel):
    """Asociación profesional del catálogo."""
    model_config = ConfigDict(
        json_schema_extra={
            'examples': [{'id_asociacion': 2, 'nombre': 'Sociedad de Cardiología'}]
        }
    )
    id_asociacion: int
    nombre: str