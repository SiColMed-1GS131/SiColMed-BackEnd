"""Endpoints de catálogos profesionales."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.catalogos_profesionales import EspecialidadItem
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