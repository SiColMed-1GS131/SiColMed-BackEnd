# Fuente de especialidades y subespecialidades médicas

Explica de dónde salen las especialidades y subespecialidades que carga
`app/scripts/seed_catalogos.py` (archivos `app/scripts/datos/especialidades_cts.csv` y
`app/scripts/datos/subespecialidades_cts.csv`).

## Fuente

Universidad de Panamá, Consejo General Universitario, reunión N°1-24 de 6 de marzo de 2024:
*Reglamento de Equivalencias Médicas, Maestrías y Doctorados en Ciencias Clínicas de la
Facultad de Medicina*.

- Documento: <https://secretariageneral.up.ac.pa/sites/secretariageneral/files/2024-03/CGU_N%C2%B01-24.pdf>
- Consultado el 3 de noviembre de 2026.
- **Artículo 3**: «Las especialidades médicas que, a la fecha, ha reconocido el Consejo
  Técnico de Salud son». Hay 31, y para cada una se da la resolución del MINSA y la Gaceta Oficial.
- **Artículo 4**: «Las subespecialidades médicas que tienen una especialidad de base o
  formación previa de una especialidad y que, a la fecha, ha reconocido el Consejo Técnico
  de Salud son». Hay 61, con su «especialidad básica».
- **Base legal que cita el reglamento** (artículo 1):
  - el Decreto Ejecutivo N°418 de 4 de diciembre de 2018 (Gaceta Oficial N°28669-A);
  - el Decreto Ejecutivo N°180 de 27 de mayo de 2019, que lo modifica;
  - la Resolución N°03 de 28 de febrero de 2018 del Consejo Técnico de Salud (Gaceta
    Oficial N°28490).

No se encontró una lista publicada directamente por el Consejo Técnico de Salud. Este
reglamento es la recopilación institucional más reciente que se encontró. Cada entrada
remite a su resolución del MINSA, de modo que se puede contrastar.

## Qué se cargó

- **Especialidades:** las 31 del artículo 3, con el nombre tal como lo escribe el documento.
  - En `especialidades_cts.csv` la resolución y la Gaceta solo están en las filas 1 a 10.
  - Desde la fila 11 la tabla del PDF está desalineada al extraer el texto: no se puede
    saber con certeza qué resolución corresponde a cada especialidad. Se dejaron vacías en
    lugar de adivinarlas. Esas columnas no se cargan en la BD; solo sirven de referencia.
- **Subespecialidades:** 45 de las 61.
  - La tabla `subespecialidad` tiene **una sola** especialidad (`id_especialidad`).
  - Se cargan solo las que el documento asocia a **una** especialidad del artículo 3.
  - La columna `especialidad_catalogo` indica cuál. Por ejemplo, «Ginecología obstetricia»
    del artículo 4 corresponde a «Ginecología y obstetricia» del artículo 3.

### Subespecialidades que quedaron fuera (16): diagnóstico

La columna «Especialidad básica» es la del artículo 4, tal cual. La columna «Relación en el
catálogo» indica con qué fila ya cargada corresponde cada base:

- **(E):** especialidad del artículo 3.
- **(S):** subespecialidad ya cargada.

