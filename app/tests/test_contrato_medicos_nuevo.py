"""Pruebas de contrato POST/PATCH sin modificar PostgreSQL.
Ejecutar desde la raiz del Backend: python -m pytest app/tests/test_contrato_medicos_nuevo.py -v
"""
from datetime import date
from unittest.mock import Mock, patch

import pytest
from pydantic import ValidationError

from app.schemas.medicos import MedicoRegistro
from app.schemas.medicos_directorio import ActualizarMedicoSolicitud
from app.services.medicos_directorio import actualizar_medico
from app.repositories.medicos import registrar_medico


def datos_registro():
    return {
        "medico": {
            "numero_idoneidad": "I123", "numero_registro_medico": "RM123",
            "cedula": "8-100-200", "primer_nombre": "Ana",
            "apellido_paterno": "Perez", "fecha_nacimiento": "1990-01-01",
        },
        "direccion": {"id_corregimiento": 1},
        "especialidades": {"agregar": [1, 2], "quitar": []},
        "subespecialidades": {"agregar": [3], "quitar": []},
        "asociaciones": {"agregar": [1], "quitar": []},
        "estudio_medico": [], "lugar_trabajo": [], "certificaciones": [],
    }


def test_post_acepta_objetos_agregar_quitar():
    m = MedicoRegistro.model_validate(datos_registro())
    assert m.especialidades.agregar == [1, 2]
    assert m.subespecialidades.agregar == [3]


def test_post_acepta_formato_completo_agrupado():
    datos = datos_registro()
    datos["medico"].update(
        {
            "segundo_nombre": "Maria",
            "apellido_materno": "Rodriguez",
            "foto": "https://ejemplo.com/fotos/ana-gonzalez.jpg",
            "telefono_residencial": "300-1234",
            "celular": "6000-1234",
            "email_personal": "ana.gonzalez@ejemplo.com",
        }
    )
    datos["lugar_trabajo"] = [
        {
            "id_lugar_trabajo": 1,
            "empresa_institucion": "Hospital Central",
            "cargo": "Medica especialista",
            "telefono_trabajo": "300-5678",
            "email_laboral": "ana.gonzalez@hospital.com",
        }
    ]
    datos["estudio_medico"] = [
        {
            "id_estudio": 1,
            "tipo_estudio": "Licenciatura",
            "titulo": "Medicina General",
            "institucion": "Universidad Nacional",
            "lugar": "Panama",
            "fecha": "2015-12-15",
        }
    ]
    datos["certificaciones"] = [
        {
            "id_certificacion": 1,
            "vigente": True,
            "fecha_obtencion": "2025-01-15",
            "puntaje": 95,
            "fecha_expiracion": "2028-01-15",
        }
    ]

    medico = MedicoRegistro.model_validate(datos)

    assert medico.medico.numero_idoneidad == "I123"
    assert medico.lugar_trabajo[0].id_lugar_trabajo == 1
    assert medico.estudio_medico[0].id_estudio == 1
    assert medico.certificaciones[0].vigente is True


def test_post_rechaza_quitar_en_alta():
    datos = datos_registro()
    datos["asociaciones"]["quitar"] = [1]
    with pytest.raises(ValidationError):
        MedicoRegistro.model_validate(datos)


def test_rechaza_id_duplicado_y_conflicto():
    datos = datos_registro()
    datos["especialidades"]["agregar"] = [1, 1]
    with pytest.raises(ValidationError):
        MedicoRegistro.model_validate(datos)
    datos["especialidades"] = {"agregar": [1], "quitar": [1]}
    with pytest.raises(ValidationError):
        MedicoRegistro.model_validate(datos)


def test_patch_parcial_con_relaciones_y_contrato_bd():
    datos = ActualizarMedicoSolicitud.model_validate({
        "primer_nombre": "Ana Maria",
        "especialidades": {"agregar": [1, 2], "quitar": [4]},
        "asociaciones": {"agregar": [], "quitar": [3]},
    })
    repo = Mock()
    repo.actualizar_medico.return_value = True
    result = actualizar_medico(Mock(), 5, 8, datos, repo)
    assert result.actualizado is True
    payload = repo.actualizar_medico.call_args.args[3]
    assert payload["medico"] == {"primer_nombre": "Ana Maria"}
    assert payload["especialidades"] == {"agregar": [1, 2], "quitar": [4]}
    assert payload["asociaciones"] == {"agregar": [], "quitar": [3]}
    assert "subespecialidades" not in payload


def test_post_persiste_relaciones_en_transaccion_simulada():
    m = MedicoRegistro.model_validate(datos_registro())
    db = Mock()
    with patch("app.repositories.medicos.llamar_escalar", return_value=13):
        id_medico = registrar_medico(db, m)
    assert id_medico == 13
    assert db.execute.call_count == 4
    assert db.commit.call_count == 1
    db.rollback.assert_not_called()


def test_post_revierte_si_falla_insercion_relacionada():
    m = MedicoRegistro.model_validate(datos_registro())
    db = Mock()
    db.execute.side_effect = RuntimeError("fallo SQL simulado")
    with patch("app.repositories.medicos.llamar_escalar", return_value=13):
        with pytest.raises(RuntimeError, match="fallo SQL simulado"):
            registrar_medico(db, m)
    db.rollback.assert_called_once()
    db.commit.assert_not_called()
