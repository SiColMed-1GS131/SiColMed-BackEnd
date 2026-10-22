# SiColMed Backend

Backend de la API de SiColMed, construido con FastAPI, SQLAlchemy y
PostgreSQL. El equipo de Backend conecta los procedimientos almacenados de la
base de datos con endpoints HTTP documentados en Swagger.

## Arquitectura obligatoria

Cada funcionalidad debe implementarse verticalmente en las siguientes capas:

```text
Router → Schema → Service → Repository → Base de datos
   ↓         ↓         ↓           ↓
 HTTP     Validación   Reglas     Función SQL
```

Cada endpoint debe incluir:

1. **Router:** método HTTP, ruta, dependencias y códigos de respuesta.
2. **Schema:** modelos Pydantic de entrada, salida y parámetros.
3. **Service:** reglas de negocio y validaciones que no correspondan al router
   ni a PostgreSQL.
4. **Repository:** llamada al procedimiento almacenado o consulta acordada
   con el equipo de Base de datos.
5. **Pruebas:** pruebas unitarias preparadas por P6 con repositorios y
   autenticación falsos.
6. **Swagger:** endpoint visible en `/docs`, con parámetros y ejemplos claros.

No se debe colocar lógica de negocio ni SQL directamente dentro del router.

## Estructura de carpetas

```text
app/
├── errors.py
├── main.py
├── routers/
│   ├── medicos.py
│   ├── catalogos_geograficos.py
│   ├── solicitudes_cambio.py
│   ├── catalogos_profesionales.py
│   ├── cuentas.py
│   ├── movimientos.py
│   └── reportes.py
├── schemas/
│   ├── medicos.py
│   ├── catalogos_geograficos.py
│   ├── solicitudes_cambio.py
│   ├── catalogos_profesionales.py
│   ├── cuentas.py
│   ├── movimientos.py
│   └── reportes.py
├── services/
│   ├── medicos.py
│   ├── catalogos_geograficos.py
│   ├── solicitudes_cambio.py
│   ├── catalogos_profesionales.py
│   ├── cuentas.py
│   ├── movimientos.py
│   └── reportes.py
├── repositories/
│   ├── base.py
│   ├── medicos.py
│   ├── catalogos_geograficos.py
│   ├── solicitudes_cambio.py
│   ├── catalogos_profesionales.py
│   ├── cuentas.py
│   ├── movimientos.py
│   └── reportes.py
└── tests/
    ├── conftest.py
    ├── test_medicos.py
    ├── test_catalogos_geograficos.py
    ├── test_solicitudes_cambio.py
    ├── test_catalogos_profesionales.py
    ├── test_cuentas.py
    ├── test_movimientos.py
    └── test_reportes.py
```

Los nombres pueden agruparse de otra forma si el equipo lo acuerda, pero cada
endpoint debe conservar la separación Router/Schema/Service/Repository.

## Reparto de trabajo

Reemplacen `P1` a `P6` por los nombres reales del equipo. P1 a P5 son
responsables de router, schema, service, repository y Swagger para sus
endpoints. P6 es responsable de la infraestructura y las pruebas automatizadas
de todos los módulos.

### P1 — Registro y perfil de médicos

Archivos principales:

```text
routers/medicos.py                 # P1: registro y perfil
schemas/medicos.py                 # P1: registro y perfil
services/medicos.py                # P1: registro y perfil
repositories/medicos.py            # P1: registro y perfil
```

Endpoints:

| Método | Ruta | Procedimiento BD |
|---|---|---|
| `POST` | `/medicos` | `registrar_medico` |
| `GET` | `/medicos/{id_medico}` | `obtener_perfil_medico` |

Responsabilidades:

- Modelar los datos personales, profesionales y de dirección.
- Registrar médicos y validar los campos requeridos en Pydantic.
- Exponer el perfil completo agrupado por secciones.
- Coordinar con Base de datos las reglas de unicidad de idoneidad, registro
  médico y cédula.
- Aplicar el permiso de administrador mediante `requiere_rol`.

Tareas compartidas de P1:

- Crear o confirmar la estructura inicial de `app/`.
- Coordinar con Login y permisos las firmas de `get_usuario_actual` y
  `requiere_rol`.
- Coordinar el entorno de desarrollo y las reglas de ramas.
- Mantener la documentación general e integrar cambios a `develop` o `main`.
- Confirmar con Base de datos quién inicializa Alembic.

### P2 — Filtro, edición y catálogos geográficos

Archivos principales:

```text
routers/medicos_directorio.py
routers/catalogos_geograficos.py
schemas/medicos_directorio.py
schemas/catalogos_geograficos.py
services/medicos_directorio.py
services/catalogos_geograficos.py
repositories/medicos_directorio.py
repositories/catalogos_geograficos.py
```

Endpoints:

| Método | Ruta | Procedimiento BD o fuente |
|---|---|---|
| `GET` | `/medicos` | `filtrar_medicos` |
| `PATCH` | `/medicos/{id_medico}/perfil` | `actualizar_medico` |
| `PATCH` | `/medicos/{id_medico}` | `actualizar_medico` |
| `GET` | `/provincias` | Confirmar con BD |
| `GET` | `/provincias/{id_provincia}/distritos` | Confirmar con BD |
| `GET` | `/distritos/{id_distrito}/corregimientos` | Confirmar con BD |

Responsabilidades:

- Validar que `GET /medicos` reciba exactamente un filtro.
- Soportar filtros por apellido, especialidad, asociación, certificación
  vigente o provincia.
- Validar la lista de campos permitidos para `PATCH`.
- Permitir al médico actualizar únicamente información no sensible de su
  propio perfil mediante `/medicos/{id_medico}/perfil`.
- Enviar a `actualizar_medico` los datos como JSON y el administrador actual.
- Confirmar si los catálogos geográficos se consultan mediante funciones
  almacenadas u ORM.

### P3 — Solicitudes de cambio y catálogos profesionales

Archivos principales:

```text
routers/solicitudes_cambio.py
routers/catalogos_profesionales.py
schemas/solicitudes_cambio.py
schemas/catalogos_profesionales.py
services/solicitudes_cambio.py
services/catalogos_profesionales.py
repositories/solicitudes_cambio.py
repositories/catalogos_profesionales.py
```

Endpoints:

| Método | Ruta | Procedimiento BD o fuente |
|---|---|---|
| `POST` | `/solicitudes-cambio` | `crear_solicitud_cambio` |
| `GET` | `/solicitudes-cambio` | `listar_solicitudes_cambio` |
| `POST` | `/solicitudes-cambio/{id_solicitud}/procesar` | `procesar_solicitud_cambio` |
| `GET` | `/especialidades` | Confirmar con BD |
| `GET` | `/subespecialidades` | Confirmar con BD |
| `GET` | `/asociaciones` | Confirmar con BD |

Responsabilidades:

- Validar que las solicitudes solo contengan campos no personales.
- Modelar `cambios` y `decisiones` como JSON estructurado.
- Permitir únicamente decisiones `ACEPTADO` o `NEGADO`.
- Validar que las decisiones cubran todos los campos solicitados.
- Diferenciar el estado general de la solicitud del estado de cada cambio.
- Confirmar con Base de datos los valores oficiales de estado y los catálogos.

### P4 — Cuentas contables

Archivos principales:

```text
routers/cuentas.py
schemas/cuentas.py
services/cuentas.py
repositories/cuentas.py
```

Endpoints:

| Método | Ruta | Procedimiento BD o fuente |
|---|---|---|
| `POST` | `/cuentas` | `crear_cuenta` |
| `PUT` | `/cuentas/{id_cuenta}` | `editar_cuenta` |
| `DELETE` | `/cuentas/{id_cuenta}` | `eliminar_cuenta` |
| `GET` | `/cuentas` | Confirmar con BD |

Responsabilidades:

- Validar nombre, tipo y estado de la cuenta.
- Confirmar con BD los valores permitidos para `tipo`.
- Mostrar el resultado `ELIMINADA` o `DESACTIVADA`.
- No permitir cambios de tipo cuando existan movimientos; la regla final la
  aplica la función de BD.
- Confirmar con Login, Base de datos y el docente los roles autorizados para
  el Módulo 5.
- Resolver si `GET /cuentas` utilizará una función almacenada u ORM.

### P5 — Movimientos, reportes y guía de endpoints

Archivos principales:

```text
routers/movimientos.py
routers/reportes.py
schemas/movimientos.py
schemas/reportes.py
services/movimientos.py
services/reportes.py
repositories/movimientos.py
repositories/reportes.py
docs/endpoints.md
```

Endpoints:

| Método | Ruta | Procedimiento BD |
|---|---|---|
| `POST` | `/movimientos` | `registrar_movimiento` |
| `GET` | `/movimientos` | `consultar_movimientos_diarios` |
| `GET` | `/cuentas/{id_cuenta}/movimientos` | `consultar_movimientos_por_cuenta` |
| `GET` | `/reportes/balance-general` | `calcular_balance_general` |

