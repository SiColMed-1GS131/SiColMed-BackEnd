"""Acceso a datos de catálogos profesionales."""

from typing import Any

from sqlalchemy.orm import Session

from app.repositories.base import Arg, llamar_tabla

# PENDIENTE DE CONFIRMAR CON BD: nombres de funciones y columnas de retorno.
FUNCION_LISTAR_ESPECIALIDADES = "listar_especialidades"
FUNCION_LISTAR_SUBESPECIALIDADES = "listar_subespecialidades"
FUNCION_LISTAR_ASOCIACIONES = "listar_asociaciones"


def listar_especialidades(db: Session) -> list[dict[str, Any]]:
    """Devuelve las especialidades disponibles en la base de datos."""
    return llamar_tabla(db, FUNCION_LISTAR_ESPECIALIDADES)


def listar_subespecialidades(
    db: Session, p_id_especialidad: int | None = None
) -> list[dict[str, Any]]:
    """Devuelve subespecialidades, opcionalmente filtradas por especialidad."""
    return llamar_tabla(
        db,
        FUNCION_LISTAR_SUBESPECIALIDADES,
        {"p_id_especialidad": Arg(p_id_especialidad, "integer")},
    )


def listar_asociaciones(db: Session) -> list[dict[str, Any]]:
    """Devuelve las asociaciones disponibles en la base de datos."""
    return llamar_tabla(db, FUNCION_LISTAR_ASOCIACIONES)
