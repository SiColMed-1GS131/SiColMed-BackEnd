from sqlalchemy.orm import Session
from app.repositories import medicos as repository
from app.schemas.medicos import MedicoPublico, MedicoRegistro

def registrar_medico(db: Session, datos: MedicoRegistro) -> int:
    return repository.registrar_medico(db, datos)

def obtener_perfil_medico(db: Session, id_medico: int) -> dict | None:
    return repository.obtener_perfil_medico(db, id_medico)


def perfil_publico(perfil: dict) -> MedicoPublico:
    """Reduce el perfil completo a la ficha pública del directorio."""
    datos = perfil.get("datos_personales") or {}
    nombre = " ".join(
        str(datos[campo]).strip()
        for campo in ("primer_nombre", "segundo_nombre", "apellido_paterno", "apellido_materno")
        if datos.get(campo)
    )
    certificaciones = perfil.get("certificaciones") or []
    lugares = perfil.get("lugares_trabajo") or []
    id_medico = datos.get("id_medico") or perfil.get("id_medico")
    return MedicoPublico(
        id_medico=id_medico,
        nombre_completo=nombre,
        numero_idoneidad=datos.get("numero_idoneidad"),
        especialidades=perfil.get("especialidades") or [],
        subespecialidades=perfil.get("subespecialidades") or [],
        asociaciones=perfil.get("asociaciones") or [],
        provincia=(perfil.get("direccion_residencial") or {}).get("provincia"),
        certificacion_vigente=any(c.get("vigente") for c in certificaciones),
        lugar_trabajo=lugares[0].get("empresa_institucion") if lugares else None,
        foto_url=f"/medicos/{id_medico}/foto" if datos.get("foto") else None,
    )
