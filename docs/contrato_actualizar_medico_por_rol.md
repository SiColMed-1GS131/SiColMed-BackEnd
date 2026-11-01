# Contrato de actualización de médico por rol

## Objetivo

Definir cómo se utilizará la función de Base de Datos
`actualizar_medico` desde los dos flujos del backend:

1. Actualización directa de información no sensible por el propio médico.
2. Aplicación administrativa de cambios previamente aprobados.

Ambos flujos pueden utilizar la misma función SQL, pero el backend debe aplicar
un contrato diferente según el rol antes de enviarla a Base de Datos.

```text
PATCH /medicos/{id_medico}/perfil
    Rol: medico
    Actor: el propio médico

PATCH /medicos/{id_medico}
    Rol: admin_cmp
    Actor: administrador que aplica un cambio aprobado

GET /medicos/{id_medico}
    Roles: medico, admin_cmp
    Actor: el propio médico o un administrador
```

La autorización del endpoint no reemplaza las validaciones de Base de Datos.
La función SQL debe validar nuevamente el actor, el médico, los campos y las
reglas de integridad.

El endpoint `GET /medicos/{id_medico}` requiere autenticación. Un usuario con
rol `medico` solo puede consultar el perfil asociado a su `id_medico`; un
usuario con rol `admin_cmp` puede consultar cualquier perfil autorizado.
Para aplicar esta regla, el JWT de un médico debe incluir el claim
`id_medico`. Los tokens administrativos no necesitan ese claim.

## Firma única de Base de Datos

La función debe conservar una firma única:

```sql
actualizar_medico(
    p_id_medico        INTEGER,
    p_id_administrador INTEGER,
    p_datos            JSONB
) RETURNS BOOLEAN
```

Aunque el nombre `p_id_administrador` se conserva por compatibilidad, representa
al usuario que ejecuta la actualización. En el flujo administrativo será un
administrador CMP. En el flujo del perfil será el médico autenticado, siempre
que Base de Datos y el equipo definan que ese actor está autorizado para los
campos no sensibles.

## Reglas generales obligatorias

La función debe rechazar la operación cuando:

1. `p_id_medico` sea `NULL` o menor que `1`.
2. `p_id_administrador` sea `NULL` o menor que `1`.
3. `p_datos` sea `NULL`.
4. `p_datos` no sea un objeto JSON.
5. `p_datos` sea un objeto vacío.
6. El usuario actor no exista.
7. El usuario actor esté inactivo.
8. El médico no exista.
9. Se reciba un campo no permitido para el flujo.
10. Se intente enviar un campo obligatorio con `NULL` o texto vacío.
11. Se viole una restricción de unicidad o integridad.

La actualización debe realizarse dentro de una única transacción. Si una
validación o actualización falla, no debe quedar aplicado ningún cambio
parcial.

## Campos permitidos para el perfil del médico

Este contrato corresponde a:

```text
PATCH /medicos/{id_medico}/perfil
```

Rol requerido:

```text
medico
```

El backend debe permitir únicamente estos campos:

### Información personal no sensible

| Campo | Tipo | ¿Puede ser `NULL`? | Regla |
|---|---|---:|---|
| `primer_nombre` | `TEXT` | No, si se envía | No puede quedar vacío |
| `segundo_nombre` | `TEXT` | Sí | No puede quedar vacío si se envía |
| `apellido_paterno` | `TEXT` | No, si se envía | No puede quedar vacío |
| `apellido_materno` | `TEXT` | Sí | No puede quedar vacío si se envía |
| `foto` | `TEXT` | Sí | No puede quedar vacía si se envía |
| `telefono_residencial` | `TEXT` | Sí | No puede quedar vacío si se envía |
| `celular` | `TEXT` | Sí | No puede quedar vacío si se envía |
| `email_personal` | `TEXT` | Sí | Debe tener formato válido si se envía |

### Dirección residencial

La dirección debe enviarse agrupada bajo la clave `direccion`:

