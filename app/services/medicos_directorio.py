"""Reglas de negocio para filtros y actualización de médicos."""

from math import ceil
from typing import Protocol

from sqlalchemy.orm import Session
from pydantic import ValidationError

from app.errors import MedicoNoEncontrado, RespuestaBDInvalida
from app.schemas.medicos_directorio import (
    ActualizarMedicoRespuesta,
    ActualizarMedicoSolicitud,
    CamposActualizablesMedico,
    FiltroMedicos,
    ListaMedicosRespuesta,
    MedicoResumen,
)


class RepositorioFiltroMedicos(Protocol):
    """Contrato que debe cumplir el repositorio de filtrado."""

    def filtrar_medicos(
        self,
        db: Session,
        filtros: FiltroMedicos,
    ) -> dict[str, object]:
        ...


class RepositorioActualizacionMedico(Protocol):
    """Contrato que debe cumplir el repositorio de actualización."""

    def actualizar_medico(
        self,
        db: Session,
        id_medico: int,
        id_administrador: int,
        datos: dict[str, object],
    ) -> bool:
        ...


def obtener_medicos(
    db: Session,
    filtros: FiltroMedicos,
    repositorio: RepositorioFiltroMedicos,
) -> ListaMedicosRespuesta:
    """Obtiene una página de médicos y calcula sus metadatos."""
    resultado = repositorio.filtrar_medicos(db, filtros)
    elementos = resultado.get("items")
    total = resultado.get("total")

    if not isinstance(elementos, list) or not isinstance(total, int):
        raise RespuestaBDInvalida(
            "La respuesta de filtrar_medicos debe contener items y total."
        )
    if total < 0:
        raise RespuestaBDInvalida("El total de médicos no puede ser negativo.")

    try:
        medicos = [
            MedicoResumen.model_validate(elemento)
            for elemento in elementos
        ]
    except ValidationError as error:
        raise RespuestaBDInvalida(
            "La respuesta de filtrar_medicos contiene médicos inválidos."
        ) from error
    total_paginas = ceil(total / filtros.tamano_pagina) if total else 0
    return ListaMedicosRespuesta(
        medicos=medicos,
        total=total,
        pagina=filtros.pagina,
        tamano_pagina=filtros.tamano_pagina,
        total_paginas=total_paginas,
    )


def actualizar_medico(
    db: Session,
    id_medico: int,
    id_administrador: int,
    datos: ActualizarMedicoSolicitud,
    repositorio: RepositorioActualizacionMedico,
) -> ActualizarMedicoRespuesta:
    """Valida y ejecuta una actualización administrativa de médico."""
    if id_medico < 1:
        raise ValueError("El id del médico debe ser mayor que cero.")
    if id_administrador < 1:
        raise ValueError("El id del administrador debe ser mayor que cero.")

    cambios = datos.model_dump(exclude_unset=True)
    campos_no_permitidos = set(cambios) - CamposActualizablesMedico
    if campos_no_permitidos:
        nombres = ", ".join(sorted(campos_no_permitidos))
        raise ValueError(f"Campos no permitidos para actualizar: {nombres}.")
    if not cambios:
        raise ValueError("Debe enviar al menos un campo para actualizar.")

    actualizado = repositorio.actualizar_medico(
        db,
        id_medico,
        id_administrador,
        cambios,
    )
    if not actualizado:
        raise MedicoNoEncontrado(
            f"No se encontró el médico con id {id_medico}."
        )
    return ActualizarMedicoRespuesta(actualizado=actualizado)
