# Datos de prueba (QA)

Qué crea `app/scripts/seed_qa.py`, para qué sirve cada registro y cómo usarlo.

> **Solo para desarrollo y QA.** El script solo corre si `ENVIRONMENT` es `development`,
> `qa` o `test`. Sin la variable, con otro valor o con `production`, se detiene antes de
> conectarse a la base de datos. En Docker la variable viene del `.env` de
> `SiColMed-Infrastructure`: si tu `.env` no la tiene, agrega `ENVIRONMENT=development`.
> Las contraseñas de esta página son públicas: no las uses en ningún ambiente real.

## Cómo cargarlos

Desde `SiColMed-Infrastructure`, con los contenedores levantados:

```bash
docker compose exec api alembic upgrade head                     # estructura
docker compose exec api python -m app.scripts.seed_catalogos     # catálogos (obligatorio)
docker compose exec api python -m app.scripts.seed_qa            # datos de prueba
```

`python -m app.scripts.seed` sigue funcionando y ejecuta los dos seeds seguidos.

Se puede ejecutar varias veces. Cada registro se busca por una clave estable y, si ya
existe, no se vuelve a crear ni se modifica. El script nunca borra datos.

| Registro | Clave estable |
|---|---|
| Usuario | Correo |
| Médico | Número de idoneidad |
| Cuenta | Nombre |
| Movimiento | Descripción |
| Solicitud | Comentario que empieza con `[QA]` |

## Identificadores

Los identificadores los genera la base de datos. Dependen de lo que ya había antes del
seed. La tabla muestra los que quedaron:

- **BD nueva:** después de `alembic upgrade head` en una base vacía.
- **BD de desarrollo actual:** la del equipo, al 3 de noviembre de 2026. Ya tenía el admin,
  dos médicos y una cuenta borrada (la 1).

| Entidad | Clave estable | ID en BD nueva | ID en BD de desarrollo actual | Escenario |
|---|---|---|---|---|
| Médico | IDONEIDAD-0001 | 1 | 1 | Certificación vigente (Panamá, Medicina interna, subespecialidad Cardiología) |
| Médico | IDONEIDAD-0002 | 2 | 2 | Certificación vencida (Panamá, Pediatría) |
| Médico | IDONEIDAD-0003 | 3 | 3 | Sin certificación (Chiriquí, Ginecología y obstetricia) |
| Médico | IDONEIDAD-0004 | 4 | 4 | Certificación vigente (Veraguas, Cirugía general) |
| Cuenta | QA Caja general | 1 | 2 | Tiene movimientos. Prueba las restricciones de eliminar y de cambiar el tipo |
| Cuenta | QA Banco operativo | 2 | 3 | Tiene movimientos |
| Cuenta | QA Ingresos por cuotas | 3 | 4 | Tiene movimientos (cuenta CREDITO) |
| Cuenta | QA Cuenta sin movimientos | 4 | 5 | Sin movimientos. Se puede eliminar y cambiar el tipo |
| Solicitud | [QA] Solicitud pendiente | 1 | 1 | Pendiente |
| Solicitud | [QA] Solicitud aceptada | 2 | 2 | Aceptada |
| Solicitud | [QA] Solicitud negada | 3 | 3 | Negada |
| Denuncia | — | — | — | **No implementado**: el proyecto no tiene tabla, modelo ni endpoint de denuncias |

Para ver los identificadores en cualquier base de datos:

```sql
SELECT 'medico', id_medico, numero_idoneidad FROM medico WHERE numero_idoneidad LIKE 'IDONEIDAD-000%'
UNION ALL SELECT 'cuenta', id_cuenta, nombre FROM cuenta WHERE nombre LIKE 'QA %'
UNION ALL SELECT 'solicitud', id_solicitud_cambio, comentario FROM solicitud_cambio WHERE comentario LIKE '[QA]%'
ORDER BY 1, 2;
```

## Credenciales

| Rol | Correo | Contraseña | Variables para cambiarlas |
|---|---|---|---|
| admin_cmp | admin@colmed.dev | Admin123! | `DEMO_ADMIN_EMAIL`, `DEMO_ADMIN_PASSWORD` |
| medico | medico1@colmed.dev | Medico123! | `DEMO_MEDICO1_EMAIL`, `DEMO_MEDICO1_PASSWORD` |
| medico | medico2@colmed.dev | Medico123! | `DEMO_MEDICO2_EMAIL`, `DEMO_MEDICO2_PASSWORD` |
| medico | medico3@colmed.dev | Medico123! | `DEMO_MEDICO3_EMAIL`, `DEMO_MEDICO3_PASSWORD` |
| medico | medico4@colmed.dev | Medico123! | `DEMO_MEDICO4_EMAIL`, `DEMO_MEDICO4_PASSWORD` |

- **Contraseñas:** en la base de datos solo se guarda su hash (pwdlib), nunca el texto.
- **Variables `DEMO_*`:** cada valor de la tabla se puede cambiar con su variable de
  entorno.
- **Tesorero y admin de asociación:** no hay usuarios de prueba, porque ningún mecanismo
  real los crea:
  - `crear_usuario_admin.sql` crea solo `admin_cmp`.
  - `crear_cuenta_medico.sql` y `POST /auth/register` crean solo `medico`, y exigen un
    médico registrado.
  - No hay endpoint ni pantalla de administración de usuarios.

  Insertarlos directo en `usuario` saltaría las validaciones y la auditoría que hacen esas
  funciones. Además, `admin_asociacion` no tiene cómo indicar *qué* asociación administra:
  `usuario` no tiene esa relación y el catálogo de asociaciones está vacío. Base de Datos
  debe definir una función de alta para esos roles. Con ella, el escenario se agrega a
  `seed_qa.py`.

