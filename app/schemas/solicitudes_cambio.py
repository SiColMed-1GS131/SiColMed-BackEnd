"""Schemas de solicitudes de cambio (contrato por secciones de la BD).

El contrato es el que ya implementan las funciones fusionadas en `develop`:
`crear_solicitud_cambio.sql`, `procesar_solicitud_cambio.sql` y
`listar_solicitudes_cambio.sql`. Las secciones permitidas son
`lugar_trabajo`, `estudio_medico`, `certificaciones` (arreglos de registros) y
`especialidades`, `subespecialidades`, `asociaciones` (relaciones
`{agregar, quitar}`). `medico` y `direccion` no se solicitan por este flujo.
"""

from datetime import datetime
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    PositiveInt,
    field_validator,
    model_validator,
)

EstadoDecision = Literal["APROBADO", "RECHAZADO"]
EstadoSolicitud = Literal["PENDIENTE", "PROCESADO"]

# Espejo de las listas blancas de `crear_solicitud_cambio.sql`.
CAMPOS_LUGAR_TRABAJO = frozenset({
    "empresa_institucion",
    "cargo",
    "telefono_trabajo",
    "email_laboral",
})
CAMPOS_ESTUDIO_MEDICO = frozenset({
    "tipo_estudio",
    "titulo",
    "institucion",
    "lugar",
    "fecha",
})
CAMPOS_CERTIFICACION = frozenset({
    "vigente",
    "fecha_obtencion",
    "puntaje",
    "fecha_expiracion",
})

SECCIONES_REGISTRO = ("lugar_trabajo", "estudio_medico", "certificaciones")
SECCIONES_RELACION = ("especialidades", "subespecialidades", "asociaciones")
SECCIONES_PERMITIDAS = frozenset(SECCIONES_REGISTRO + SECCIONES_RELACION)

_CAMPOS_POR_SECCION = {
    "lugar_trabajo": CAMPOS_LUGAR_TRABAJO,
    "estudio_medico": CAMPOS_ESTUDIO_MEDICO,
    "certificaciones": CAMPOS_CERTIFICACION,
}


class _RegistroCambio(BaseModel):
    """Base de un registro a modificar dentro de una sección."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    def campos_cambiados(self) -> dict:
        """Campos enviados (sin el id y sin valores nulos)."""
        return self.model_dump(exclude_none=True)

    @model_validator(mode="after")
    def exigir_al_menos_un_campo(self):
        datos = self.campos_cambiados()
        ids = {clave for clave in datos if clave.startswith("id_")}
        if not datos.keys() - ids:
            raise ValueError("Cada registro debe incluir al menos un campo a cambiar.")
        return self


class LugarTrabajoCambio(_RegistroCambio):
    id_lugar_trabajo: PositiveInt
    empresa_institucion: str | None = None
    cargo: str | None = None
    telefono_trabajo: str | None = None
    email_laboral: str | None = None


class EstudioMedicoCambio(_RegistroCambio):
    id_estudio: PositiveInt
    tipo_estudio: str | None = None
    titulo: str | None = None
    institucion: str | None = None
    lugar: str | None = None
    fecha: str | None = None


class CertificacionCambio(_RegistroCambio):
    id_certificacion: PositiveInt
    vigente: bool | None = None
    fecha_obtencion: str | None = None
    puntaje: int | None = None
    fecha_expiracion: str | None = None


class CambioRelacion(BaseModel):
    """Operaciones pendientes sobre una relación profesional."""

    model_config = ConfigDict(extra="forbid")
    agregar: list[PositiveInt] = Field(default_factory=list)
    quitar: list[PositiveInt] = Field(default_factory=list)

    @model_validator(mode="after")
    def validar_operaciones(self):
        if not self.agregar and not self.quitar:
            raise ValueError(
                "Debe indicar al menos un identificador para agregar o quitar."
            )
        if set(self.agregar) & set(self.quitar):
            raise ValueError("No se puede agregar y quitar el mismo identificador.")
        return self


class SolicitudCambioCrear(BaseModel):
    """Solicitud de cambio enviada por el médico."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [{
                "lugar_trabajo": [
                    {"id_lugar_trabajo": 3, "cargo": "Jefe de servicio"},
                ],
                "especialidades": {"agregar": [3], "quitar": []},
            }]
        },
    )

    lugar_trabajo: list[LugarTrabajoCambio] | None = None
    estudio_medico: list[EstudioMedicoCambio] | None = None
    certificaciones: list[CertificacionCambio] | None = None
    especialidades: CambioRelacion | None = None
    subespecialidades: CambioRelacion | None = None
    asociaciones: CambioRelacion | None = None

    @field_validator("lugar_trabajo", "estudio_medico", "certificaciones")
    @classmethod
    def seccion_no_vacia(cls, valor):
        if valor is not None and not valor:
            raise ValueError("La sección no puede enviarse vacía.")
        return valor

    @model_validator(mode="after")
    def exigir_al_menos_una_seccion(self):
        if not self.model_dump(exclude_none=True):
            raise ValueError("Debe indicar al menos una sección con cambios.")
        return self


