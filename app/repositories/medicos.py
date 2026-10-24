"""Registro médico transaccional. No se aceptan campos que la BD aún no puede guardar.
El procedimiento registrar_medico inserta el núcleo; el resto se persiste en tablas relacionadas.
"""
from datetime import date
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.repositories.base import Arg, llamar_escalar
from app.schemas.medicos import MedicoRegistro, DireccionRegistro

class ContratoBDPendiente(RuntimeError):
    pass

def _crear_direccion(db: Session, datos: DireccionRegistro) -> int:
    # La BD deriva provincia y distrito desde el corregimiento seleccionado.
    result = db.execute(text("""
        INSERT INTO direccion (apartado_postal, calle, edificio, numero_direccion,
                               id_provincia, id_distrito, id_corregimiento)
        SELECT :apartado_postal, :calle, :edificio, :numero_direccion,
               d.id_provincia, c.id_distrito, c.id_corregimiento
        FROM corregimiento c JOIN distrito d ON d.id_distrito = c.id_distrito
        WHERE c.id_corregimiento = :id_corregimiento
        RETURNING id_direccion
    """), datos.model_dump())
    value = result.scalar_one_or_none()
    if value is None:
        raise ValueError("El corregimiento indicado no existe")
    return value

def registrar_medico(db: Session, medico: MedicoRegistro) -> int:
    if medico.certificado_idoneidad_pdf or any(c.certificado_pdf for c in medico.certificaciones):
        raise ContratoBDPendiente("BD debe definir almacenamiento de certificados PDF antes de aceptarlos")
    if medico.otras_organizaciones:
        raise ContratoBDPendiente("BD debe definir almacenamiento de organizaciones no catalogadas")

    direccion = medico.direccion
    # Orden exacto de la firma disponible en app/funciones/registrar_medico.sql.
    params = {
        "p_numero_idoneidad": Arg(medico.numero_idoneidad, "text"),
        "p_numero_registro_medico": Arg(medico.numero_registro_medico, "text"),
        "p_cedula": Arg(medico.cedula, "text"),
        "p_primer_nombre": Arg(medico.primer_nombre, "text"),
        "p_apellido_paterno": Arg(medico.apellido_paterno, "text"),
        "p_fecha_nacimiento": Arg(medico.fecha_nacimiento, "date"),
        "p_segundo_nombre": Arg(medico.segundo_nombre, "text"),
        "p_apellido_materno": Arg(medico.apellido_materno, "text"),
        "p_telefono_residencial": Arg(medico.telefono_residencial, "text"),
        "p_celular": Arg(medico.celular, "text"),
        "p_email_personal": Arg(str(medico.email_personal) if medico.email_personal else None, "text"),
        "p_foto": Arg(medico.foto, "text"),
        "p_apartado_postal": Arg(direccion.apartado_postal, "text"),
        "p_calle": Arg(direccion.calle, "text"),
        "p_edificio": Arg(direccion.edificio, "text"),
        "p_numero_direccion": Arg(direccion.numero_direccion, "text"),
        "p_id_corregimiento": Arg(direccion.id_corregimiento, "integer"),
    }
    try:
        # Sin commit aquí: todas las inserciones relacionadas forman una sola transacción.
        id_medico = llamar_escalar(db, "registrar_medico", params)
        if not isinstance(id_medico, int) or id_medico <= 0:
            raise RuntimeError("registrar_medico no devolvió un id_medico válido")
        for estudio in medico.estudios:
            db.execute(text("""INSERT INTO estudio_medico
                (id_medico, tipo_estudio, titulo, institucion, lugar, fecha)
                VALUES (:id_medico, :tipo_estudio, :titulo, :institucion, :lugar, :fecha)"""),
                {"id_medico": id_medico, **estudio.model_dump()})
        for trabajo in medico.trabajos:
            id_direccion = _crear_direccion(db, trabajo.direccion)
            db.execute(text("""INSERT INTO lugar_trabajo
                (id_medico, empresa_institucion, cargo, telefono_trabajo, email_laboral, id_direccion)
                VALUES (:id_medico, :empresa_institucion, :cargo, :telefono_trabajo,
                        :email_laboral, :id_direccion)"""),
                {"id_medico": id_medico, "empresa_institucion": trabajo.empresa_institucion,
                 "cargo": trabajo.cargo, "telefono_trabajo": trabajo.telefono_trabajo,
                 "email_laboral": str(trabajo.email_laboral), "id_direccion": id_direccion})
        for campo, tabla, columna in (
            (medico.especialidades.agregar, "medico_especialidad", "id_especialidad"),
            (medico.subespecialidades.agregar, "medico_subespecialidad", "id_subespecialidad"),
            (medico.asociaciones.agregar, "medico_asociacion", "id_asociacion"),
        ):
            # Nombres SQL son constantes internas, no valores provistos por el cliente.
            for catalogo_id in campo:
                db.execute(text(f"INSERT INTO {tabla} (id_medico, {columna}) VALUES (:id_medico, :id_catalogo)"),
                           {"id_medico": id_medico, "id_catalogo": catalogo_id})
        for cert in medico.certificaciones:
            db.execute(text("""INSERT INTO certificacion
                (id_medico, vigente, fecha_obtencion, puntaje, fecha_expiracion)
                VALUES (:id_medico, :vigente, :fecha_obtencion, :puntaje, :fecha_expiracion)"""),
                {"id_medico": id_medico, "vigente": cert.fecha_expiracion >= date.today(),
                 "fecha_obtencion": cert.fecha_obtencion, "puntaje": cert.puntaje,
                 "fecha_expiracion": cert.fecha_expiracion})
        db.commit()
        return id_medico
    except Exception:
        db.rollback()
        raise

def obtener_perfil_medico(db: Session, id_medico: int) -> dict | None:
    return llamar_escalar(db, "obtener_perfil_medico", {"id_medico": Arg(id_medico, "integer")})
