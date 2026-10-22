"""Acceso a datos de catálogos profesionales."""

from typing import Any

from sqlalchemy.orm import Session

from app.repositories.base import llamar_tabla

# PROVISIONAL: nombre pendiente de confirmación por Base de Datos.
FUNCION_LISTAR_ESPECIALIDADES = "listar_especialidades"


def listar_especialidades(db: Session) -> list[dict[str, Any]]:
    """Devuelve las especialidades disponibles en la base de datos."""
    return llamar_tabla(db, FUNCION_LISTAR_ESPECIALIDADES)