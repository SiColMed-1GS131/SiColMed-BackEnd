"""Schemas para filtros y actualización administrativa de médicos."""

from datetime import date
from typing import ClassVar, Final

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


CamposActualizablesMedico: Final[frozenset[str]] = frozenset(
    {
        "numero_idoneidad",
        "numero_registro_medico",
        "cedula",
        "primer_nombre",
        "segundo_nombre",
        "apellido_paterno",
        "apellido_materno",
        "foto",
        "fecha_nacimiento",
        "telefono_residencial",
        "celular",
        "email_personal",
    }
)
CamposActualizablesDireccion: Final[frozenset[str]] = frozenset(
    {
        "apartado_postal",
        "calle",
        "edificio",
        "numero_direccion",
        "id_corregimiento",
    }
)
# Lo que el propio médico puede editar (sección 2.3 del documento del CMP: lo subrayado
# no se edita). Cédula, registro médico, idoneidad, certificado PDF, título básico,
# certificación, educación continua y estado de cuenta quedan fuera (los edita el admin).
CamposActualizablesPerfilMedico: Final[frozenset[str]] = frozenset(
    {
        "fecha_nacimiento",
        "primer_nombre",
        "segundo_nombre",
        "apellido_paterno",
        "apellido_materno",
        "foto",
        "telefono_residencial",
        "celular",
        "email_personal",
        "direccion",
    }
)

# Endpoint 1: GET /medicos


class FiltroMedicos(BaseModel):
    apellido: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )
    id_especialidad: int | None = Field(
        default=None,
        ge=1,
    )
    id_asociacion: int | None = Field(
        default=None,
        ge=1,
    )
    id_subespecialidad: int | None = Field(
        default=None,
        ge=1,
    )
    certificacion_vigente: bool | None = None
    id_provincia: int | None = Field(
        default=None,
        ge=1,
    )
    lugar_trabajo: str | None = Field(
        default=None,
        min_length=1,
        max_length=150,
    )
    pagina: int = Field(
        default=1,
        ge=1,
    )
    tamano_pagina: int = Field(
        default=20,
        ge=1,
        le=100,
    )


# Resumen de medico devuelto por la función de filtrado
class MedicoResumen(BaseModel):
    id_medico: int
    nombre_completo: str
    numero_idoneidad: str
    especialidades: str | None = None
    asociaciones: str | None = None
    certificacion_vigente: bool | None = None
    provincia: str | None = None
    lugar_trabajo: str | None = None


class ListaMedicosRespuesta(BaseModel):
    medicos: list[MedicoResumen]
    total: int
    pagina: int
    tamano_pagina: int
    total_paginas: int


# Endpoint 2: patch /medicos/{id_medico}
class ActualizarDireccionSolicitud(BaseModel):
    """Campos de dirección residencial que pueden actualizarse."""

    model_config = ConfigDict(extra="forbid")

    apartado_postal: str | None = Field(default=None, min_length=1)
    calle: str | None = Field(default=None, min_length=1)
    edificio: str | None = Field(default=None, min_length=1)
    numero_direccion: str | None = Field(default=None, min_length=1)
    id_corregimiento: int | None = Field(default=None, ge=1)


class _SeccionConId(BaseModel):
    """Una fila de la sección: con su id se actualiza una existente; sin id se agrega una nueva.

    - Con id: al menos un campo a cambiar además del id (DEF-014/015).
    - Sin id (solo lugar_trabajo y estudio_medico): deben venir todos los campos de
      _OBLIGATORIOS_NUEVO, porque la BD crea la fila completa (M2-REG-09 y M2-REG-10).
    """

    model_config = ConfigDict(extra="forbid")
    _CAMPO_ID: ClassVar[str] = ""
    _OBLIGATORIOS_NUEVO: ClassVar[tuple[str, ...]] = ()

    @model_validator(mode="after")
    def validar_existente_o_nueva(self):
        if getattr(self, self._CAMPO_ID) is not None:
            if not (self.model_fields_set - {self._CAMPO_ID}):
                raise ValueError(
                    "Indica al menos un campo a cambiar además del id.")
            return self
        faltan = [c for c in self._OBLIGATORIOS_NUEVO if getattr(
            self, c) is None]
        if faltan:
            raise ValueError(
                f"Para agregar un registro nuevo (sin {self._CAMPO_ID}) faltan: {', '.join(faltan)}."
            )
        return self


class DireccionTrabajoNueva(BaseModel):
    """Dirección de un lugar de trabajo nuevo: la BD la crea junto con el lugar."""

    model_config = ConfigDict(extra="forbid")

    apartado_postal: str = Field(min_length=1)
    calle: str = Field(min_length=1)
    edificio: str | None = Field(default=None, min_length=1)
    numero_direccion: str = Field(min_length=1)
    id_corregimiento: int = Field(ge=1)


