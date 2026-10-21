from app.schemas.medicos_directorio import FiltroMedicos
from app.services.medicos_directorio import actualizar_medico, obtener_medicos
from app.errors import MedicoNoEncontrado, RespuestaBDInvalida


class RepositorioFalso:
    def __init__(self, resultado):
        self.resultado = resultado
        self.filtros_recibidos = None

    def filtrar_medicos(self, db, filtros):
        self.filtros_recibidos = filtros
        return self.resultado


def test_obtener_medicos_calcula_total_de_paginas():
    repositorio = RepositorioFalso(
        {
            "items": [
                {
                    "id_medico": 1,
                    "nombre_completo": "Ana Gómez",
                    "numero_idoneidad": "MED-001",
                    "especialidades": "Cardiología",
                    "asociaciones": None,
                    "certificacion_vigente": True,
                    "provincia": "Panamá",
                    "lugar_trabajo": "Hospital Nacional",
                }
            ],
            "total": 41,
        }
    )

    respuesta = obtener_medicos(
        None,
        FiltroMedicos(apellido="gomez", pagina=2, tamano_pagina=20),
        repositorio,
    )

    assert respuesta.total_paginas == 3
    assert respuesta.pagina == 2
    assert len(respuesta.medicos) == 1
    assert repositorio.filtros_recibidos.apellido == "gomez"


def test_obtener_medicos_con_resultado_vacio_calcula_cero_paginas():
    repositorio = RepositorioFalso({"items": [], "total": 0})

    respuesta = obtener_medicos(
        None,
        FiltroMedicos(),
        repositorio,
    )

    assert respuesta.medicos == []
    assert respuesta.total == 0
    assert respuesta.total_paginas == 0


def test_obtener_medicos_rechaza_respuesta_de_bd_invalida():
    repositorio = RepositorioFalso({"resultado": []})

    try:
        obtener_medicos(None, FiltroMedicos(), repositorio)
    except RespuestaBDInvalida as error:
        assert "items y total" in str(error)
    else:
        raise AssertionError("Se esperaba una respuesta inválida de BD.")


class RepositorioActualizacionFalso:
    def actualizar_medico(self, db, id_medico, id_administrador, datos):
        return False


def test_actualizar_medico_inexistente_lanza_error_de_no_encontrado():
    from app.schemas.medicos_directorio import ActualizarMedicoSolicitud

    try:
        actualizar_medico(
            None,
            99,
            1,
            ActualizarMedicoSolicitud(primer_nombre="Ana"),
            RepositorioActualizacionFalso(),
        )
    except MedicoNoEncontrado as error:
        assert "99" in str(error)
    else:
        raise AssertionError("Se esperaba un error de médico no encontrado.")