## Médicos y certificaciones

| Médico | Nombre | Dirección (provincia / distrito / corregimiento) | Especialidad | Certificación |
|---|---|---|---|---|
| IDONEIDAD-0001 | Ana Maria Perez Gomez | Panamá / Panamá / Bella Vista | Medicina interna; subespecialidad Cardiología | Vigente: obtenida 2025-01-15, expira 2030-01-15, puntaje 95 |
| IDONEIDAD-0002 | Luis Rodriguez Diaz | Panamá / Panamá / Bella Vista | Pediatría | Vencida: obtenida 2019-01-10, expiró 2024-01-10, puntaje 80 |
| IDONEIDAD-0003 | Carmen Isabel Sanchez Rios | Chiriquí / David / David | Ginecología y obstetricia | Ninguna |
| IDONEIDAD-0004 | Jorge Castillo Vega | Veraguas / Santiago / Santiago | Cirugía general | Vigente: obtenida 2025-01-15, expira 2030-01-15. Puntaje 95; la solicitud aceptada lo cambió a 98 |

- **Médicos 1 y 2 en la BD de desarrollo actual:** además conservan la especialidad
  «Medicina General» del seed antiguo. El seed no borra relaciones que ya existían.
- **Vigencia en el perfil:** el perfil la calcula con `fecha_expiracion >= hoy`, así que
  la certificación de 2030 aparece como vigente hasta esa fecha.
- **Asociaciones:** no hay médicos con asociación. El catálogo de asociaciones está vacío
  porque no hay una lista oficial (ver `docs/fuentes-especialidades.md`).

## Cuentas y movimientos

| Movimiento | Fecha | Débito | Crédito |
|---|---|---|---|
| QA - Cobro de cuotas de enero | 2026-01-15 | QA Caja general 150.00 | QA Ingresos por cuotas 150.00 |
| QA - Depósito de caja en banco | 2026-01-20 | QA Banco operativo 100.00 | QA Caja general 100.00 |

Reglas que se pueden probar (funciones `editar_cuenta` y `eliminar_cuenta`):

| Acción | Sobre «QA Caja general» (con movimientos) | Sobre «QA Cuenta sin movimientos» |
|---|---|---|
| Cambiar el tipo | Error: «No se puede cambiar el tipo de una cuenta que ya tiene movimientos» | Se permite |
| Eliminar | No se borra: queda **desactivada** (respuesta `DESACTIVADA`) | Se borra (respuesta `ELIMINADA`) |

Estas pruebas cambian los datos, por ejemplo al eliminar la cuenta sin movimientos. Para
recuperar el escenario, vuelve a ejecutar `seed_qa`. Una cuenta borrada se crea de nuevo,
con otro ID. Una desactivada no se reactiva: el script no modifica registros existentes.

## Solicitudes de cambio

Todas piden cambiar el **puntaje** de la certificación del médico.

| Solicitud | Médico | Cambio pedido | Estado guardado | Resultado |
|---|---|---|---|---|
| [QA] Solicitud pendiente | IDONEIDAD-0001 | 95 → 97 | `PENDIENTE` | Sin resolver. Sirve para probar la aprobación o el rechazo |
| [QA] Solicitud aceptada | IDONEIDAD-0004 | 95 → 98 | `PROCESADO`, campo `APROBADO` | El puntaje se cambió a 98 |
| [QA] Solicitud negada | IDONEIDAD-0002 | 80 → 99 | `PROCESADO`, campo `RECHAZADO` | El puntaje sigue en 80 |

El proyecto no tiene estados «Aceptada» ni «Negada».

- **Qué estados existen:** `solicitud_cambio.estado` solo puede ser `PENDIENTE` o
  `PROCESADO`. La decisión se guarda campo por campo dentro de `cambios`, como `APROBADO`
  o `RECHAZADO` (función `procesar_solicitud_cambio`).
- **Cómo se armaron los dos casos:** «aceptada» es una solicitud `PROCESADO` con todos sus
  campos `APROBADO`, y «negada» una con todos `RECHAZADO`.
- **Cómo se crearon:** con las funciones reales `crear_solicitud_cambio` y
  `procesar_solicitud_cambio`, esta última con el usuario admin.

## Denuncias

**No se crearon.** El proyecto no tiene tabla, modelo, función ni endpoint de denuncias,
ni estados definidos («No atendido», «Pendiente», «Atendido»). Crearlos sería inventar
estructura, cosa que la tarea prohíbe. Cuando Base de Datos defina el módulo, se agrega el
escenario a `seed_qa.py`.

## Advertencias

- No ejecutes `seed_qa` contra una base de datos con datos reales.
  - Agrega médicos y cuentas ficticias.
  - La solicitud aceptada cambia un puntaje.
- En producción define `ENVIRONMENT=production` y ejecuta solo `seed_catalogos`. Aunque
  alguien olvide definir la variable, `seed_qa` y `seed` se niegan a correr.
- Los nombres, cédulas y teléfonos de los médicos son ficticios.
