"""Pruebas del seed QA que no necesitan PostgreSQL: protección de producción y escenarios."""
import subprocess
import sys
from pathlib import Path

import pytest

from app.scripts import seed, seed_catalogos, seed_qa

RAIZ = Path(__file__).resolve().parents[2]


class _BDProhibida:
    def __getattr__(self, nombre):
        raise AssertionError("seed_qa usó la BD en un ambiente no autorizado")


# Denegación por defecto: todo lo que no esté en AMBIENTES_QA se rechaza
RECHAZADOS = ["production", "PRODUCTION", " production ", "prod", "staging", "desarrollo", "", "   "]


def test_ambientes_autorizados():
    assert seed_qa.AMBIENTES_QA == {"development", "qa", "test"}


@pytest.mark.parametrize("valor", ["development", "qa", "test", " QA ", "Development"])
def test_ambientes_autorizados_se_permiten(monkeypatch, valor):
    monkeypatch.setenv("ENVIRONMENT", valor)
    seed_qa.verificar_ambiente()


@pytest.mark.parametrize("valor", RECHAZADOS)
def test_sembrar_se_niega_fuera_de_ambientes_autorizados(monkeypatch, valor):
    monkeypatch.setenv("ENVIRONMENT", valor)
    with pytest.raises(seed_qa.AmbienteNoPermitido):
        seed_qa.sembrar(_BDProhibida())


def test_sembrar_se_niega_sin_environment(monkeypatch):
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    with pytest.raises(seed_qa.AmbienteNoPermitido, match="no está definida"):
        seed_qa.sembrar(_BDProhibida())


@pytest.mark.parametrize("valor", [None, "production", "staging"])
def test_main_y_seed_devuelven_error(monkeypatch, valor):
    if valor is None:
        monkeypatch.delenv("ENVIRONMENT", raising=False)
    else:
        monkeypatch.setenv("ENVIRONMENT", valor)
    # seed.py comprueba antes de cargar nada: tampoco debe llegar a seed_catalogos
    monkeypatch.setattr(seed.seed_catalogos, "main", lambda: pytest.fail("seed.py cargó catálogos"))
    assert seed_qa.main() == 2
    assert seed.main() == 2


def _ejecutar(comando, ambiente):
    env = {"SYSTEMROOT": "", "PATH": ""}
    if ambiente is not None:
        env["ENVIRONMENT"] = ambiente
    return subprocess.run([sys.executable, *comando], cwd=RAIZ, capture_output=True, text=True, env=env)


@pytest.mark.parametrize("ambiente,mensaje", [
    ("production", "ENVIRONMENT=production"),
    (None, "no está definida"),
    ("staging", "no es un ambiente autorizado"),
])
@pytest.mark.parametrize("comando", [["-m", "app.scripts.seed_qa"], ["app/scripts/seed_qa.py"], ["-m", "app.scripts.seed"]])
def test_ejecutado_directamente_se_detiene(comando, ambiente, mensaje):
    resultado = _ejecutar(comando, ambiente)
    assert resultado.returncode == 2, resultado.stderr
    assert mensaje in resultado.stderr


def test_escenarios_de_medicos():
    escenarios = {m["escenario"] for m in seed_qa.MEDICOS}
    assert {"Certificación vigente", "Certificación vencida", "Sin certificación registrada"} <= escenarios
    assert seed_qa.VIGENTE["vigente"] and seed_qa.VIGENTE["fecha_expiracion"] > seed_qa.VIGENTE["fecha_obtencion"]
    assert not seed_qa.VENCIDA["vigente"]
    claves = [m["numero_idoneidad"] for m in seed_qa.MEDICOS]
    assert len(set(claves)) == len(claves)


def test_medicos_usan_catalogos_permanentes():
    _, _, corregimientos = seed_catalogos.leer_division_politica()
    corregimientos = {c.codigo: c for c in corregimientos}
    provincias = {corregimientos[m["corregimiento"]].codigo[:2] for m in seed_qa.MEDICOS}
    assert len(provincias) >= 3
    especialidades = {seed_catalogos.normalizar(e) for e in seed_catalogos.leer_especialidades()}
    subespecialidades = {seed_catalogos.normalizar(s) for s, _ in seed_catalogos.leer_subespecialidades()}
    for m in seed_qa.MEDICOS:
        assert seed_catalogos.normalizar(m["especialidad"]) in especialidades
        assert m["subespecialidad"] is None or seed_catalogos.normalizar(m["subespecialidad"]) in subespecialidades
    assert len({m["especialidad"] for m in seed_qa.MEDICOS}) >= 3


def test_cuentas_y_movimientos():
    con_movimientos = {c for mov in seed_qa.MOVIMIENTOS for c, _, _ in mov["detalle"]}
    assert con_movimientos <= set(seed_qa.CUENTAS)
    assert set(seed_qa.CUENTAS) - con_movimientos == {"QA Cuenta sin movimientos"}
    for mov in seed_qa.MOVIMIENTOS:
        # registrar_movimiento exige que cuadre
        debitos = sum(float(m) for _, m, t in mov["detalle"] if t == "DEBITO")
        creditos = sum(float(m) for _, m, t in mov["detalle"] if t == "CREDITO")
        assert debitos == creditos > 0


def test_solicitudes_en_los_tres_estados():
    decisiones = {s["decision"] for s in seed_qa.SOLICITUDES}
    assert decisiones == {None, "APROBADO", "RECHAZADO"}
    con_certificacion = {m["numero_idoneidad"] for m in seed_qa.MEDICOS if m["certificacion"]}
    assert all(s["medico"] in con_certificacion for s in seed_qa.SOLICITUDES)
