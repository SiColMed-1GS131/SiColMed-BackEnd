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
    tipo_estudio: str = Field(min_length=1)
    titulo: str = Field(min_length=1)
    institucion: str = Field(min_length=1)
    lugar: str = Field(min_length=1)
    fecha: date

class TrabajoRegistro(Estricto):
    empresa_institucion: str = Field(min_length=1)
    cargo: str = Field(min_length=1)
    telefono_trabajo: str = Field(min_length=1)
    email_laboral: EmailStr

class CertificacionRegistro(Estricto):
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

class RelacionesRegistro(RootModel[list[int]]):
    @model_validator(mode="after")
    def validar_ids(self):
        valores = self.root
        if any(valor <= 0 for valor in valores) or len(valores) != len(set(valores)):
            raise ValueError("Las relaciones deben contener IDs positivos sin duplicados")
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
    fecha_nacimiento: date
    telefono_residencial: str | None = None
    celular: str | None = None
    email_personal: EmailStr | None = None


class MedicoRegistro(Estricto):
    """Formato agrupado para registrar o cargar un médico completo."""

    medico: DatosMedicoRegistro
    direccion: DireccionRegistro
    lugar_trabajo: TrabajoRegistro | None = None
    direccion_trabajo: DireccionRegistro | None = None
    estudio_medico: EstudioRegistro | None = None
    certificacion: CertificacionRegistro | None = None
    especialidades: RelacionesRegistro = Field(default_factory=lambda: RelacionesRegistro([ ]))
    subespecialidades: RelacionesRegistro = Field(default_factory=lambda: RelacionesRegistro([ ]))
    asociaciones: RelacionesRegistro = Field(default_factory=lambda: RelacionesRegistro([ ]))

    @model_validator(mode="after")
    def validar_nacimiento_y_registro(self):
        if self.medico.fecha_nacimiento > date.today():
            raise ValueError("La fecha de nacimiento no puede ser futura")
        if self.lugar_trabajo is None and self.direccion_trabajo is not None:
            raise ValueError(
                "direccion_trabajo requiere un lugar_trabajo"
            )
        if self.lugar_trabajo is not None and self.direccion_trabajo is None:
            raise ValueError(
                "lugar_trabajo requiere una direccion_trabajo"
            )
        return self

class MedicoCreado(BaseModel):
    id_medico: int = Field(gt=0)

class PerfilMedico(RootModel[dict[str, Any]]):
    """Respuesta de la función obtener_perfil_medico; contrato de salida pendiente."""
