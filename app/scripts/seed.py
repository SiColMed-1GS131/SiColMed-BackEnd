"""Compatibilidad: ejecuta seed_catalogos y después seed_qa.

Uso:
    docker compose exec api python -m app.scripts.seed

Antes este script mezclaba catálogos y datos de demostración. Ahora son dos procesos:
- app.scripts.seed_catalogos: catálogos permanentes, en todos los ambientes.
- app.scripts.seed_qa: datos de prueba, solo con ENVIRONMENT en seed_qa.AMBIENTES_QA.
Este comando se conserva para quien ya lo usaba. Como incluye datos QA, comprueba el
ambiente ANTES de cargar nada: si no está autorizado (ENVIRONMENT sin definir, desconocido
o production) no ejecuta ninguno de los dos pasos. Fuera de desarrollo y QA se usa
directamente seed_catalogos.
"""

from __future__ import annotations

import sys

from app.scripts import seed_catalogos, seed_qa


def main() -> int:
    try:
        seed_qa.verificar_ambiente()
    except seed_qa.AmbienteNoPermitido as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return seed_catalogos.main() or seed_qa.main()


if __name__ == "__main__":
    raise SystemExit(main())
