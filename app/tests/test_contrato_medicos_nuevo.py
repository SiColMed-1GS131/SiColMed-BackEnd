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
        "numero_idoneidad": "I123", "numero_registro_medico": "RM123", "cedula": "8-100-200",
        "primer_nombre": "Ana", "apellido_paterno": "Perez", "fecha_nacimiento": "1990-01-01",
        "direccion": {"id_corregimiento": 1},
        "especialidades": {"agregar": [1, 2], "quitar": []},
        "subespecialidades": {"agregar": [3], "quitar": []},
        "asociaciones": {"agregar": [1], "quitar": []},
        "estudios": [], "trabajos": [], "certificaciones": [], "otras_organizaciones": [],
    }


def test_post_acepta_objetos_agregar_quitar():
    m = MedicoRegistro.model_validate(datos_registro())
    assert m.especialidades.agregar == [1, 2]
    assert m.subespecialidades.agregar == [3]


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
