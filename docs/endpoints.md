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