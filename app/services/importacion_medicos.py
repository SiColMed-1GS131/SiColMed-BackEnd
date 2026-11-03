"""Carga masiva de médicos por CSV (requerimiento 9, POST /medicos/importar).

Formato: UTF-8 (con o sin BOM), separador coma, una cabecera con COLUMNAS (en
cualquier orden). Cada fila se valida con MedicoRegistro y se registra con la
función registrar_medico, igual que el formulario. Una fila con error no detiene
la carga: se informa con su número de línea. Toda carga, aunque el archivo se
rechace, deja una fila en auditoria (registrar_carga_medicos).

Formato completo y ejemplo: docs/carga-medicos-csv.md y
docs/ejemplos/carga_medicos_ejemplo.csv.
"""

from __future__ import annotations

import csv
import io
import unicodedata
from datetime import date
from typing import Any

from fastapi import UploadFile
from pydantic import ValidationError
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from app.errors import _obtener_mensaje_bd
from app.repositories import catalogos
from app.repositories import medicos as repository
from app.schemas.medicos import ErrorImportacion, MedicoRegistro, ResultadoImportacion

TAMANO_MAXIMO = 2 * 1024 * 1024
MAXIMO_FILAS = 500
SEPARADOR_LISTAS = ";"   # dentro de especialidades, subespecialidades y asociaciones

COLUMNAS = (
    # Datos personales
    "cedula", "primer_nombre", "segundo_nombre", "primer_apellido", "segundo_apellido",
    "fecha_nacimiento", "telefono", "celular", "email", "apartado_postal", "idoneidad",
    "registro_medico",
    # Dirección residencial (corregimiento = código oficial DPA, ej. 080807)
    "calle", "edificio", "numero", "corregimiento",
    # Lugar de trabajo y su dirección
    "empresa_institucion", "cargo", "telefono_trabajo", "email_laboral",
    "trabajo_apartado_postal", "trabajo_calle", "trabajo_edificio", "trabajo_numero",
    "trabajo_corregimiento",
    # Estudio básico
    "titulo", "institucion", "lugar_estudio", "fecha_titulo",
    # Certificación
    "cert_fecha_obtencion", "cert_fecha_expiracion", "cert_puntaje",
    # Relaciones: nombres del catálogo separados por ";"
    "especialidades", "subespecialidades", "asociaciones",
)


class ImportacionInvalida(ValueError):
    """El archivo completo no se puede procesar (formato, tamaño, cabecera)."""

    def __init__(self, mensaje: str, status_code: int = 422):
        super().__init__(mensaje)
        self.status_code = status_code


def _normalizar(nombre: str) -> str:
    sin_tildes = "".join(c for c in unicodedata.normalize("NFD", nombre) if unicodedata.category(c) != "Mn")
    return " ".join(sin_tildes.casefold().split())


class _Catalogos:
    """Nombres y códigos del CSV -> IDs de la BD, cargados una vez por archivo."""

    def __init__(self, db: Session):
        self.corregimientos = catalogos.ids_corregimiento_por_codigo(db)
        self.relaciones = {
            "especialidades": {_normalizar(e.nombre): e.id_especialidad for e in catalogos.especialidades(db)},
            "subespecialidades": {_normalizar(s.nombre): s.id_subespecialidad for s in catalogos.subespecialidades(db)},
            "asociaciones": {_normalizar(a.nombre): a.id_asociacion for a in catalogos.asociaciones(db)},
        }

    def corregimiento(self, codigo: str | None, columna: str) -> int | None:
        if codigo is None:
            return None
        if codigo not in self.corregimientos:
            raise ValueError(f"{columna}: el corregimiento con código {codigo} no existe")
        return self.corregimientos[codigo]

    def ids(self, valor: str | None, columna: str) -> list[int]:
        if valor is None:
            return []
        ids = []
        for nombre in (n.strip() for n in valor.split(SEPARADOR_LISTAS)):
            if not nombre:
                continue
            id_catalogo = self.relaciones[columna].get(_normalizar(nombre))
            if id_catalogo is None:
                raise ValueError(f"{columna}: «{nombre}» no está en el catálogo")
            ids.append(id_catalogo)
        return ids


def _bloque(datos: dict[str, Any]) -> dict[str, Any] | None:
    # Sección opcional: None si todas sus columnas vienen vacías
    return datos if any(v is not None for v in datos.values()) else None