Responsabilidades:

- Hacer obligatoria la fecha de movimientos diarios.
- Validar que `fecha_inicio <= fecha_fin`.
- Validar montos mayores que cero y tipos de movimiento.
- Confirmar con Base de datos si un movimiento recibe una línea o varias
  líneas contables. El modelo `MOVIMIENTO_CUENTA` permite varias líneas, pero
  la firma actual de `registrar_movimiento` describe una sola.
- Mantener `docs/endpoints.md` con método, ruta, parámetros, rol y ejemplos.
- Entregar a P6 los contratos de entrada, salida, errores y permisos de sus
  endpoints.
- Entregar la guía al equipo Frontend y usarla como contrato para las pruebas.

### P6 — Pruebas automatizadas con pytest

P6 no implementa endpoints de negocio. Prepara la infraestructura de pruebas y
cubre los endpoints desarrollados por P1 a P5.

Archivos principales:

```text
requirements-dev.txt
app/tests/conftest.py
app/tests/test_medicos_directorio.py
app/tests/test_catalogos_geograficos.py
app/tests/test_solicitudes_cambio.py
app/tests/test_catalogos_profesionales.py
app/tests/test_cuentas.py
app/tests/test_movimientos.py
app/tests/test_reportes.py
```

Responsabilidades:

- Mantener `requirements-dev.txt` con `pytest`, `httpx` y las dependencias de
  pruebas acordadas.
- Crear `app/tests/conftest.py` con fixtures comunes.
- Crear un cliente de pruebas para FastAPI.
- Configurar `dependency_overrides` para reemplazar la sesión de BD, los
  repositorios y la autenticación.
- Preparar repositorios falsos para probar services y routers sin PostgreSQL.
- Escribir pruebas de éxito, validación `422`, permisos `401/403`, errores de
  BD `400` y respuestas vacías.
- Verificar códigos de estado, cuerpos JSON y modelos de respuesta.
- Ejecutar la suite completa y reportar fallos al responsable del endpoint.
- Mantener pruebas de regresión para evitar romper endpoints existentes.

Cada responsable P1-P5 debe entregar a P6:

- Método y ruta.
- Schema de entrada y salida.
- Parámetros y ejemplos de Swagger.
- Rol requerido.
- Comportamiento esperado ante éxito, validación y error de BD.
- Interfaz del repository que debe simularse.

P6 prueba el comportamiento HTTP y no debe duplicar la lógica del endpoint.

## Trabajo compartido

Estas tareas no pertenecen exclusivamente a un endpoint:

| Área | Responsable principal | Participantes |
|---|---|---|
| `repositories/base.py` | P2 | Todos los responsables de repositorios |
| `errors.py` y traducción de errores de BD | P2 | Todos |
| `tests/conftest.py`, fixtures y `dependency_overrides` | P6 | P1-P5 entregan contratos |
| Autenticación y autorización | Login y permisos | Backend integra sus dependencias |
| Funciones almacenadas y firmas | Base de datos | Cada responsable valida su módulo |
| Modelos, migraciones y datos iniciales | Base de datos | Backend solo coordina contratos |
| Pruebas unitarias de endpoints | P6 | P1-P5 entregan contratos y repositorios simulables |
| Pruebas de integración y sistema | Grupo de Pruebas | P6 entrega la suite unitaria y los contratos |
| Documentación de endpoints | P5 | Todos actualizan sus rutas |

Backend no implementa JWT, hash de contraseñas, login, roles, modelos ni
migraciones pertenecientes a los otros grupos. El endpoint
`crear_cuenta_medico` debe ser asignado formalmente a Login y permisos porque
involucra credenciales y posiblemente emisión de token.

## Dependencias de implementación

1. P1 confirma la estructura de `app/` y el arranque del proyecto.
2. Login y permisos entrega las firmas de `get_usuario_actual` y
   `requiere_rol`.
3. P2 mantiene disponibles `repositories/base.py` y `errors.py`.
4. P6 prepara `conftest.py`, los fixtures y el cliente de pruebas.
5. Cada persona implementa primero sus schemas; después su repository, service
   y router.
6. Cada responsable verifica sus procedimientos contra la base real cuando
   Base de datos los entregue.
7. P1-P5 entregan sus contratos a P6; P5 mantiene la guía de endpoints y P6
   mantiene la suite de pytest.

Ningún endpoint se considera terminado si depende de una firma de BD o de un
rol que todavía no está confirmado.

