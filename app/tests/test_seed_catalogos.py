"""Pruebas de los catálogos permanentes (archivos versionados; sin PostgreSQL)."""
from collections import Counter
from pathlib import Path

from app.scripts import seed_catalogos as sc

DOCS = Path(__file__).resolve().parents[2] / "docs" / "fuentes-division-politica-panama.md"

PROVINCIAS = {
    "01": "Bocas del Toro", "02": "Coclé", "03": "Colón", "04": "Chiriquí", "05": "Darién",
    "06": "Herrera", "07": "Los Santos", "08": "Panamá", "09": "Veraguas", "13": "Panamá Oeste",
}


def _dpa():
    return sc.leer_division_politica()


def test_cantidades_de_la_dpa_2025():
    provincias, distritos, corregimientos = _dpa()
    # 10 provincias + 3 comarcas de nivel provincial; 83 distritos (82 + Naso Tjër Di);
    # 699 corregimientos de la fuente menos 1 registro auxiliar
    assert (len(provincias), len(distritos), len(corregimientos)) == (13, 83, 698)


def test_las_diez_provincias_con_su_codigo_oficial():
    provincias = {p.codigo: p.nombre for p in _dpa()[0]}
    for codigo, nombre in PROVINCIAS.items():
        assert provincias[codigo] == nombre


def test_comarcas_segun_su_categoria():
    provincias, distritos, corregimientos = _dpa()
    provincias = {p.codigo: p.nombre for p in provincias}
    distritos = {d.codigo: d for d in distritos}
    corregimientos = {c.codigo: c for c in corregimientos}

    # Categoría provincial
    assert provincias["10"] == "Comarca Kuna Yala"
    assert provincias["11"] == "Comarca Emberá-Wounaán"
    assert provincias["12"] == "Comarca Ngäbe-Buglé"
    # Categoría de distrito, dentro de Bocas del Toro
    assert distritos["0105"].nombre == "Comarca Naso Tjër Di"
    assert distritos["0105"].codigo_superior == "01"
    # Categoría de corregimiento: Chepo (Panamá) y Pinogana (Darién)
    assert corregimientos["080507"].nombre == "Comarca Kuna de Madungandi"
    assert corregimientos["080507"].codigo_superior == "0805"
    assert corregimientos["050209"].nombre == "Comarca Kuna de Wargandi"
    assert corregimientos["050209"].codigo_superior == "0502"


def test_relaciones_y_codigos_coherentes():
    provincias, distritos, corregimientos = _dpa()
    codigos_provincia = {p.codigo for p in provincias}
    codigos_distrito = {d.codigo for d in distritos}
    assert all(len(p.codigo) == 2 and p.codigo.isdigit() for p in provincias)
    for d in distritos:
        assert len(d.codigo) == 4 and d.codigo.isdigit()
        assert d.codigo_superior in codigos_provincia and d.codigo.startswith(d.codigo_superior)
    for c in corregimientos:
        assert len(c.codigo) == 6 and c.codigo.isdigit()
        assert c.codigo_superior in codigos_distrito and c.codigo.startswith(c.codigo_superior)


def test_sin_duplicados_ni_espacios_sobrantes():
    for unidades in _dpa():
        assert not [c for c, n in Counter(u.codigo for u in unidades).items() if n > 1]
        assert all(u.nombre == " ".join(u.nombre.split()) for u in unidades)
    corregimientos = _dpa()[2]
    por_distrito = Counter((c.codigo_superior, sc.normalizar(c.nombre)) for c in corregimientos)
    assert not [k for k, n in por_distrito.items() if n > 1]


def test_registros_auxiliares_fuera_y_documentados():
    codigos = {c.codigo for c in _dpa()[2]}
    documento = DOCS.read_text(encoding="utf-8")
    for codigo, nombre in sc.CORREGIMIENTOS_AUXILIARES.items():
        assert codigo not in codigos
        assert codigo in documento and nombre in documento
    assert "Ley 188" in documento
    distritos = {d.codigo: d.nombre for d in _dpa()[1]}
    for codigo, nombre in sc.DISTRITOS_FICTICIOS_CARGADOS.items():
        assert distritos[codigo] == nombre
        assert codigo in documento


def test_cantidades_oficiales_de_anati_cuadran_con_lo_cargado():
    """82 distritos oficiales + 1 ficticio = 83; 699 corregimientos de la capa - 1 auxiliar = 698."""
    _, distritos, corregimientos = _dpa()
    assert len(distritos) - len(sc.DISTRITOS_FICTICIOS_CARGADOS) == 82
    assert len(corregimientos) + len(sc.CORREGIMIENTOS_AUXILIARES) == 699
    metadatos = (sc.DPA / "metadatos" / "Distrito.xml").read_text(encoding="utf-8")
    assert "existen 83 distritos" in metadatos and "1 es ficticio" in metadatos
    assert "699 corregimientos" in metadatos


def test_todo_distrito_con_corregimientos_salvo_naso():
    _, distritos, corregimientos = _dpa()
    con_corregimientos = {c.codigo_superior for c in corregimientos}
    assert {d.codigo for d in distritos} - con_corregimientos == {"0105"}


def test_especialidades_y_subespecialidades():
    especialidades = sc.leer_especialidades()
    assert len(especialidades) == 31 == len({sc.normalizar(e) for e in especialidades})
    normalizadas = {sc.normalizar(e) for e in especialidades}
    subespecialidades = sc.leer_subespecialidades()
    assert len(subespecialidades) == 45
    assert all(sc.normalizar(base) in normalizadas for _, base in subespecialidades)
    assert len(set(subespecialidades)) == len(subespecialidades)


def test_normalizar_ignora_tildes_mayusculas_y_espacios():
    assert sc.normalizar("  Panamá  Oeste ") == sc.normalizar("panama oeste")
    assert sc.normalizar("Ngäbe-Buglé") == "ngabe-bugle"


def test_roles_de_la_aplicacion():
    assert sc.ROLES == ("admin_cmp", "medico", "tesorero", "admin_asociacion")
