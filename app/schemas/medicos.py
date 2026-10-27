"""Contratos de registro y perfil completo de médicos."""
from datetime import date
from typing import Any
from pydantic import BaseModel, ConfigDict, EmailStr, Field, RootModel, model_validator

class Estricto(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

class DireccionRegistro(Estricto):
    apartado_postal: str | None = None
    calle: str | None = None
    edificio: str | None = None
    numero_direccion: str | None = None
    id_corregimiento: int = Field(gt=0)

class EstudioRegistro(Estricto):
    id_estudio: int | None = Field(default=None, gt=0)
    tipo_estudio: str = Field(min_length=1)
    titulo: str = Field(min_length=1)
    institucion: str = Field(min_length=1)
    lugar: str = Field(min_length=1)
    fecha: date

class TrabajoRegistro(Estricto):
    id_lugar_trabajo: int | None = Field(default=None, gt=0)
    empresa_institucion: str = Field(min_length=1)
    cargo: str = Field(min_length=1)
    telefono_trabajo: str = Field(min_length=1)
    email_laboral: EmailStr
    direccion: DireccionRegistro | None = None

class CertificacionRegistro(Estricto):
    id_certificacion: int | None = Field(default=None, gt=0)
    vigente: bool | None = None
    fecha_obtencion: date
    puntaje: int = Field(ge=0)
    fecha_expiracion: date
    certificado_pdf: str | None = None

    @model_validator(mode="after")
    def validar_fechas(self):
        if self.fecha_expiracion < self.fecha_obtencion:
            raise ValueError("La fecha de expiración debe ser posterior a la de obtención")
        return self

class CambiosRelaciones(Estricto):
    agregar: list[int] = Field(default_factory=list)
    quitar: list[int] = Field(default_factory=list)

    @model_validator(mode="after")
    def validar_relaciones(self):
        for nombre in ("agregar", "quitar"):
            valores = getattr(self, nombre)
            if any(x <= 0 for x in valores) or len(valores) != len(set(valores)):
                raise ValueError(f"{nombre} debe contener IDs positivos sin duplicados")
        if set(self.agregar) & set(self.quitar):
            raise ValueError("No se puede agregar y quitar el mismo ID")
        return self

class DatosMedicoRegistro(Estricto):
    numero_idoneidad: str = Field(min_length=1)
    numero_registro_medico: str = Field(min_length=1)
    cedula: str = Field(min_length=1)
    primer_nombre: str = Field(min_length=1)
    segundo_nombre: str | None = None
    apellido_paterno: str = Field(min_length=1)
    apellido_materno: str | None = None
    foto: str | None = None
    certificado_idoneidad_pdf: str | None = None
    fecha_nacimiento: date
    telefono_residencial: str | None = None
    celular: str | None = None
    email_personal: EmailStr | None = None


class MedicoRegistro(Estricto):
    """Formato agrupado para registrar o cargar un médico completo."""

    medico: DatosMedicoRegistro
    direccion: DireccionRegistro
    lugar_trabajo: list[TrabajoRegistro] = Field(default_factory=list)
    estudio_medico: list[EstudioRegistro] = Field(default_factory=list)
    especialidades: CambiosRelaciones = Field(default_factory=CambiosRelaciones)
    subespecialidades: CambiosRelaciones = Field(default_factory=CambiosRelaciones)
    asociaciones: CambiosRelaciones = Field(default_factory=CambiosRelaciones)
    certificaciones: list[CertificacionRegistro] = Field(default_factory=list)

    @model_validator(mode="after")
    def validar_nacimiento_y_registro(self):
        if self.medico.fecha_nacimiento > date.today():
            raise ValueError("La fecha de nacimiento no puede ser futura")
        for nombre in ("especialidades", "subespecialidades", "asociaciones"):
            if getattr(self, nombre).quitar:
                raise ValueError(f"{nombre}.quitar debe estar vacío al registrar un médico")
        return self

class MedicoCreado(BaseModel):
    id_medico: int = Field(gt=0)

class PerfilMedico(RootModel[dict[str, Any]]):
    """Respuesta de la función obtener_perfil_medico; contrato de salida pendiente."""