| Campo | Tipo | ¿Puede ser `NULL`? | Regla |
|---|---|---:|---|
| `apartado_postal` | `TEXT` | Sí | No puede quedar vacío si se envía |
| `calle` | `TEXT` | Sí | No puede quedar vacía si se envía |
| `edificio` | `TEXT` | Sí | No puede quedar vacío si se envía |
| `numero_direccion` | `TEXT` | Sí | No puede quedar vacío si se envía |
| `id_corregimiento` | `INTEGER` | Sí | Debe existir si se envía |

La función no debe permitir que el perfil del médico modifique directamente:

```text
numero_idoneidad
numero_registro_medico
cedula
fecha_nacimiento
educación
especialidades
subespecialidades
asociaciones
certificaciones
lugar_trabajo
```

## Campos permitidos para el flujo administrativo

Este contrato corresponde a:

```text
PATCH /medicos/{id_medico}
```

Rol requerido:

```text
admin_cmp
```

El backend puede enviar los campos médicos definidos por el cambio aprobado:

| Campo | Tipo | ¿Puede ser `NULL`? | Regla |
|---|---|---:|---|
| `numero_idoneidad` | `TEXT` | No, si se envía | No puede quedar vacío; debe ser único |
| `numero_registro_medico` | `TEXT` | No, si se envía | No puede quedar vacío; debe ser único |
| `cedula` | `TEXT` | No, si se envía | No puede quedar vacía; debe ser única |
| `primer_nombre` | `TEXT` | No, si se envía | No puede quedar vacío |
| `segundo_nombre` | `TEXT` | Sí | No puede quedar vacío si se envía |
| `apellido_paterno` | `TEXT` | No, si se envía | No puede quedar vacío |
| `apellido_materno` | `TEXT` | Sí | No puede quedar vacío si se envía |
| `foto` | `TEXT` | Sí | No puede quedar vacía si se envía |
| `fecha_nacimiento` | `DATE` | No, si se envía | No puede ser futura |
| `telefono_residencial` | `TEXT` | Sí | No puede quedar vacío si se envía |
| `celular` | `TEXT` | Sí | No puede quedar vacío si se envía |
| `email_personal` | `TEXT` | Sí | Debe tener formato válido si se envía |

También puede incluir:

```json
{
  "direccion": {
    "apartado_postal": "0819",
    "calle": "Calle Principal",
    "edificio": "Edificio 4",
    "numero_direccion": "12",
    "id_corregimiento": 5
  }
}
```

La lista administrativa debe coincidir con los campos que fueron aprobados en
la solicitud. Base de Datos no debe aceptar que el backend envíe campos fuera
de esta lista.

## Campos obligatorios

### En la estructura de la función

Estos parámetros siempre son obligatorios:

```text
p_id_medico
p_id_administrador
p_datos
```

### Dentro de `p_datos`

Los campos de `p_datos` son parciales: una actualización puede modificar uno o
varios campos. Por eso no se debe exigir que todos los campos médicos estén
presentes en cada llamada.

Cuando un campo obligatorio existente se incluya en `p_datos`, no puede quedar
vacío:

```text
numero_idoneidad
numero_registro_medico
cedula
primer_nombre
apellido_paterno
fecha_nacimiento
```

La ausencia de un campo significa “no modificarlo”. No significa borrar su
valor actual.

Ejemplo válido de actualización parcial:

```json
{
  "celular": "6000-1234"
}
```

Ejemplo inválido:

```json
{
  "primer_nombre": ""
}
```

## Reglas adicionales de autorización

La función debe verificar el actor según el flujo. El backend debe hacer la
primera validación mediante JWT y `requiere_rol`.

### Flujo del médico

Debe cumplirse:

```text
rol del token = medico
id_medico del usuario autenticado = p_id_medico
```

El médico no debe poder actualizar el perfil de otro médico cambiando el ID de
la URL.

### Flujo administrativo

Debe cumplirse:

