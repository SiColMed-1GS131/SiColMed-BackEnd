"""Dependencias provisionales hasta la entrega del módulo de Login."""

from collections.abc import Callable
from typing import Any

from fastapi import Depends, HTTPException, status


def get_usuario_actual() -> Any:
    """Punto de reemplazo para la autenticación real."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="La autenticación todavía no está disponible.",
    )


def requiere_rol(rol: str) -> Callable[..., Any]:
    """Punto de reemplazo para la autorización real."""
    def dependencia(usuario: Any = Depends(get_usuario_actual)) -> Any:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="La autorización todavía no está disponible.",
        )

    return dependencia