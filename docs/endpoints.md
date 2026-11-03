# Guía de Endpoints - Módulo 5 (Contabilidad y Reportes)
**Responsable:** Persona 5 (P5)

> **Nota sobre Roles:** Los roles específicos con acceso al Módulo 5 están pendientes de confirmación con el docente y BD (Tarea P4-08). Por ahora, los endpoints están protegidos bajo el rol general de acceso contable.

---

## 1. Registrar Movimiento Contable
Registra una nueva operación contable en el sistema.

* **Método:** `POST`
* **Ruta:** `/movimientos`
* **Rol Requerido:** Administrador / Contable (Por definir)
* **Body (JSON):**
  ```json
  {
    "fecha": "2026-10-17", 
    "descripcion": "Pago de servicios de internet",
    "id_cuenta": 3,
    "tipo": "DEBITO",
    "monto": 150.50
  }
  ```
  *(Nota: Si "fecha" se envía como null o se omite, la Base de Datos usará la fecha actual del sistema).*
* **Respuesta Exitosa (201 Created):**
  ```json
  {
    "mensaje": "Movimiento registrado exitosamente",
    "id_movimiento": 105
  }
  ```

---

## 2. Consultar Movimientos Diarios
Obtiene todos los movimientos registrados en una fecha específica.

* **Método:** `GET`
* **Ruta:** `/movimientos`
* **Rol Requerido:** Administrador / Contable
* **Parámetros Query:**
  * `fecha` (Obligatorio, formato YYYY-MM-DD)
* **Respuesta Exitosa (200 OK):**
  ```json
  [
    {
      "id_movimiento": 105,
      "fecha": "2026-10-17",
      "descripcion": "Pago de servicios de internet",
      "id_cuenta": 3,
      "nombre_cuenta": "Gastos Operativos",
      "tipo": "DEBITO",
      "monto": 150.50
    }
  ]
  ```

---

## 3. Consultar Movimientos por Cuenta
Obtiene el historial de débitos y créditos de una cuenta específica dentro de un período.

* **Método:** `GET`
* **Ruta:** `/cuentas/{id_cuenta}/movimientos`
* **Rol Requerido:** Administrador / Contable
* **Parámetros de Ruta:**
  * `id_cuenta` (Obligatorio, entero)
* **Parámetros Query:**
  * `fecha_inicio` (Obligatorio, formato YYYY-MM-DD)
  * `fecha_fin` (Obligatorio, formato YYYY-MM-DD)
* **Respuesta Exitosa (200 OK):**
  ```json
  [
    {
      "id_movimiento": 105,
      "fecha": "2026-10-17",
      "descripcion": "Pago de servicios de internet",
      "monto": 150.50,
      "tipo": "DEBITO"
    }
  ]
  ```

---

## 4. Reporte: Balance General
Calcula y obtiene los saldos contables para elaborar el reporte del balance general.

* **Método:** `GET`
* **Ruta:** `/reportes/balance-general`
* **Rol Requerido:** Administrador / Contable / Gerencia
* **Parámetros Query:**
  * `fecha_inicio` (Obligatorio, formato YYYY-MM-DD)
  * `fecha_fin` (Obligatorio, formato YYYY-MM-DD)
* **Respuesta Exitosa (200 OK):**
  ```json
  {
    "filas": [
      {
        "id_cuenta": 1,
        "nombre_cuenta": "Caja General",
        "total_debito": 5000.00,
        "total_credito": 1500.00,
        "saldo": 3500.00
      }
    ]
  }
  ```

---

## Nota: funciones `listar_cuentas` y `crear_cuenta` (fix de emergencia)

> ⚠️ **Pendiente de revisión por Base de Datos.** Estas dos funciones las creó **Desarrollo**, no el subgrupo de BD, como fix de emergencia: sin ellas `GET /cuentas` y `POST /cuentas` respondían 400 (`function listar_cuentas(boolean) does not exist`).

* **Archivos:** `app/funciones/listar_cuentas.sql`, `app/funciones/crear_cuenta.sql`
* **Migración:** `alembic/versions/0b02962cab9d_agrega_funciones_listar_cuentas_y_crear_.py` (llega con `alembic upgrade head`)
* **Firmas:**
  * `listar_cuentas(p_activa boolean DEFAULT NULL)` → `TABLE(id_cuenta, nombre, tipo, activa, tiene_movimientos)`. `tiene_movimientos` es `true` si la cuenta aparece en `movimiento_cuenta`; el frontend lo usa para bloquear el cambio de tipo.
  * `crear_cuenta(p_nombre text, p_tipo text)` → `integer` (id_cuenta). Rechaza tipos distintos de `DEBITO`/`CREDITO` y crea la cuenta activa.
* **Qué debe confirmar BD:** el orden de `listar_cuentas` (por nombre), el mensaje de error de `crear_cuenta` y si quieren un mensaje propio para nombres repetidos (hoy lo rechaza la restricción `UNIQUE` de `cuenta.nombre`).

  