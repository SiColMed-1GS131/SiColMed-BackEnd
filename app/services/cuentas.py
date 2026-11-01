"""Reglas de negocio de las cuentas contables (Módulo 5).

La regla de no cambiar el tipo de una cuenta con movimientos la aplica la
función editar_cuenta en BD; su error llega como HTTP 400 por app.errors.
"""

from fastapi import Depends, HTTPException, status

from app.repositories.cuentas import CuentasRepository, get_cuentas_repository
from app.schemas.cuentas import Cuenta, CuentaCrear, CuentaEditar, CuentaEliminada


class CuentasService:
    def __init__(self, repositorio: CuentasRepository):
        self.repositorio = repositorio

    def listar(self, activa: bool | None) -> list[Cuenta]:
        return [Cuenta(**fila) for fila in self.repositorio.listar(activa)]

    def crear(self, datos: CuentaCrear) -> Cuenta:
        id_cuenta = self.repositorio.crear(datos.nombre, datos.tipo.value)
        # Una cuenta nueva nace activa: aún no tiene movimientos.
        return Cuenta(id_cuenta=id_cuenta, nombre=datos.nombre, tipo=datos.tipo, activa=True)

    def editar(self, id_cuenta: int, datos: CuentaEditar) -> Cuenta:
        editada = self.repositorio.editar(
            id_cuenta, datos.nombre, datos.tipo.value, datos.activa
        )
        if not editada:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No existe la cuenta {id_cuenta}",
            )
        return Cuenta(id_cuenta=id_cuenta, **datos.model_dump())

    def eliminar(self, id_cuenta: int) -> CuentaEliminada:
        resultado = self.repositorio.eliminar(id_cuenta)
        return CuentaEliminada(id_cuenta=id_cuenta, resultado=resultado)


def get_cuentas_service(
    repositorio: CuentasRepository = Depends(get_cuentas_repository),
) -> CuentasService:
    return CuentasService(repositorio)