| N.° | Subespecialidad | Especialidad básica | Relación en el catálogo | Tipo |
|---|---|---|---|---|
| 1 | Alergología e inmunología clínica | Medicina interna o Pediatría | Medicina interna (E), Pediatría (E) | Varias especialidades |
| 2 | Algiología | Anestesiología, Ortopedia, Medicina física y rehabilitación, Neurocirugía | Anestesiología y reanimación (E), Ortopedia y traumatología (E), Medicina física y rehabilitación (E), Neurocirugía (E) | Varias especialidades |
| 14 | Dermatología pediátrica | Pediatría, Dermatología | Pediatría (E), Dermatología (E) | Varias especialidades |
| 21 | Genética médica y genómica | Medicina interna, Medicina familiar Pediatría | Medicina interna (E), Medicina familiar (E), Pediatría (E). Falta una coma en el documento | Varias especialidades |
| 22 | Geriatría y gerontología | Medicina interna, Medicina familiar | Medicina interna (E), Medicina familiar (E) | Varias especialidades. También es la especialidad 9 del artículo 3 |
| 33 | Medicina crítica | Medicina interna, Anestesiología, Cirugía general, Urgencias médicas quirúrgicas | Medicina interna (E), Anestesiología y reanimación (E), Cirugía general (E), Urgencias médico-quirúrgicas (E) | Varias especialidades |
| 4 | Cardiología intervencionista | Cardiología | Cardiología (S) | Depende de una subespecialidad |
| 5 | Cardiología nuclear | Cardiología | Cardiología (S) | Depende de una subespecialidad |
| 15 | Ecocardiografía | Cardiología | Cardiología (S) | Depende de una subespecialidad |
| 16 | Electrofisiología | Cardiología | Cardiología (S) | Depende de una subespecialidad |
| 29 | Hemodinámica | Cardiología | Cardiología (S) | Depende de una subespecialidad |
| 56 | Rehabilitación cardiaca y ergometría | Cardiología | Cardiología (S) | Depende de una subespecialidad |
| 30 | Hemodinámica en cardiología pediátrica | Cardiología pediátrica | Cardiología pediátrica, que es la n.° 6, también pendiente | Depende de una subespecialidad pendiente (dos niveles) |
| 6 | Cardiología pediátrica | Pediatría, Cardiología | Pediatría (E) y Cardiología (S) | Mixta: especialidad y subespecialidad |
| 10 | Cirugía pediátrica | Pediatría, Cardiología | Pediatría (E) y Cardiología (S) | Mixta. También es la especialidad 5 del artículo 3 |
| 7 | Cirugía cardiovascular y endovascular | Endocrinología | Endocrinología es una subespecialidad (n.° 17, base Medicina interna) | Inconsistente: ninguna base razonable, y también es la especialidad 3 del artículo 3. Hay que verificarla en su resolución (N°05 de 26/julio/2021) |

**Resumen:**

| Tipo | Cantidad |
|---|---|
| Varias especialidades de origen | 6 (1, 2, 14, 21, 22, 33) |
| Dependen de otra subespecialidad | 7 (4, 5, 15, 16, 29, 30, 56) |
| Mixtas (especialidad y subespecialidad) | 2 (6, 10) |
| Inconsistente en el documento | 1 (7) |

**Nombres que figuran en los dos artículos.** Hematología, Neumología, Neurología y Cirugía
Torácica aparecen como especialidad (artículo 3) y como subespecialidad (artículo 4). Las
cuatro ya están cargadas en las dos tablas. Geriatría y gerontología, Cirugía pediátrica y
Cirugía cardiovascular y endovascular también están en ambos artículos; por ahora solo
existen como especialidad. Parece que el Consejo Técnico de Salud las reconoce por las dos
vías de formación. Base de Datos debe confirmar si deben existir en ambas tablas.

**Qué permite el modelo actual.** `subespecialidad.id_especialidad` es una sola FK NOT NULL.
Además, `registrar_medico.sql` exige que cada subespecialidad del médico pertenezca a una de
sus especialidades: `s.id_especialidad = ANY(v_ids_especialidad)`. Con eso no se puede
representar ninguno de los 16 casos sin inventar una base única.

**Cambio mínimo propuesto (sin implementar, requiere aprobación de Base de Datos):**

1. **Tabla nueva `subespecialidad_requisito`** con estas columnas:
   - `id_subespecialidad_requisito` (PK)
   - `id_subespecialidad` (FK NOT NULL)
   - `id_especialidad` (FK, opcional)
   - `id_subespecialidad_base` (FK a `subespecialidad`, opcional)
   - un CHECK para que haya exactamente una de las dos bases y un UNIQUE

   Cada fila es una base posible, con sentido de «cualquiera de» como en el artículo 4. Cubre
   los 4 tipos y no duplica modelos.
2. **`subespecialidad.id_especialidad` pasa a ser opcional**, para las subespecialidades cuya
   base es otra subespecialidad. No se renombra ni se borra. Las 45 cargadas conservan su
   valor y se copian como requisito.
