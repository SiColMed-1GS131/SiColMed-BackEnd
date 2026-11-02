"""Pruebas de contrato POST/PATCH sin modificar PostgreSQL.
Ejecutar desde la raiz del Backend: python -m pytest app/tests/test_contrato_medicos_nuevo.py -v
"""
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
        "direccion": {
            "apartado_postal": "0819",
            "calle": "Calle 50",
            "edificio": "Torre Medica",
            "numero_direccion": "12",
            "id_corregimiento": 1,
        },
        "especialidades": [1, 2],
        "subespecialidades": [3],
        "asociaciones": [1],
    }


def test_post_acepta_relaciones_como_listas():
    m = MedicoRegistro.model_validate(datos_registro())
    assert m.especialidades.root == [1, 2]
    assert m.subespecialidades.root == [3]


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
    datos["lugar_trabajo"] = {
            "empresa_institucion": "Hospital Central",
            "cargo": "Medica especialista",
            "telefono_trabajo": "300-5678",
            "email_laboral": "ana.gonzalez@hospital.com",
    }
    datos["direccion_trabajo"] = {
            "apartado_postal": "0819",
            "calle": "Calle 50",
            "edificio": "Hospital Central",
            "numero_direccion": "1",
            "id_corregimiento": 1,
    }
    datos["estudio_medico"] = {
            "tipo_estudio": "Licenciatura",
            "titulo": "Medicina General",
            "institucion": "Universidad Nacional",
            "lugar": "Panama",
            "fecha": "2015-12-15",
    }
    datos["certificacion"] = {
            "vigente": True,
            "fecha_obtencion": "2025-01-15",
            "puntaje": 95,
            "fecha_expiracion": "2028-01-15",
    }

    medico = MedicoRegistro.model_validate(datos)

    assert medico.medico.numero_idoneidad == "I123"
    assert medico.lugar_trabajo.empresa_institucion == "Hospital Central"
    assert medico.estudio_medico.titulo == "Medicina General"
    assert medico.certificacion.vigente is True


def test_post_rechaza_ids_de_relaciones_invalidos():
    datos = datos_registro()
    datos["asociaciones"] = [1, 1]
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


def test_post_envia_todo_en_un_jsonb():
    m = MedicoRegistro.model_validate(datos_registro())
    db = Mock()
    with patch(
        "app.repositories.medicos.llamar_escalar",
        return_value=13,
    ) as llamar:
        id_medico = registrar_medico(db, m)
    assert id_medico == 13
    llamar.assert_called_once()
    _, nombre_funcion, parametros = llamar.call_args.args
    assert nombre_funcion == "registrar_medico"
    assert list(parametros) == ["p_datos"]
    assert parametros["p_datos"].sql_type == "jsonb"
    assert parametros["p_datos"].value["medico"]["primer_nombre"] == "Ana"
    assert parametros["p_datos"].value["especialidades"] == [1, 2]


def test_post_propaga_error_de_la_funcion_jsonb():
    m = MedicoRegistro.model_validate(datos_registro())
    db = Mock()
    with patch(
        "app.repositories.medicos.llamar_escalar",
        side_effect=RuntimeError("fallo SQL simulado"),
    ):
        with pytest.raises(RuntimeError, match="fallo SQL simulado"):
            registrar_medico(db, m)