class ActualizarLugarTrabajoSolicitud(_SeccionConId):
    _CAMPO_ID: ClassVar[str] = "id_lugar_trabajo"
    _OBLIGATORIOS_NUEVO: ClassVar[tuple[str, ...]] = (
        "empresa_institucion", "cargo", "telefono_trabajo", "email_laboral", "direccion",
    )
    # Sin id_lugar_trabajo se agrega un lugar nuevo (con direccion). Un null explícito se rechaza.
    id_lugar_trabajo: int = Field(default=None, ge=1)
    empresa_institucion: str | None = Field(default=None, min_length=1)
    cargo: str | None = Field(default=None, min_length=1)
    telefono_trabajo: str | None = Field(default=None, min_length=1)
    email_laboral: EmailStr | None = None
    # Solo para un lugar nuevo: la dirección de uno existente no se edita en este endpoint.
    direccion: DireccionTrabajoNueva | None = None

    @model_validator(mode="after")
    def direccion_solo_en_lugar_nuevo(self):
        if self.id_lugar_trabajo is not None and "direccion" in self.model_fields_set:
            raise ValueError(
                "La dirección de un lugar de trabajo existente no se edita aquí.")
        return self


class ActualizarEstudioMedicoSolicitud(_SeccionConId):
    _CAMPO_ID: ClassVar[str] = "id_estudio"
    _OBLIGATORIOS_NUEVO: ClassVar[tuple[str, ...]] = (
        "tipo_estudio", "titulo", "institucion", "lugar", "fecha",
    )
    # Sin id_estudio se agrega un estudio nuevo (por ejemplo, el título básico).
    id_estudio: int = Field(default=None, ge=1)
    tipo_estudio: str | None = Field(default=None, min_length=1)
    titulo: str | None = Field(default=None, min_length=1)
    institucion: str | None = Field(default=None, min_length=1)
    lugar: str | None = Field(default=None, min_length=1)
    fecha: date | None = None


class ActualizarCertificacionSolicitud(_SeccionConId):
    _CAMPO_ID: ClassVar[str] = "id_certificacion"
    id_certificacion: int = Field(ge=1)
    vigente: bool | None = None
    fecha_obtencion: date | None = None
    puntaje: int | None = Field(default=None, ge=0)
    fecha_expiracion: date | None = None


class CambiosRelacionesSolicitud(BaseModel):
    model_config = ConfigDict(extra="forbid")
    # DEF-014: "quitar" (y "agregar") son opcionales; el service siempre envía los dos.
    agregar: list[int] = Field(default_factory=list)
    quitar: list[int] = Field(default_factory=list)

    @model_validator(mode="after")
    def validar(self):
        for nombre in ("agregar", "quitar"):
            valores = getattr(self, nombre)
            if any(v <= 0 for v in valores) or len(set(valores)) != len(valores):
                raise ValueError(f"{nombre}: IDs positivos y sin duplicados")
        if set(self.agregar) & set(self.quitar):
            raise ValueError("El mismo ID no puede agregarse y quitarse")
        return self


class ActualizarMedicoSolicitud(BaseModel):
    """Campos que la API puede recibir para actualizar un médico."""

    model_config = ConfigDict(extra="forbid")

    numero_idoneidad: str | None = Field(default=None, min_length=1)
    numero_registro_medico: str | None = Field(default=None, min_length=1)
    cedula: str | None = Field(default=None, min_length=1)
    primer_nombre: str | None = Field(default=None, min_length=1)
    segundo_nombre: str | None = Field(default=None, min_length=1)
    apellido_paterno: str | None = Field(default=None, min_length=1)
    apellido_materno: str | None = Field(default=None, min_length=1)
    foto: str | None = Field(default=None, min_length=1)
    fecha_nacimiento: date | None = None
    telefono_residencial: str | None = Field(default=None, min_length=1)
    celular: str | None = Field(default=None, min_length=1)
    email_personal: EmailStr | None = None
    direccion: ActualizarDireccionSolicitud | None = None
    especialidades: CambiosRelacionesSolicitud | None = None
    subespecialidades: CambiosRelacionesSolicitud | None = None
    asociaciones: CambiosRelacionesSolicitud | None = None
    # DEF-014/015 (decisión 4): secciones que actualizar_medico.sql acepta. Cada elemento
    # actualiza una fila existente (con su id, de GET /medicos/{id}); en lugar_trabajo y
    # estudio_medico, un elemento sin id agrega una fila nueva (M2-REG-09 y M2-REG-10).
    lugar_trabajo: list[ActualizarLugarTrabajoSolicitud] | None = Field(
        default=None, min_length=1)
    estudio_medico: list[ActualizarEstudioMedicoSolicitud] | None = Field(
        default=None, min_length=1)
    certificacion: list[ActualizarCertificacionSolicitud] | None = Field(
        default=None, min_length=1)


class ActualizarPerfilMedicoSolicitud(BaseModel):
    """Campos no sensibles que el médico puede actualizar directamente.

    extra="forbid": cualquier campo no editable (cédula, registro médico, estudios,
    certificación...) responde 422.
    """

    model_config = ConfigDict(extra="forbid")

    fecha_nacimiento: date | None = None

    primer_nombre: str | None = Field(default=None, min_length=1)
    segundo_nombre: str | None = Field(default=None, min_length=1)
    apellido_paterno: str | None = Field(default=None, min_length=1)
    apellido_materno: str | None = Field(default=None, min_length=1)
    foto: str | None = Field(default=None, min_length=1)
    telefono_residencial: str | None = Field(default=None, min_length=1)
    celular: str | None = Field(default=None, min_length=1)
    email_personal: EmailStr | None = None
    direccion: ActualizarDireccionSolicitud | None = None


# Resultado de la actualización devuelto por la función de BD
class ActualizarMedicoRespuesta(BaseModel):
    """Resultado de la actualización devuelto por la función de BD."""

    actualizado: bool