3. **Funciones de BD a ajustar** (todas son del equipo de Base de Datos):
   - `registrar_medico.sql`, la validación de subespecialidades;
   - `actualizar_medico.sql`;
   - `listar_subespecialidades.sql`, con el filtro por especialidad;
   - `obtener_perfil_medico.sql`, que devuelve `id_especialidad`.
4. **Contrato de la API:** `SubespecialidadItem.id_especialidad` pasaría a admitir `null`, y
   habría que agregar la lista de requisitos. Afecta al frontend (`CatalogosRepository` y el
   formulario de registro).

No se implementó porque cambia funciones y contratos que pertenecen a Base de Datos y a otros
grupos. La tarea pide presentar primero el diagnóstico. Con la aprobación se implementa con
una migración `PGFunction` (alembic_utils) y se cargan las 15 que tienen una base
verificable. La n.° 7 queda pendiente de su resolución.

### Defecto conocido: renombrar una especialidad la duplica

Especialidades y subespecialidades no tienen código oficial, así que `seed_catalogos` las
busca por nombre. Si alguien cambia el nombre de una especialidad cargada, la siguiente
ejecución no la reconoce: crea de nuevo la especialidad con el nombre original, duplica sus
subespecialidades, y `seed_qa` vincula a la copia los médicos de prueba que la usan.

Lo demuestra la prueba `test_especialidad_renombrada_no_se_duplica` (marcada `xfail`, en
`app/tests/test_seeds_postgres.py`). Para corregirlo hace falta una clave estable, que
también requiere aprobación de Base de Datos:

- **Opción A:** una columna `referencia` con el número de orden del documento fuente (por
  ejemplo «CTS-A3-25»). No es un código oficial y se documentaría como referencia interna.
- **Opción B:** que el seed no vuelva a crear una especialidad cuando la tabla ya tiene filas
  de la fuente. Esto impediría agregar especialidades nuevas en el futuro.

Mientras tanto, **no renombres especialidades en la BD**. Si un nombre debe cambiar, cámbialo
en `especialidades_cts.csv` con la decisión documentada.

### Correcciones de texto

- «Gastroenterologíay endoscopia digestiva» → «Gastroenterología y endoscopia digestiva»:
  el PDF no tiene el espacio.
- «Cirugía colorrectal Coloproctología» se conserva tal cual: en el documento ocupa dos
  líneas.

## Filas que ya existían

La BD de desarrollo tenía «Medicina General», creada por el seed antiguo. No figura en el
artículo 3. No se borró porque la usan médicos existentes, pero el seed nuevo ya no la
crea. Base de Datos debe decidir si se conserva.

## Asociaciones médicas

No se cargan: no se encontró una lista oficial verificable. La tabla `asociacion` queda como
estaba (vacía en una BD nueva).

**Qué se buscó** (3 de noviembre de 2026):

- **Consejo Técnico de Salud y MINSA (normatividad):** no hay una resolución que enumere las
  asociaciones o sociedades médicas reconocidas. El CTS se integra con representantes de
  asociaciones profesionales de carácter nacional, nombrados por decreto ejecutivo. Por
  ejemplo, el Decreto Ejecutivo N°14 de 1 de marzo de 2023 designa al representante de la
  Asociación Nacional de Enfermeras. Esos decretos identifican asociaciones una por una,
  según la representación en el CTS. No son un registro de asociaciones médicas.
- **Prensa:** una nota de Telemetro (junio de 2026) menciona a la Asociación de Médicos de
  Panamá y un proceso de certificación de «50 especialidades». Es una nota periodística, no
  una fuente oficial.

**Qué falta definir.** Ni el modelo ni el código explican qué es una «asociación» en SiColMed:
`asociacion` solo tiene `nombre`, y el rol `admin_asociacion` no está vinculado a ninguna
asociación. Antes de buscar una lista, el equipo debe definir:

- si son sociedades científicas de especialidad;
- si son capítulos o asociaciones del Colegio Médico;
- si son organizaciones que administran cuentas del módulo contable.

Según la respuesta, la fuente sería el propio Colegio, los decretos del CTS o el Registro
Público. Mientras tanto no se carga ninguna, para no presentar datos como oficiales sin
respaldo.
