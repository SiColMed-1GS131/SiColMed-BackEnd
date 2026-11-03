# Carga masiva de médicos por CSV

Este documento explica cómo preparar el archivo CSV para registrar médicos en lote. Se sube
desde **Registro médico → «Cargar médicos con .csv»**, en sesión de administrador.

El frontend envía el archivo a `POST /medicos/importar` (requerimiento 9). La lógica está en
`app/services/importacion_medicos.py` y el ejemplo listo para usar en
`docs/ejemplos/carga_medicos_ejemplo.csv`, con 5 médicos ficticios.

## Formato del archivo

- **Codificación:** UTF-8, con o sin BOM. Si el archivo usa otra codificación, la carga se
  rechaza con el código 415.
- **Separador:** coma (`,`). Un valor que lleve una coma va entre comillas dobles.
- **Primera línea:** la cabecera, con todas las columnas de la tabla de abajo. Pueden ir en
  cualquier orden. Si falta alguna, el archivo completo se rechaza con el código 422 y
  la respuesta indica cuáles faltan.
- **Límites:** 2 MB y 500 filas de datos. Las filas vacías se ignoran.
- **Fechas:** formato `AAAA-MM-DD`.

Una columna «opcional» debe estar en la cabecera, pero su valor puede quedar vacío.

### Columnas

| Columna | Obligatorio | Contenido |
|---|---|---|
| `cedula` | Sí | Cédula, única. Ej.: `8-901-2345` |
| `primer_nombre` | Sí | |
| `segundo_nombre` | No | |
| `primer_apellido` | Sí | Se guarda como `apellido_paterno` |
| `segundo_apellido` | No | Se guarda como `apellido_materno` |
| `fecha_nacimiento` | Sí | No puede ser futura |
| `telefono` | No | Teléfono residencial. Ej.: `507-264-1180` |
| `celular` | No | Ej.: `6612-4478` |
| `email` | No | Correo personal válido |
| `apartado_postal` | Sí | Apartado de la dirección residencial |
| `idoneidad` | Sí | Número de idoneidad, único |
| `registro_medico` | Sí | Número de registro médico, único |
| `calle`, `numero` | Sí | Dirección residencial |
| `edificio` | No | |
| `corregimiento` | Sí | **Código oficial DPA** del corregimiento de residencia (ej. `080807` = Bella Vista, Panamá). Ver `docs/fuentes-division-politica-panama.md` |
| `empresa_institucion`, `cargo`, `telefono_trabajo`, `email_laboral` | Sí | Lugar de trabajo |
| `trabajo_apartado_postal`, `trabajo_calle`, `trabajo_numero`, `trabajo_corregimiento` | Sí | Dirección del trabajo. El corregimiento va como código DPA |
| `trabajo_edificio` | No | |
| `titulo`, `institucion`, `lugar_estudio`, `fecha_titulo` | Sí | Estudio básico. Se guarda con el tipo «Título básico» |
| `cert_fecha_obtencion`, `cert_fecha_expiracion`, `cert_puntaje` | Sí | Certificación. El puntaje es un entero ≥ 0 y la expiración no puede ser anterior a la obtención |
| `especialidades`, `subespecialidades`, `asociaciones` | No | Nombres del catálogo separados por `;` (ej. `Medicina interna;Pediatría`). No distingue tildes ni mayúsculas. Cada subespecialidad debe pertenecer a una de las especialidades indicadas |

Notas sobre algunos campos:

- **Certificación vigente:** no tiene columna propia. Se deduce como
  `cert_fecha_expiracion >= hoy`, la misma regla que usa el perfil del médico.
- **Por qué hay tantas columnas obligatorias:** la función `registrar_medico` exige la
  dirección, el lugar de trabajo con su dirección, el estudio básico y la certificación.
  Además, la tabla `direccion` no admite apartado postal, calle ni número vacíos.

## Qué pasa con cada fila

- **Registro:** cada fila se valida y se registra por separado, con `registrar_medico`, igual
  que el formulario.
- **Filas con error:** no detienen la carga. Se informan con su número de línea (la línea 1
  es la cabecera), y las demás filas se registran igual.
- **Errores comunes:**
  - un dato obligatorio vacío o con formato inválido;
  - un corregimiento o una especialidad que no existe en el catálogo;
  - una cédula, idoneidad o registro médico repetido. En este caso el mensaje es el de la
    base de datos.

Respuesta:

```json
{"archivo": "carga.csv", "procesados": 5, "registrados": 4, "rechazados": 1,
 "errores": [{"fila": 3, "error": "corregimiento: el corregimiento con código 999999 no existe"}],
 "id_auditoria": 16}
```

## Auditoría

Cada carga deja **una fila en la tabla `auditoria`**, también la que se rechaza entera
(cabecera incompleta, codificación incorrecta, archivo demasiado grande). La escribe la
función `registrar_carga_medicos` (migración `e98cfc158897`).

| Columna | Valor |
|---|---|
| `id_usuario`, `id_rol` | Administrador del token JWT. La función exige que esté activo y sea `admin_cmp` |
| `accion` / `entidad` | `CARGA_MASIVA_MEDICOS` / `MEDICO` |
| `id_registro` | `0`: la carga no corresponde a un único registro |
| `fecha_hora` | Momento de la carga |
| `descripcion` | JSON: `{"archivo", "procesados", "registrados", "rechazados", "errores": [{"fila", "error"}]}` |

Para consultar las cargas:

```sql
SELECT id_auditoria, fecha_hora, descripcion::jsonb
  FROM auditoria
 WHERE accion = 'CARGA_MASIVA_MEDICOS'
 ORDER BY fecha_hora DESC;
```