```text
rol del token = admin_cmp
```

El administrador puede aplicar cambios sobre el médico indicado, pero la lista
de campos debe provenir de una solicitud aprobada. El backend no debe convertir
automáticamente cualquier body administrativo en un cambio aprobado.

Base de Datos debe verificar como mínimo que el actor exista y esté activo.
La validación definitiva del rol puede realizarse en backend, en Base de Datos o
en ambos lugares, pero debe existir una política única y documentada.

## Ejemplos de solicitudes

### Médico: información personal

```json
{
  "celular": "6000-1234",
  "email_personal": "medico@ejemplo.com"
}
```

### Médico: dirección

```json
{
  "direccion": {
    "calle": "Calle Principal",
    "edificio": "Edificio 4",
    "numero_direccion": "12",
    "id_corregimiento": 5
  }
}
```

### Administrador: cambio aprobado

```json
{
  "cedula": "8-123-456",
  "fecha_nacimiento": "1990-01-10"
}
```

Este último ejemplo solo debe ejecutarse después de que exista una solicitud
aprobada para esos campos.

## Educación

La sección de educación aparece en el perfil funcional, pero sus campos,
tablas y relaciones no están definidos todavía en la función
`actualizar_medico`.

Hasta que Base de Datos confirme el contrato, no se deben agregar claves como
`educacion`, `titulo_basico`, `institucion`, `lugar` o `fecha` a la función.

Cuando se defina, deberá documentarse explícitamente:

1. Si `educacion` es un objeto o una lista.
2. Los nombres exactos de sus campos.
3. Los tipos de cada campo.
4. Las tablas que se modifican.
5. Si el médico puede editarla directamente.
6. Si requiere solicitud y aprobación administrativa.
7. Cómo se eliminan o reemplazan registros anteriores.

## Retorno

La función debe devolver:

```sql
BOOLEAN
```

Respuesta esperada cuando la actualización se aplica correctamente:

```json
{
  "actualizado": true
}
```

Si no se actualiza ningún registro, debe producirse un error controlado o
devolver `false` según el contrato definitivo. El backend no debe convertir
silenciosamente un resultado ambiguo en una respuesta exitosa.

## Errores esperados

| Situación | Respuesta HTTP recomendada |
|---|---:|
| Body con campos desconocidos | `422 Unprocessable Entity` |
| Body vacío | `422 Unprocessable Entity` |
| ID inválido | `422 Unprocessable Entity` |
| Token ausente o inválido | `401 Unauthorized` |
| Rol incorrecto | `403 Forbidden` |
| Médico intentando modificar otro perfil | `403 Forbidden` |
| Médico inexistente | `404 Not Found` |
| Actor inexistente o inactivo | `400 Bad Request` |
| Duplicidad de cédula, idoneidad o registro | `400 Bad Request` |
| Corregimiento inexistente | `400 Bad Request` |
| Error inesperado de la función | `500 Internal Server Error` |

## Auditoría

Cada ejecución exitosa debe registrar:

```text
id_usuario
id_rol
accion
entidad = MEDICO
id_registro = p_id_medico
fecha_hora
campos actualizados
```

La auditoría debe identificar al usuario que realmente ejecutó la operación:

- Médico en la edición directa.
- Administrador CMP en la aplicación de un cambio aprobado.

## Criterios de aceptación

La implementación se considerará correcta cuando:

- La firma de la función coincida con este documento.
- Los parámetros se reciban en el orden documentado.
- El backend envíe `p_datos` como `JSONB`.
- El médico solo pueda modificar su propio perfil.
- El médico no pueda modificar campos sensibles.
- El administrador CMP pueda aplicar únicamente cambios aprobados.
- Los campos obligatorios no puedan quedar vacíos.
- Los campos únicos se validen contra otros médicos.
- La dirección valide el `id_corregimiento`.
- La operación sea atómica.
- Toda actualización exitosa quede auditada.
- Educación no se acepte hasta contar con un contrato definido.