## Convenciones de implementación

### Repository

Los repositorios deben reutilizar las funciones de
`app.repositories.base`:

```python
from app.repositories.base import Arg, llamar_escalar, llamar_tabla
```

- Usar `llamar_escalar` para resultados simples.
- Usar `llamar_tabla` para varias filas.
- Usar `Arg(valor, tipo_sql)` cuando el valor pueda ser `None` o sea JSON.
- Usar `commit=True` únicamente en operaciones de escritura.
- No concatenar valores de usuario dentro del SQL.

### Service

El service debe contener validaciones como:

- Exactamente un filtro.
- Fechas consistentes.
- Campos permitidos.
- Decisiones completas.
- Transformación de estructuras de entrada.

### Router

El router debe encargarse de:

- Recibir parámetros HTTP.
- Declarar dependencias.
- Aplicar permisos.
- Llamar al service.
- Declarar `response_model`, `status_code` y ejemplos OpenAPI.

Los errores `DBAPIError` se procesan globalmente mediante
`app.errors.manejar_error_bd`, que devuelve el mensaje de PostgreSQL con HTTP
`400`.

## Criterios de terminado

Un endpoint está terminado cuando:

- Tiene router, schema, service y repository.
- Su procedimiento o fuente de datos está confirmado.
- P6 tiene pruebas unitarias con repositorio falso.
- Comprueba casos exitosos, validación, permisos y errores de BD.
- Aparece correctamente en `/docs`.
- Incluye ejemplos de solicitud y respuesta.
- Fue revisado por otra persona mediante pull request.
- Funciona contra la base real cuando el procedimiento está disponible.
- Está documentado en `docs/endpoints.md`.

## Ejecución con Docker Compose

El sistema utiliza tres repositorios coordinados:

```text
SiColMed-Infrastructure/
├── docker-compose.yml
├── SiColMed-BackEnd/
└── SiColMed-FrontEnd/
```

El archivo `docker-compose.yml` está en `SiColMed-Infrastructure`, no en este
repositorio. Desde la carpeta raíz que contiene los tres repositorios, entra a
la infraestructura, verifica el archivo `.env` y levanta los tres servicios:

```powershell
cd .\SiColMed-Infrastructure
docker compose up --build
```

Usa `--build` después de cambiar un `Dockerfile`, dependencias o la
configuración de construcción. Si las imágenes ya están actualizadas, basta
con:

```powershell
docker compose up
```

Para ejecutar en segundo plano:

```powershell
docker compose up --build -d
```

Para detener los servicios:

```powershell
docker compose down
```

Servicios disponibles:

| Servicio | Dirección | Propósito |
|---|---|---|
| `db` | `localhost:5432` | PostgreSQL |
| `api` | `http://localhost:8000` | Backend FastAPI |
| `web` | `http://localhost:3000` | Frontend |

No ejecutes `docker compose up --build` desde la carpeta del backend si el
`docker-compose.yml` está únicamente en `SiColMed-Infrastructure`.

## Pruebas con pytest

P6 mantiene y ejecuta las pruebas del backend. Para ejecutar la suite en el
entorno virtual local:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pytest .\app\tests -v
```

Si las dependencias de desarrollo están instaladas en el contenedor `api`,
también se puede ejecutar desde `SiColMed-Infrastructure`:

```powershell
docker compose exec api python -m pytest /code/app/tests -v
```

### Ejecución opcional de la API fuera de Docker

El siguiente comando solo debe utilizarse cuando se quiera iniciar el backend
directamente desde el entorno virtual local:

```powershell
uvicorn app.main:app --reload
```

Este comando no inicia PostgreSQL ni el frontend. En este caso,
`DATABASE_URL` debe apuntar a una base de datos accesible desde el equipo
local, normalmente utilizando `localhost` en lugar de `db`.

Documentación interactiva:

```text
http://127.0.0.1:8000/docs
```

Antes de ejecutar la API se debe configurar `DATABASE_URL` en `.env`. Nunca
subir credenciales, claves ni datos reales al repositorio.

## Flujo de ramas y revisión

- Crear ramas como `feature/<modulo>-<tema>`.
- Partir siempre de `develop`.
- Usar commits con prefijos `feat:`, `fix:`, `test:` o `docs:`.
- Abrir pull requests hacia `develop`.
- Solicitar al menos una aprobación.
- No modificar carpetas de otros grupos sin avisar.
- Integrar a `main` únicamente después de validar el entorno y las pruebas.
