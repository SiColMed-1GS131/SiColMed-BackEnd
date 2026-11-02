"""Repositorio para operaciones de filtrado y actualización de médicos."""

from typing import Any

from sqlalchemy.orm import Session

from app.repositories.base import Arg, llamar_escalar
from app.schemas.medicos_directorio import FiltroMedicos


class RepositorioMedicosDirectorio:
    """Acceso a las funciones del directorio médico de P2."""

    def filtrar_medicos(
        self,
        db: Session,
        filtros: FiltroMedicos,
    ) -> dict[str, Any]:
        resultado = llamar_escalar(
            db,
            "filtrar_medicos",
            {
                "apellido": Arg(filtros.apellido, "text"),
                "id_especialidad": Arg(filtros.id_especialidad, "integer"),
                "id_asociacion": Arg(filtros.id_asociacion, "integer"),
                "id_subespecialidad": Arg(
                    filtros.id_subespecialidad,
                    "integer",
                ),
                "certificacion_vigente": Arg(
                    filtros.certificacion_vigente,
                    "boolean",
                ),
                "id_provincia": Arg(filtros.id_provincia, "integer"),
                "lugar_trabajo": Arg(filtros.lugar_trabajo, "text"),
                "pagina": Arg(filtros.pagina, "integer"),
                "tamano_pagina": Arg(filtros.tamano_pagina, "integer"),
            },
        )
        if not isinstance(resultado, dict):
            raise TypeError("filtrar_medicos debe devolver un objeto JSON.")
        return resultado

    def actualizar_medico(
        self,
        db: Session,
        id_medico: int,
        id_administrador: int,
        datos: dict[str, object],
    ) -> bool:
        return llamar_escalar(
            db,
            "actualizar_medico",
            {
                "id_medico": Arg(id_medico, "integer"),
                "id_administrador": Arg(id_administrador, "integer"),
                "datos": Arg(datos, "jsonb"),
            },
            commit=True,
        )