def _fila_a_registro(fila: dict[str, str | None], cat: _Catalogos) -> MedicoRegistro:
    v = {columna: ((fila.get(columna) or "").strip() or None) for columna in COLUMNAS}
    lugar_trabajo = _bloque({
        "empresa_institucion": v["empresa_institucion"], "cargo": v["cargo"],
        "telefono_trabajo": v["telefono_trabajo"], "email_laboral": v["email_laboral"],
    })
    direccion_trabajo = _bloque({
        "apartado_postal": v["trabajo_apartado_postal"], "calle": v["trabajo_calle"],
        "edificio": v["trabajo_edificio"], "numero_direccion": v["trabajo_numero"],
        "id_corregimiento": cat.corregimiento(v["trabajo_corregimiento"], "trabajo_corregimiento"),
    })
    estudio = _bloque({
        "titulo": v["titulo"], "institucion": v["institucion"],
        "lugar": v["lugar_estudio"], "fecha": v["fecha_titulo"],
    })
    certificacion = _bloque({
        "fecha_obtencion": v["cert_fecha_obtencion"], "fecha_expiracion": v["cert_fecha_expiracion"],
        "puntaje": v["cert_puntaje"],
    })
    if certificacion:
        # registrar_medico exige "vigente": se deduce con la misma regla que usa
        # obtener_perfil_medico (fecha_expiracion >= hoy). Una fecha mal escrita la
        # rechaza Pydantic después.
        try:
            certificacion["vigente"] = date.fromisoformat(v["cert_fecha_expiracion"] or "") >= date.today()
        except ValueError:
            pass
    return MedicoRegistro.model_validate({
        "medico": {
            "numero_idoneidad": v["idoneidad"], "numero_registro_medico": v["registro_medico"],
            "cedula": v["cedula"], "primer_nombre": v["primer_nombre"],
            "segundo_nombre": v["segundo_nombre"], "apellido_paterno": v["primer_apellido"],
            "apellido_materno": v["segundo_apellido"], "fecha_nacimiento": v["fecha_nacimiento"],
            "telefono_residencial": v["telefono"], "celular": v["celular"], "email_personal": v["email"],
        },
        "direccion": {
            "apartado_postal": v["apartado_postal"], "calle": v["calle"], "edificio": v["edificio"],
            "numero_direccion": v["numero"],
            "id_corregimiento": cat.corregimiento(v["corregimiento"], "corregimiento"),
        },
        "lugar_trabajo": lugar_trabajo,
        "direccion_trabajo": direccion_trabajo,
        "estudio_medico": {"tipo_estudio": "Título básico", **estudio} if estudio else None,
        "certificacion": certificacion,
        "especialidades": cat.ids(v["especialidades"], "especialidades"),
        "subespecialidades": cat.ids(v["subespecialidades"], "subespecialidades"),
        "asociaciones": cat.ids(v["asociaciones"], "asociaciones"),
    })


def _mensaje_validacion(error: ValidationError) -> str:
    partes = []
    for detalle in error.errors():
        ruta = ".".join(str(p) for p in detalle["loc"] if not isinstance(p, int))
        partes.append(f"{ruta}: {detalle['msg']}" if ruta else detalle["msg"])
    return "; ".join(partes)


def _leer_filas(contenido: bytes) -> list[dict[str, str | None]]:
    try:
        texto = contenido.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise ImportacionInvalida("El archivo no está en UTF-8.", 415) from error
    lector = csv.DictReader(io.StringIO(texto, newline=""), delimiter=",")
    cabecera = [c.strip() for c in (lector.fieldnames or [])]
    if not cabecera:
        raise ImportacionInvalida("El archivo está vacío.")
    faltan = [c for c in COLUMNAS if c not in cabecera]
    if faltan:
        raise ImportacionInvalida(f"Faltan columnas en la cabecera: {', '.join(faltan)}.")
    lector.fieldnames = cabecera
    filas = [f for f in lector if any((valor or "").strip() for valor in f.values() if isinstance(valor, str))]
    if not filas:
        raise ImportacionInvalida("El archivo no tiene filas de datos.")
    if len(filas) > MAXIMO_FILAS:
        raise ImportacionInvalida(f"El archivo tiene {len(filas)} filas; el máximo es {MAXIMO_FILAS}.")
    return filas


def importar(db: Session, archivo: UploadFile, id_administrador: int) -> ResultadoImportacion:
    nombre = (archivo.filename or "sin_nombre.csv").strip()
    try:
        if not nombre.lower().endswith(".csv"):
            raise ImportacionInvalida("El archivo debe tener extensión .csv.", 415)
        contenido = archivo.file.read(TAMANO_MAXIMO + 1)
        if len(contenido) > TAMANO_MAXIMO:
            raise ImportacionInvalida("El archivo supera el máximo de 2 MB.", 413)
        filas = _leer_filas(contenido)
    except ImportacionInvalida as error:
        # También se audita la carga rechazada
        repository.registrar_carga(db, id_administrador, nombre, 0, 0, [{"fila": 0, "error": str(error)}])
        raise

    cat = _Catalogos(db)
    errores: list[ErrorImportacion] = []
    registrados = 0
    for numero, fila in enumerate(filas, start=2):   # la línea 1 es la cabecera
        try:
            repository.registrar_medico(db, _fila_a_registro(fila, cat))
            registrados += 1
        except ValidationError as error:
            errores.append(ErrorImportacion(fila=numero, error=_mensaje_validacion(error)))
        except ValueError as error:
            errores.append(ErrorImportacion(fila=numero, error=str(error)))
        except DBAPIError as error:
            # llamar_escalar ya deshizo la fila; las anteriores quedaron confirmadas
            errores.append(ErrorImportacion(fila=numero, error=_obtener_mensaje_bd(error)))

    id_auditoria = repository.registrar_carga(
        db, id_administrador, nombre, len(filas), registrados, [e.model_dump() for e in errores]
    )
    return ResultadoImportacion(
        archivo=nombre, procesados=len(filas), registrados=registrados,
        rechazados=len(filas) - registrados, errores=errores, id_auditoria=id_auditoria,
    )
