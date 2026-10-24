"""Catálogos públicos para formularios y filtros."""
from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.catalogos import (ProvinciaItem, DistritoItem, CorregimientoItem,
                                  EspecialidadItem, SubespecialidadItem, AsociacionItem)
from app.services import catalogos as service

router = APIRouter(tags=["Catálogos"])

@router.get("/provincias", response_model=list[ProvinciaItem])
def listar_provincias(db: Session = Depends(get_db)):
    return service.listar_provincias(db)

@router.get("/provincias/{id_provincia}/distritos", response_model=list[DistritoItem])
def listar_distritos(id_provincia: int = Path(ge=1), db: Session = Depends(get_db)):
    return service.listar_distritos(db, id_provincia)

@router.get("/distritos/{id_distrito}/corregimientos", response_model=list[CorregimientoItem])
def listar_corregimientos(id_distrito: int = Path(ge=1), db: Session = Depends(get_db)):
    return service.listar_corregimientos(db, id_distrito)

@router.get("/especialidades", response_model=list[EspecialidadItem])
def listar_especialidades(db: Session = Depends(get_db)):
    return service.listar_especialidades(db)

@router.get("/subespecialidades", response_model=list[SubespecialidadItem])
def listar_subespecialidades(db: Session = Depends(get_db)):
    return service.listar_subespecialidades(db)

@router.get("/asociaciones", response_model=list[AsociacionItem])
def listar_asociaciones(db: Session = Depends(get_db)):
    return service.listar_asociaciones(db)
