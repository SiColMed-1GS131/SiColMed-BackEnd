"""Endpoints de catálogos profesionales."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.catalogos_profesionales import (
    AsociacionItem,
    EspecialidadItem,
    SubespecialidadItem,
)
from app.services import catalogos_profesionales as service

router = APIRouter(tags=["Catálogos profesionales"])


@router.get(
    "/especialidades",
    response_model=list[EspecialidadItem],
    status_code=200,
    summary="Listar especialidades",
    description="Devuelve el catálogo de especialidades médicas.",
    responses={400: {"description": "Error devuelto por la base de datos"}},
)
def listar_especialidades(
    db: Session = Depends(get_db),
) -> list[dict]:
    # PENDIENTE: requiere_rol cuando Login lo entregue.
    return service.listar_especialidades(db)


@router.get(
    "/subespecialidades",
    response_model=list[SubespecialidadItem],
    status_code=200,
    summary="Listar subespecialidades",
    description="Devuelve el catálogo de subespecialidades médicas.",
    responses={400: {"description": "Error devuelto por la base de datos"}},
)
def listar_subespecialidades(
    id_especialidad: int | None = Query(
        default=None, gt=0, examples=[1], description="Filtra por especialidad."
    ),
    db: Session = Depends(get_db),
) -> list[dict]:
    # PENDIENTE: requiere_rol cuando Login lo entregue.
    return service.listar_subespecialidades(db, id_especialidad)


@router.get(
    "/asociaciones",
    response_model=list[AsociacionItem],
    status_code=200,
    summary="Listar asociaciones",
    description="Devuelve el catálogo de asociaciones profesionales.",
    responses={400: {"description": "Error devuelto por la base de datos"}},
)
def listar_asociaciones(
    db: Session = Depends(get_db),
) -> list[dict]:
    # PENDIENTE: requiere_rol cuando Login lo entregue.
    return service.listar_asociaciones(db)