class DecisionRelacion(BaseModel):
    """Decisión sobre una relación completa."""

    model_config = ConfigDict(extra="forbid")
    estado: EstadoDecision


class SolicitudCambioProcesar(BaseModel):
    """Decisiones del administrador sobre la solicitud de cambio.

    Las secciones de registro reciben un arreglo en el mismo orden que la
    solicitud; cada elemento asocia campo -> APROBADO/RECHAZADO. Las relaciones
    reciben únicamente ``{"estado": ...}``.
    """

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [{
                "lugar_trabajo": [{"cargo": "APROBADO"}],
                "especialidades": {"estado": "RECHAZADO"},
                "comentario": "Cambio revisado.",
            }]
        },
    )

    lugar_trabajo: list[dict[str, EstadoDecision]] | None = None
    estudio_medico: list[dict[str, EstadoDecision]] | None = None
    certificaciones: list[dict[str, EstadoDecision]] | None = None
    especialidades: DecisionRelacion | None = None
    subespecialidades: DecisionRelacion | None = None
    asociaciones: DecisionRelacion | None = None
    comentario: str | None = None

    @field_validator("lugar_trabajo", "estudio_medico", "certificaciones")
    @classmethod
    def decisiones_no_vacias(cls, valor, info):
        if valor is None:
            return valor
        if not valor:
            raise ValueError("La sección no puede enviarse vacía.")
        permitidos = _CAMPOS_POR_SECCION[info.field_name]
        for decisiones in valor:
            if not decisiones:
                raise ValueError("Cada registro debe tener al menos una decisión.")
            desconocidos = set(decisiones) - permitidos
            if desconocidos:
                raise ValueError(
                    f"Campo(s) no permitido(s) en {info.field_name}: "
                    + ", ".join(sorted(desconocidos))
                )
        return valor

    @model_validator(mode="after")
    def exigir_al_menos_una_decision(self):
        decisiones = self.model_dump(exclude_none=True, exclude={"comentario"})
        if not decisiones:
            raise ValueError("Debe indicar al menos una decisión.")
        return self


class SolicitudCambioCreada(BaseModel):
    """Respuesta al crear una solicitud de cambio."""

    model_config = ConfigDict(
        json_schema_extra={"examples": [{"id_solicitud_cambio": 12}]}
    )
    id_solicitud_cambio: int


class SolicitudCambioItem(BaseModel):
    """Fila de la bandeja del administrador."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{
                "id_solicitud_cambio": 12,
                "id_medico": 5,
                "nombre_completo": "Ana Pérez",
                "estado": "PENDIENTE",
                "fecha_solicitud": "2026-10-18T09:30:00",
                "cambios": {
                    "lugar_trabajo": [{
                        "id_lugar_trabajo": 3,
                        "cargo": {
                            "valor_anterior": "Médico general",
                            "valor_nuevo": "Jefe de servicio",
                            "estado": "PENDIENTE",
                        },
                    }],
                },
            }]
        }
    )
    id_solicitud_cambio: int
    id_medico: int
    nombre_completo: str
    estado: str
    fecha_solicitud: datetime
    cambios: dict
